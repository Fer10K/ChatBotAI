# Plan — Spec 001: Configuración de negocio de comida

> Documento **de arquitectura y diseño**: stack, modelo de datos, archivos y secuencia.
> El *qué* y el *porqué* están en [`spec.md`](./spec.md). Las tareas concretas van en `tasks.md`.

---

## 1. Alcance de este plan

**Incluye**

- Modelo de datos nuevo (tablas, columnas, restricciones, RLS).
- Capa de API para configurar un negocio por completo: negocio, locales, horarios, menú base, menú por local, relaciones y plantillas.
- Reglas de negocio del menú (propagación, versiones por local, descartes, reutilización de ingredientes).
- El constructor del objeto de menú interactivo (RF-28, RF-30).
- Sustituir el `if service_type == "SERVICE"` del código por plantillas que llegan desde la base de datos.
- Semilla del nicho `comida` (plantilla de datos y plantilla de respuesta).

**No incluye** (va en la spec 002 o posterior, igual que en la spec)

- La conversación: avanzar por la plantilla, validar el texto libre, enviar el menú interactivo, evitar desvíos, avisos de horario.
- El panel/dashboard (interfaces y pantallas).
- Permisos y roles (spec aparte).
- El pedido: cobro, historial de órdenes, entrega al negocio.
- El menú en PDF.
- El borrado de los datos existentes (precondición manual, fuera de la spec).

---

## 2. Decisiones de arquitectura

| # | Decisión | Por qué |
|---|---|---|
| D1 | **Menú en `jsonb`**, no tablas normalizadas | Elección explícita del usuario (modelo A). El menú se entrega entero al asistente en una sola lectura (RNF-2) y el menú de un restaurante es pequeño. Coste: las reglas de propagación y borrado se resuelven en la capa de aplicación, no con `JOIN`. |
| D2 | **`business_data` con clave `bot_id`** | Elección explícita: un bot = un local. Cada local tiene su propia copia del menú. |
| D3 | **Tabla nueva `businesses`** como contenedor del negocio | Hacen falta: menú base (RF-11/12/21), entregas y mínimo base (RF-4/5), categorías compartidas (RF-9) y el nicho (RF-1). Sin ella no hay dónde poner el menú base. |
| D4 | **Tabla nueva `niches`** para las plantillas | RF-29 CA2 exige que el administrador del sistema defina plantillas «para un nicho», no para un negocio. `businesses.niche_id` apunta al nicho (RF-23 CA1). |
| D5 | **La tabla `bots` pasa a representar un *local*** | Ya tiene `phone_id`, `access_token`, `sucursal_name`, `address`, y `conversations`/`messages`/`leads` cuelgan de `bot_id`. Renombrarla tocaría 5 tablas y 4 archivos sin ganancia funcional: se mantiene el nombre y se documenta. |
| D6 | **Categorías solo en el menú base** | RF-9 dice que las categorías son del negocio y los locales solo las usan. No se copian a `business_data`: una sola fuente, propagación gratis. |
| D7 | **El aislamiento entre negocios (RNF-1) se hace en la capa de aplicación** | Ver §7.1. Las políticas RLS actuales son `USING (true)` y no hay identidad por usuario en el backend. |
| D8 | **La completitud (RF-31) se calcula al leer, no se guarda** | Un campo guardado se desincroniza; RNF-4 exige que los cambios se noten en la siguiente atención. |

---

## 3. Modelo de datos

### 3.1 Antes → después

| Tabla | Estado | Acción |
|---|---|---|
| `niches` | no existe | **crear** |
| `businesses` | no existe | **crear** |
| `business_data` | no existe | **crear** |
| `bots` | existe (1 fila) | **modificar** |
| `business_hours` | existe (0 filas) | **modificar** (2 columnas) |
| `items` | existe (**0 filas**) | **eliminar** |
| `conversations` | existe | sin cambios |
| `messages` | existe | sin cambios |
| `leads` | existe | sin cambios |

> `items` está vacía: la migración de datos de artículos **no existe**, no hay nada que mover.

### 3.2 DDL

