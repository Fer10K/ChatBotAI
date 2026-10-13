## AGENTS - ChatBotAI

Chatbot de WhatsApp para negocios: FastAPI + Supabase + Google Gemini.
- Python 3.11 y FastAPI; `app/` con `api/`, `services/`, `database/`, `workers/`, `schemas/`.
- Sin frameworks de frontend ni build: la interfaz es el chat de WhatsApp.
- Arranque: `docker compose up` (servicio `api`), escucha en `:8000`. Apagado: `docker compose down`.
- Túnel público (opcional): `cloudflared tunnel --url http://localhost:8000`. La URL que
  devuelve es efímera: al reiniciar el túnel cambia y hay que volver a copiarla.

## Webhook de Meta
- Callback URL: `<url del túnel>/webhook`
- Verify token: el valor de `TOKEN_WEBHOOK` en `.env` (aquí nunca se escribe).
- Meta envía `metadata.phone_number_id` en cada mensaje; debe coincidir con el
  `phone_id` de la fila correspondiente de la tabla `bots`.

## Configuración (.env)
- `SUPABASE_URL` → termina en **`.supabase.co`**, no `.supabase.com`: `.com` da `NXDOMAIN`
  y la app no conecta. Es el fallo que más veces ha costado de localizar.
- `DEV_API_URL_BASE` → `http://api:8000` dentro de Docker; `http://127.0.0.1:8000` en local.
  El hostname `api` es el servicio del `docker-compose.yml` y solo resuelve dentro de la red.
- `API_KEY_SECRETO` → cabecera `X-API-KEY` de los endpoints protegidos.
- `TOKEN_WEBHOOK` → verify token del webhook de Meta.
- `GEMINI_API_KEY`, `SUPABASE_KEY`, `PORT` → el resto de variables de arranque.
- `.env` está ignorado por git: sus valores no se escriben en el repo ni en `MEMORY.md`.

## Convenciones
- Textos, mensajes y comentarios en español.
- Nombres descriptivos; comentarios solo donde aporten.
- Estilo existente respetado: no se re-formatea código que ya funciona.

## Datos
- Supabase: `bots`, `conversations`, `messages`, `leads` (todas con RLS activo).
- Si cambias la forma de los datos, mantén compatibilidad con lo ya guardado o el usuario
  perderá sus sesiones.
- Nunca escribas claves ni tokens en el repo: van en `.env` (ignorado por git).

## Forma de trabajar
- Haz solo lo que se pide: no añadas funcionalidades por tu cuenta.
- Cambios pequeños y enfocados; no reescribas lo que ya funciona.
- Al terminar, resume qué has cambiado y cualquier decisión que deba revisar.

## Reglas
- Lee `docs/constitution.md` y la spec activa (`specs/NNN-*/`) antes de tocar código.
- No dar por concluida una spec si hay dudas aviertas marcadas con NECESITA ACLARACIÓN

## Límites
- ✅ Siempre: mantener los textos en español y la compatibilidad de los datos guardados.
- ✅ Siempre: actualizar `MEMORY.md` al terminar cada tarea.
- ⚠ Pregunta antes: crear archivos nuevos, cambiar el formato de los datos guardados.
- 🚫 Nunca añadir sin consultar antes: dependencias, frameworks o un paso de build.

## Verificación
- Sin carpeta `test/` en el proyecto. La verificación mínima antes de dar un cambio por bueno:
  - `find app -name '*.py' -exec python3 -m py_compile {} +`
  - `pyflakes app/` → sin salida
  - `flake8 --select=E9,F63,F7,F82,F401,F811,F821,F841,F541 app/` → sin salida
  - `set -a; . ./.env; set +a; python -c "import app.main"`
- El flujo real se prueba con el servicio levantado (`docker compose up`) y un POST al webhook.
- Comprobación rápida del webhook sin mandar nada a Meta:
  `GET /webhook?hub.mode=subscribe&hub.verify_token=<TOKEN_WEBHOOK>&hub.challenge=x`
  debe devolver `x` con `200`, y `400` si el token no coincide.
