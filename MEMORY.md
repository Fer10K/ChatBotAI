## Memoria - ChatBotAI

### Estado actual
- Documentación al día: `AGENTS.md` cubre arranque, túnel, webhook de Meta y variables de `.env`;
  `docs/constitution.md` con los6 principios innegociables.
- Corrección de errores completada: `pyflakes`/`flake8` en 0 avisos, `import app.main` OK.
- Arreglado `SUPABASE_URL`: el dominio era `.supabase.com` (NXDOMAIN); el correcto es `.supabase.co`.
- Servicios apagados (Docker + túnel) tras la sesión de pruebas.
- **Spec 001 completa en fase de diseño**: `specs/001-configuracion-negocio-comida/`
  - `spec.md` → 31 RF con CA en EARS, 28 casos límite, 0 dudas abiertas (el QUÉ).
  - `plan.md` → 488 líneas: modelo de datos, DDL, API, cambios de código, verificación (el CÓMO).
  - Falta `tasks.md` (desglose ejecutable).

### Decisiones
- `AGENTS.md`, `MEMORY.md` y `docs/` **no se versionan** a propósito (`.gitignore`).
- `get_history` devuelve dicts `{"sender", "text"}` (no objetos de langchain) para ser
  compatible con `ia_service` y serializable a JSON.
- Servicio `worker` eliminado de `docker-compose.yml`: no tenía `__main__` y la lógica
  corre como `BackgroundTask` en la API.
- Las especificaciones (`specs/NNN-*/`) se crearán durante el desarrollo.
- Política de estilo: nada se da por bueno sin prueba ejecutable (ver `docs/constitution.md`).

### Spec 001 — nicho comida (requerimientos, QUÉ/POR QUÉ)
- Alcance: **solo configuración del negocio**; la conversación queda para otra spec.
- Cuatro perfiles: administrador del sistema, dueño del negocio, **administrador de local**,
  operador multi-negocio. Solo el admin del sistema crea plantillas.
- Menú: **menú base del negocio + menú propio de cada local** (`business_data` por `bot_id`).
  El dueño añade/elimina artículos eligiendo en qué locales se aplica; el local añade
  platos exclusivos y **descarta** (reversible) los que no ofrece.
- Propagación de cambios: **salvo a los locales con versión propia o descartado**.
- Categorías y entregas/mínimo: base del negocio, ajustables por local.
- Relación plato↔extra: **un solo nivel**; los ingredientes quitables son artículos
  reutilizables declarados en lista explícita por plato. Nombres únicos por negocio.
- Plantillas pasan a la BD por nicho: **plantilla de datos** (pedido completo) y
  **plantilla de respuesta** (mensaje + plantilla + acción + objeto de menú interactivo),
  creadas **por prioridad de llenado**, con dos modalidades de entrada (menú interactivo
  de WhatsApp y texto libre validado por el back) y confirmación siempre antes de cerrar.
- Menú al cliente: **categorías y luego en bloques** (nunca exceder el límite de opciones).
- Horarios: solo se registran; su efecto va en la spec de conversación.
- PDF del menú: **fuera de alcance** (se deja la posibilidad de ofrecerlo).

### Plan 001 — decisiones de arquitectura
- **Menú en `jsonb`** (elección del usuario): `businesses.menu` = menú base,
  `business_data.menu` (clave `bot_id`) = copia del local. Reglas de propagación,
  borrado y relaciones se resuelven en `app/database/menu_ops.py` (funciones puras).
- Tablas nuevas: **`niches`** (plantillas por nicho), **`businesses`** (contenedor +
  config base + menú base), **`business_data`** (menú por local). Se **elimina `items`**
  (ya está en 0 filas) y `bots.service_type`.
- **`bots` pasa a ser el LOCAL** (no se renombra: cuelgan de él `conversations`,
  `messages` y `leads`). Gana `business_id`, `delivery_methods`, `min_order`.
- Campos por local: `customized` (no recibe propagación) y `available` (descartado).
  Un plato exclusivo de local se detecta porque **no** existe en el menú base.