```sql
-- ── 1. Nichos: fuente única de las plantillas (RF-1, RF-22, RF-23, RF-29)
create table niches (
  id              uuid primary key default extensions.uuid_generate_v4(),
  name            text not null unique,
  schema_request  jsonb not null,          -- plantilla de datos (RF-22)
  schema_response jsonb not null,          -- plantilla de respuesta (RF-23)
  created_at      timestamptz default now()
);

-- ── 2. Negocio: contenedor, config base y menú base
create table businesses (
  id               uuid primary key default extensions.uuid_generate_v4(),
  user_id          uuid not null references auth.users(id),
  name             text not null unique,                    -- RF-1 CA2
  niche_id         uuid not null references niches(id),     -- RF-1
  menu             jsonb not null default '{"categories":[],"items":[]}'::jsonb,  -- menú base
  delivery_methods jsonb not null default '[]'::jsonb,      -- RF-4 (base)
  min_order        numeric,                                 -- RF-5 (base)
  created_at       timestamptz default now()
);
create index idx_businesses_user on businesses(user_id);

-- ── 3. bots pasa a ser el LOCAL
alter table bots add column business_id uuid references businesses(id);
create index idx_bots_business on bots(business_id);
alter table bots add column delivery_methods jsonb;   -- NULL = usar la base (RF-4 CA3)
alter table bots add column min_order numeric;        -- NULL = usar la base (RF-5 CA3)
alter table bots drop column service_type;            -- lo sustituye businesses.niche_id

-- ── 3b. bots.user_id: pendiente de aprobación (§10). OJO: no se puede
--        soltar la columna directamente. Comprobado en pg_depend que la
--        política "Enable insert for authenticated users only" depende de
--        ella con deptype='n' → Postgres 17 aborta con
--        "cannot drop column user_id ... because other objects depend on it".
--        Hay que bajar la política ANTES que la columna, y rehacerla contra
--        el negocio. La FK bots_user_id_fkey cae sola (deptype='a').
--        user_id no aparece en ningún .py del proyecto.
-- drop policy if exists "Enable insert for authenticated users only" on bots;
-- alter table bots drop column user_id;
-- create policy bots_insert on bots for insert to authenticated
--   with check (exists (
--     select 1 from businesses b
--     where b.id = bots.business_id and b.user_id = auth.uid()));

-- ── 3c. La política SELECT de bots miente: "Los usuarios solo ven sus
--        propios bots" tiene USING (true) y no filtra nada. Con business_id
--        en la mano se puede hacer real.
-- drop policy if exists "Los usuarios solo ven sus propios bots" on bots;
-- create policy bots_select on bots for select using (exists (
--   select 1 from businesses b
--   where b.id = bots.business_id and b.user_id = auth.uid()
-- ));

-- ── 4. business_data: el menú de UN local (RF-17..RF-21)
create table business_data (
  id         uuid primary key default extensions.uuid_generate_v4(),
  bot_id     uuid not null unique references bots(id) on delete cascade,
  menu       jsonb not null default '{"items":[]}'::jsonb,
  updated_at timestamptz default now()
);
create index idx_business_data_bot on business_data(bot_id);

-- ── 5. Horarios: un día cerrado no tiene horas (RF-3)
alter table business_hours alter column open_time  drop not null;
alter table business_hours alter column close_time drop not null;
-- ya existente y correcto: unique(bot_id, day_of_week) + fk → bots on delete cascade

-- ── 6. La tabla items deja de existir
drop table items;
```

`conversations`, `messages` y `leads` **no se tocan**. `conversations.metadata` sigue siendo la plantilla activa (RF-22 CA2), y su clave `bot_id` mantiene separadas las conversaciones de cada local (RF-2 CA2).

### 3.3 Forma del menú en `jsonb`

**`businesses.menu`** (menú base) — dos claves:

```jsonc
{
  "categories": [
    { "id": "uuid", "name": "Entradas", "position": 1 }
  ],
  "items": [
    {
      "id": "uuid",                       // estable; es con lo que se referencian los extras
      "name": "Hamburguesa clásica",      // ÚNICO por negocio (RF-8)
      "description": "…",
      "price": 120,                       // number >= 0; 0 = gratis (RF-7)
      "image_url": null,
      "category": "uuid-de-categoría",    // RF-9
      "role": "plato",                    // "plato" | "extra" (RF-14)
      "accepts_extras": true,             // solo con role=plato
      "allow_remove": true,               // solo con role=plato
      "extras": ["uuid", "uuid"],         // un solo nivel (RF-14)
      "removable": ["uuid", "uuid"],      // ingredientes quitables (RF-13)
      "is_active": true                   // ocultar sin borrar (RF-10)
    }
  ]
}
```

**`business_data.menu`** (menú de un local) — solo `items`, con dos campos extra:

```jsonc
{
  "items": [ { …mismo shape…, "customized": false, "available": true } ]
}
```

| Campo | Dónde vive | Significado |
|---|---|---|
| `customized` | solo en `business_data` | Este local ya editó el artículo → **no recibe propagación** (RF-21 CA2) |
| `available` | solo en `business_data` | `false` = «no disponible en este local» (RF-19). Nunca lo toca la propagación (RF-21 CA3) |
| `role` | ambos | «es un extra» / «lleva extras». Sustituye al `type` original |
| `category` | ambos | El «tipo» para filtrar y presentar. Id de `categories[].id` |

Un plato **exclusivo de local** simplemente **no existe** en `businesses.menu`; se deriva, no se guarda un campo `origin` (menos superficie para que se desincronice).

### 3.4 Reglas de negocio

| RF | Regla concreta |
|---|---|
| RF-7 | `price` debe ser `number` y `>= 0`. Si no → 422 con el campo indicado. |
| RF-8 | Al crear/editar: buscar `name` en `businesses.menu.items` (ignorando el propio `id`). Si coincide → 409. En `business_data`, si el nombre ya está en la base, se crea **versión** (`customized=true`), no artículo nuevo (RF-18 CA2, RF-8 CA3). |
| RF-9 | Categorías en `businesses.menu.categories`, `UNIQUE` por nombre dentro del negocio. Eliminar solo si `items` no la referencia. Se copian a `business_data` en cada guardado del menú base. |
| RF-11 | `aplicar-a-locales(item_id, bot_ids)` → añade el artículo a `business_data.menu` de cada local indicado. `bot_ids = []` → el artículo queda solo en la base (CA2). |
| RF-12 | `retirar(item_id, bot_ids_que_conservan)` → borra el artículo de `business_data.menu` de todos los locales **menos** los indicados. El artículo **no** se toca en `businesses.menu` (CA4). |
| RF-13/14 | `declarar_relacion(parent, related, tipo)`. Antes de insertar: si `related` ya aparece como `parent` de otra relación → 409 (un solo nivel, CA2 de RF-14). |
| RF-15 | `buscar_o_crear_ingrediente(nombre)` → busca por `name` dentro del negocio; si no existe, lo crea con `role="extra"` y lo vincula. |
| RF-16 | `borrar_item(id)` → recorre base + todos los `business_data`, cuenta en cuántos `extras`/`removable` aparece, limpia esas entradas, borra el artículo y devuelve `{referencias_limpiadas: n}`. |
| RF-17 | `menu_efectivo(bot_id)` = `business_data.menu` filtrando `available != false` y `is_active != false`, con `category` resuelta desde la base. |
| RF-19 | `descartar` → `available=false`. `reactivar` → `available=true`. El artículo nunca se borra de `business_data` → datos y relaciones intactos (CA2). |
| RF-20 | `PATCH` sobre el menú del local → escribe los campos cambiados y pone `customized=true`. |
| RF-21 | **Propagación**: al guardar `businesses.menu`, para cada local con copia del artículo: si `customized=false` → copia los campos del base; si `customized=true` → no toca nada; `available` **nunca** se toca. |
| RF-31 | `evaluar_completitud()` devuelve `{is_complete, missing[]}` comprobando: ≥1 artículo activo, ≥1 forma de entrega, ≥1 local, y cada local con 7 horarios declarados. |

---

## 4. Plantillas del nicho (semilla)

Contenido que se inserta en `niches` durante la migración.

### 4.1 `schema_request` — plantilla de datos (RF-22, RF-24)

```jsonc
{
  "fields": [
    {"key": "purchase_type", "priority": 1, "label": "Forma de compra",
     "required": true,  "options": ["domicilio", "local", "pickup"]},
    {"key": "branch",       "priority": 2, "label": "Local",       "required": true},
    {"key": "items",        "priority": 3, "label": "Artículos",   "required": true},
    {"key": "address",      "priority": 4, "label": "Dirección",
     "required": true,  "condition": "purchase_type == 'domicilio'"},   // RF-22 CA3/CA4
    {"key": "contact",      "priority": 5, "label": "Datos de contacto", "required": true},
    {"key": "total",        "priority": 6, "label": "Total",       "required": true},
    {"key": "confirmed",    "priority": 7, "label": "Confirmación",
     "required": true,  "condition": "todos_los_requeridos_llenos"}      // RF-25
  ],
  "data": {
    "purchase_type": null,
    "branch": null,
    "items": [],                       // [{item_id, name, price, quantity, extras[], removed[]}]
    "address": null,
    "contact": {"name": null, "phone": null},
    "total": 0,
    "confirmed": false,
    "status": "iniciado"               // iniciado | en_curso | confirmado | cancelado
  }
}
```

`priority` cubre RF-24; `condition` cubre RF-22 CA3/CA4. La sesión guarda **este objeto entero** en `conversations.metadata`, de modo que un cambio de nicho posterior no corrompe una atención en curso (RF-22 CA2).

### 4.2 `schema_response` — plantilla de respuesta (RF-23, RF-27, RF-28)

Estructura pasada a Gemini como `response_schema`. Los cuatro elementos de RF-23 son `required` (CA2):

```jsonc
{
  "type": "OBJECT",
  "properties": {
    "text_response":     {"type": "STRING", "description": "Mensaje para el cliente"},
    "updated_template":  { "…mismo shape que schema_request…" },
    "action_required":   {
      "type": "STRING",
      "enum": ["none", "show_menu", "show_section", "show_item_options",
               "show_delivery_methods", "show_hours", "ask_address", "ask_branch",
               "confirm_order", "cancel_order", "view_order"]          // RF-27
    },
    "interactive_object": {                                              // RF-28
      "type": "OBJECT",
      "description": "Null cuando action_required = none",
      "properties": {
        "kind":     {"type": "STRING",
                     "enum": ["sections", "items", "item_options", "delivery", "hours", "none"]},
        "sections": {"type": "ARRAY", "items": {"type": "OBJECT"}},     // categorías
        "items":    {"type": "ARRAY", "items": {"type": "OBJECT"}},     // artículos del bloque
        "options":  {"type": "ARRAY", "items": {"type": "OBJECT"}},     // extras / quitos / entregas
        "next":     {"type": "STRING", "description": "Cursor de paginación o null"}
      },
      "required": ["kind"]
    }
  },
  "required": ["text_response", "updated_template", "action_required", "interactive_object"]
}
```

---

## 5. API

Prefijo `/api/v1`, igual que las rutas existentes. Todas protegidas con `X-API-KEY` (`verificar_api_key`, patrón ya usado en `sessions.py`).

### 5.1 Negocio

| Método y ruta | RF |
|---|---|
| `POST  /businesses` | RF-1 |
| `GET   /businesses/{bid}` — devuelve config + completitud | RF-31 |
| `PATCH /businesses/{bid}` — `delivery_methods`, `min_order` | RF-4, RF-5 |
| `GET   /businesses/{bid}/completitud` | RF-31 |

### 5.2 Menú base