- **RLS hoy es `USING (true)`** con clave `publishable` → RNF-1 se cumple en la capa
  de aplicación (todas las consultas acotadas por `business_id`/`bot_id`); el aislamiento
  fuerte queda para la spec de permisos.
- Completitud (RF-31) **se calcula al leer**, no se guarda (evita desincronización).
- DDL: **no hay CLI de Supabase ni cadena de conexión en `.env`**, y el MCP
  `execute_sql` es solo lectura → la migración va en `migrations/001_*.sql`
  para pegarla en el SQL editor.
- `plan.md` tiene **10 decisiones marcadas como "a revisar"** (§10) pendientes de
  aprobación antes de ejecutar.

### Verificado en Supabase (ChatBotProyect, `xdnwuelrtjilvzhhkezm`)
- Tablas hoy: `bots` (1), `items` (**0**), `business_hours` (0), `conversations` (1),
  `messages` (12), `leads` (2).
- `items.price` es `text` (hay que pasarla a `numeric`); `business_hours.open_time/close_time`
  son NOT NULL (habrá que soltarlo para `is_closed = true`).
- RLS: `conversations` con SELECT/INSERT/UPDATE y `leads` con UPDATE → el flujo completo funciona.
- **RLS es permissiva**: `bots`, `conversations`, `messages`, `leads` usan `USING (true)`.
  La única política con condición real es `bots` INSERT (`auth.uid() = user_id`), que el
  backend con clave `anon` **no puede** cumplir → el backend solo **lee** `bots`.
- La política `bots` SELECT **se llama** «Los usuarios solo ven sus propios bots» pero su
  `USING` es `true`: no filtra nada.
- **`pg_depend` sobre `bots.user_id`**: dependen `bots_user_id_fkey` (`deptype='a'`, cae
  sola) y la política `Enable insert for authenticated users only` (`deptype='n'`).
  → `drop column user_id` **aborta** si no se baja antes la política.
- **PostgreSQL 17.6**. `user_id` no aparece en ningún `.py` del proyecto.
- Datos de prueba limpiados (`messages` y `leads`).

### Errores a evitar
- No usar la key `anon`/publishable como si fuera de backend sin revisar RLS:
  `conversations` tenía RLS activo con 0 políticas → el upsert fallaba con `42501`.
- No asumir que RLS aísla datos: aquí es `USING (true)`. Sin identidad de usuario en el
  backend, el aislamiento entre negocios **solo** puede ser en la capa de aplicación.
- No intentar ejecutar DDL por el MCP de Supabase: `execute_sql` es **solo lectura**
  (`25006 cannot execute ... in a read-only transaction`).
- **Antes de un `DROP COLUMN`, mirar `pg_depend`**: una RLS policy con `deptype='n'`
  bloquea el borrado aunque las filas no tengan nada que ver. Las FK (`deptype='a'`)
  caen solas.
- `pg_policies` **no** tiene columna `rowname`: usar
  `tablename, policyname, cmd, qual, with_check`.
  Tampoco `pg_depend` tiene `description`: usar `classid, objid, deptype`.
- Ojo con los f-strings anidados con comillas dobles: el Dockerfile usa Python 3.11.
- No confiar en un diagnóstico de "errores de sintaxis" sin ejecutar el linter.

### Pendiente
- **Aprobar las 10 decisiones del `plan.md` §10** (carpeta `migrations/`, archivos nuevos,
  borrado de `items`/`service_type`/`bots.user_id`, etc.) antes de ejecutar.
- **Borrado manual de los datos existentes** (negocio, artículos, conversaciones): decidido,
  irreversible, y se hace **antes** de aplicar la spec 001. Pendiente de ejecutar.
- Escribir `tasks.md` de la spec 001 (desglose ejecutable de los pasos 4–10 del plan).
- Recrear `/tmp/opencode/lintenv`: **ya no existe** y `pyflakes`/`flake8` no están
  instalados, pero `AGENTS.md` los exige para verificar.