| Método y ruta | RF |
|---|---|
| `GET    /businesses/{bid}/menu` | RF-6 |
| `POST   /businesses/{bid}/menu/items` | RF-6, RF-7, RF-8 |
| `PATCH  /businesses/{bid}/menu/items/{iid}` — edita base **y propaga** | RF-21 |
| `DELETE /businesses/{bid}/menu/items/{iid}` — limpia relaciones y devuelve el conteo | RF-16 |
| `POST   /businesses/{bid}/menu/items/{iid}/aplicar-a-locales` | RF-11 |
| `POST   /businesses/{bid}/menu/items/{iid}/retirar` | RF-12 |
| `POST   /businesses/{bid}/menu/items/{iid}/relaciones` | RF-13, RF-14, RF-15 |
| `PATCH  /businesses/{bid}/menu/categories` | RF-9 |
| `PATCH  /businesses/{bid}/menu/items/{iid}/estado` | RF-10 |

### 5.3 Locales

| Método y ruta | RF |
|---|---|
| `GET  /businesses/{bid}/locales` | RF-2 |
| `POST /businesses/{bid}/locales` — crea `bots` **y** su `business_data` | RF-2, RF-17 |
| `GET  /locales/{bot_id}` | — |
| `PATCH /locales/{bot_id}` — `address`, `delivery_methods`, `min_order` | RF-2, RF-4, RF-5 |
| `GET  /locales/{bot_id}/hours` · `PUT /locales/{bot_id}/hours` | RF-3 |

### 5.4 Menú del local

| Método y ruta | RF |
|---|---|
| `GET    /locales/{bot_id}/menu` — menú efectivo | RF-17 |
| `POST   /locales/{bot_id}/menu/items` — exclusivo o versión | RF-18 |
| `PATCH  /locales/{bot_id}/menu/items/{iid}` — marca `customized` | RF-20 |
| `POST   /locales/{bot_id}/menu/items/{iid}/descartar` | RF-19 |
| `POST   /locales/{bot_id}/menu/items/{iid}/reactivar` | RF-19 |

### 5.5 Plantillas (administrador del sistema)

| Método y ruta | RF |
|---|---|
| `GET /niches` · `GET /niches/{nid}` | RF-1 |
| `PUT /niches/{nid}` | RF-29 CA2 |

### 5.6 Lectura del flujo de atención (modificada)

| Método y ruta | Cambio |
|---|---|
| `GET /bots_info/bot_data/{bot_id}` | Devuelve `system_prompt`, `schema_request` y `schema_response` en lugar de `service_type` |

---

## 6. Cambios en el código existente

| Archivo | Qué cambia |
|---|---|
| `app/schemas/schemas.py` | Se vacía de las plantillas hardcodeadas (`APPOINTMENT_TEMPLATE`, `UPDATE_SESSION_SCHEMA`) y pasa a contener los **modelos pydantic de entrada** de la API. |
| `app/schemas/response_schema.py` | **Se elimina** (`SERVICE_SCHEMA` y `PRODUCT_SCHEMA` pasan a `niches.schema_response`). |
| `app/database/supabase.py` | `get_bot_data` deja de pedir `service_type` y trae las plantillas del nicho. Se añaden: `create_business`, `get_business`, `update_business_config`, `get_menu_base`, `save_menu_base`, `get_menu_local`, `save_menu_local`, `create_local`, `list_locals`, `get_local`, `update_local_config`, `get_hours`, `save_hours`, `get_niche`, `update_niche`, `get_completitud`. |
| `app/services/ia_service.py` | Firma: `get_response_for_text(loaded_metadata, system_prompt, user_message, template, response_schema, history)`. Se elimina el `if service_type == "SERVICE"` y la instrucción hardcodeada de citas; la instrucción se arma a partir de `template.fields`. |
| `app/workers/proccessor.py` | Deja de leer `service_type`; pasa `schema_request`/`schema_response` desde `bot_data`. |
| `app/api/routes/bots_info.py` | Devuelve las plantillas en vez de `service_type`. |
| `app/api/routes/sessions.py` | Sin cambios estructurales. |
| `app/api/routes/webhook.py` | Sin cambios. |
| `app/services/whatsapp.py` | Sin cambios (el envío del menú interactivo llega en la spec 002). |

### Archivos nuevos

| Archivo | Responsabilidad |
|---|---|
| `app/database/menu_ops.py` | Reglas de negocio del menú como **funciones puras** sobre el `jsonb` (§3.4). Sin acceso a BD → se prueban sin base de datos. |
| `app/services/menu_builder.py` | Construye el objeto de menú interactivo (RF-28, RF-30) con `MAX_SECCIONES = 10` y `MAX_OPCIONES = 10` (límites de WhatsApp), paginando con `next`. |
| `app/api/routes/businesses.py` | §5.1 y §5.2 |
| `app/api/routes/locales.py` | §5.3 y §5.4 |
| `app/api/routes/niches.py` | §5.5 |
| `migrations/001_configuracion_negocio_comida.sql` | DDL (§3.2) + semilla del nicho comida (§4). **Carpeta nueva — requiere aprobación.** |

---

## 7. Requisitos no funcionales

### 7.1 RNF-1 — aislamiento entre negocios

**Situación verificada**: las políticas RLS actuales son `USING (true)` en `bots`, `conversations`, `messages` y `leads`, y el backend usa una clave **publishable** (`anon`), sin identidad por usuario. Con eso, RLS **no puede** distinguir negocios.

**Qué se hace en esta spec**

1. Todas las consultas de la capa de datos van **acotadas explícitamente** por `business_id` o `bot_id`: ninguna función acepta un `business_id` sin validar que el recurso pertenece a él (`PATCH /locales/{bot_id}` comprueba que `bots.business_id` coincide con el negocio indicado).
2. RLS de las tablas nuevas: `SELECT` con `USING (true)` para que el backend lea, y `WITH CHECK` de integridad referencial para escritura (mismo patrón que ya usa la política `Inserción protegida por bot_id` de `leads`).
3. `businesses` y `niches` conservan el patrón `auth.uid() = user_id` para escritura desde el panel.

**Limitación declarada**: el aislamiento **fuerte** a nivel de base de datos llega con la spec de permisos/autenticación, que está fuera de alcance.

### 7.2 RNF-2 — menú completo en un solo acceso

`GET /locales/{bot_id}/menu` se resuelve con una consulta anidada de PostgREST sobre `business_data` + `businesses` (un único `HTTP` request). Si la anidación resulta ambigua, se hacen dos consultas en la misma función: sigue siendo **un acceso** desde el punto de vista de la regla.

### 7.3 RNF-5 — nunca exceder el límite de opciones

`menu_builder.py` parte siempre en bloques de `MAX_OPCIONES = 10` y añade «ver más» con el cursor `next`. Si hay más de `MAX_SECCIONES = 10` categorías, se agrupan con el mismo mecanismo.

### 7.4 RNF-6 — acciones propias del rol

Sin sistema de roles todavía, se logra **por separación de rutas**: no existen endpoints de edición de plantillas bajo las rutas de negocio, así que el dueño no puede alcanzarlos (RF-29 CA1). El control fino llega con la spec de permisos.

---

## 8. Secuencia de ejecución

| Paso | Qué | Quién |
|---|---|---|
| 0 | Aprobar las decisiones de §10 | usuario |
| 1 | **Borrado manual** de los datos existentes en el SQL editor (precondición de la spec, §12) | usuario |
| 2 | Pegar `migrations/001_*.sql` en el SQL editor de Supabase → DDL + semilla | usuario / agente |
| 3 | Verificar el esquema con SQL de comprobación (tablas, restricciones, fila del nicho) | agente |
| 4 | `app/database/menu_ops.py` (funciones puras) + `app/services/menu_builder.py` | agente |
| 5 | `app/database/supabase.py` (consultas nuevas) | agente |
| 6 | Rutas: `businesses.py`, `locales.py`, `niches.py` + `main.py` | agente |
| 7 | `ia_service.py`, `proccessor.py`, `bots_info.py` (quitar el hardcode) | agente |
| 8 | Verificación estática (§9.1) | agente |
| 9 | Verificación funcional (§9.2) | agente |
| 10 | E2E del webhook (§9.3) | agente |
| 11 | Actualizar `MEMORY.md` | agente |
| 12 | Escribir `tasks.md` (desglose de pasos 4–10) | agente |

**Por qué este orden**: `menu_ops` va primero porque es puro y desbloquea todo lo demás sin tocar la base; el SQL va antes que el código porque el código nace sabiendo la forma de los datos.

**Sobre el DDL**: no hay CLI de Supabase instalado ni cadena de conexión en `.env`, y el MCP `execute_sql` es **solo lectura** (no puede ejecutar `CREATE`/`ALTER`/`DROP`). Por eso la migración se entrega como un único archivo SQL para pegar en el SQL editor.

---

## 9. Verificación

### 9.1 Estática (obligatoria, según `AGENTS.md`)

```bash
find app -name '*.py' -exec python3 -m py_compile {} +
pyflakes app/                                   # sin salida
flake8 --select=E9,F63,F7,F82,F401,F811,F821,F841,F541 app/   # sin salida
set -a; . ./.env; set +a; python -c "import app.main"
```

> El entorno de linting (`/tmp/opencode/lintenv`) ya no existe y `pyflakes`/`flake8` no están instalados: hay que recrearlo antes del paso 8.

### 9.2 Funcional — cobertura RF/CL

| Verificación | RF/CL que cubre |
|---|---|
| SQL: existen `niches`, `businesses`, `business_data`; `items` y `bots.service_type` ya no; semilla con 1 nicho | §3.1, §4 |
| `POST /businesses` con nombre repetido → 409 | RF-1 CA2, CL-1 |
| Crear negocio sin nada → `is_complete=false` con `missing[]` | RF-31, CL-1 |
| Artículo sin precio / precio negativo → 422 | RF-6, RF-7, CL-2, CL-4 |
| Artículo con precio `0` → 200 | RF-7, CL-3 |
| Artículo con nombre repetido → 409 | RF-8, CL-5 |
| Local guarda versión con nombre de la base → se acepta como versión | RF-8 CA3, CL-6 |
| Declarar extra a un artículo que ya es extra → 409 | RF-14 CA2, CL-8 |
| Declarar ingrediente existente → no duplica, reutiliza | RF-15, CL-9 |
| Borrar artículo referenciado → `referencias_limpiadas > 0` | RF-16, CL-7 |
| Retirar de locales → el artículo sigue en la base | RF-12 CA4, CL-10 |
| Retirar marcando 2 locales → solo esos 2 lo conservan | RF-12, CL-11 |
| Editar base con local `customized=true` → no se pisa | RF-21 CA2, CL-13 |
| Local `available=false` + edición base → sigue descartado | RF-21 CA3, CL-12 |
| Reactivar local → datos y relaciones intactos | RF-19 CA2, CL-15 |
| Dos locales con versiones distintas | RF-20, CL-14 |
| `PUT /locales/{id}/hours` de un local → el otro no cambia | RF-3 CA2 |
| Local sin 7 horarios → `missing[]` lo indica | RF-31, CL-16 |
| Categoría vacía → se elimina | RF-9 CA2, CL-17 |
| `PUT /niches/{id}` funciona; no hay endpoint de plantillas en `/businesses/*` | RF-29, CL-18 |
| Local añade plato sin categoría → 422 | RF-9 CA3, CL-19 |
| `menu_builder`: 25 artículos en una categoría → 3 bloques con `next` | RF-30, RNF-5, CL-24 |
| `menu_builder`: 12 categorías → paginación de secciones | RF-30, RNF-5 |
| Entregas base sin ajuste local → el local recibe la base | RF-4 CA3 |
| Local con `min_order` propio → prevalece | RF-5 CA2 |

Los casos **CL-20 a CL-23, CL-25 a CL-27** dependen de la conversación → se cubren en la spec 002.

### 9.3 E2E del webhook (mismo procedimiento que la sesión anterior)

```bash
# verificación del webhook
GET /webhook?hub.mode=subscribe&hub.verify_token=<TOKEN_WEBHOOK>&hub.challenge=x  → 200 con "x"
GET ...&hub.verify_token=malo                                                                         → 400
# mensaje simulado
POST /webhook con el payload de Meta → {"status":"ok"} y traza en consola hasta "Return to meta"
```

---

## 10. Decisiones que necesitan aprobación antes de ejecutar

| # | Decisión | Recomendación |
|---|---|---|
| 1 | **Crear la carpeta `migrations/`** con el SQL de la migración | ✅ Recomendado: es la única vía (no hay CLI ni cadena de conexión en `.env`) |
| 2 | **Crear los 6 archivos nuevos** de §6 | ✅ Recomendado: sin ellos no hay capa de configuración |
| 3 | **Eliminar** la tabla `items` (0 filas) y la columna `bots.service_type` | ✅ Recomendado: sustituidos por `businesses.menu` y `businesses.niche_id` |
| 4 | **Eliminar** la columna `bots.user_id` (queda redundante con `businesses.user_id`) | ⚠ A revisar. **Comprobado**: no exige borrar el bot de prueba (las filas no bloquean un `DROP COLUMN`), y `user_id` no aparece en ningún `.py`. **Pero sí exige** bajar antes la política `Enable insert for authenticated users only`, que depende de la columna con `deptype='n'` (verificado en `pg_depend`). El orden y la política de recambio están en §3.2/§3b. |
| 5 | **Eliminar** `app/schemas/response_schema.py` | ✅ Recomendado: su contenido pasa a la BD (decisión ya tomada) |
| 6 | `system_prompt` se queda en `bots` (uno por local) o pasa a `businesses` (uno por negocio) | ⚠ A revisar: «la definición del asistente» está fuera de alcance, así que **lo dejo en `bots`** |
| 7 | `bots.name` y `bots.sucursal_name` son redundantes desde que cada bot es un local | ⚠ A revisar: **no toco ninguna** (cambio mínimo) |
| 8 | Overrides de entregas/mínimo: columnas en `bots` o campo dentro de `business_data` | ⚠ A revisar: **propongo columnas en `bots`** (ya guarda dirección y nombre del local, evita una consulta) |
| 9 | `get_response_for_audio` sigue hablando de `fecha_cita` (herencia de citas) | ⚠ A revisar: **propongo dejarlo** y tocarlo en la spec 002 |
| 10 | ¿Misma `X-API-KEY` para `/niches` que para el resto? | ⚠ A revisar: **propongo la misma por ahora**; una clave aparte es configuración nueva y el control real llega con la spec de permisos |

---

## 11. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Escrituras simultáneas sobre el mismo `menu` (leer-modificar-escribir) | Se pisa un cambio | Operaciones cortas + comparación de `updated_at`; se documenta como conocido hasta que haya panel con concurrencia real |
| La propagación (RF-21) vive en Python, no en SQL | Un bug silencia precios en locales | `menu_ops` son funciones puras con pruebas directas antes de tocar la BD |
| El backend no puede escribir `businesses` con clave `anon` (política `auth.uid()`) | El backend no necesita escribirla: solo lee | Verificado: el flujo de atención solo lee configuración |
| RNF-1 solo en la capa de aplicación | Un descuido de scoping filtra datos entre negocios | Todas las funciones de datos exigen `business_id`/`bot_id` como parámetro obligatorio |
| `alter table bots drop column user_id` aborta por la política que depende de ella | La migración se detiene a medias | Orden fijo en §3b: `DROP POLICY` → `DROP COLUMN` → recrear política. Verificado en `pg_depend`. |
| El entorno de linting desapareció | No se puede verificar | Recrear `/tmp/opencode/lintenv` en el paso 8 |

---

## 12. Fuera de alcance (recordatorio)

- **Borrado manual previo** de negocio, artículos, conversaciones y mensajes — **irreversible**, lo hace el usuario antes del paso 2.
- Conversación (spec 002), panel/dashboard, permisos, pedido y cobro, menú en PDF, definición del asistente.

---

## 13. Siguiente

Con el plan aprobado, se escribe `tasks.md` con el desglose de los pasos 4 a 10 en unidades ejecutables y verificables.
