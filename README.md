# ChatBotAI 🤖

> **Estado:** proyecto en desarrollo activo.

Chatbot de WhatsApp para negocios, construido con FastAPI, Supabase y Google Gemini. Recibe mensajes de WhatsApp Cloud API, los procesa con IA (texto y notas de voz) y responde automáticamente, manteniendo sesión, historial y leads en Supabase.

## Características

- **Webhook de WhatsApp** (Meta Cloud API): recibe mensajes de texto y de voz.
- **Respuestas con Gemini**: salida estructurada en JSON para un control preciso del diálogo.
- **Mensajes de voz**: transcribe el audio y responde con normalidad.
- **Gestión de sesiones**: la sesión expira tras 15 minutos de inactividad o al cambiar de día.
- **Contexto temporal**: la IA conoce la fecha y hora reales (zona `America/Mexico_City`) y no permite agendar citas en el pasado.
- **Gestión de leads**: resumen automático de cada conversación por teléfono.
- **Multi-negocio**: cada bot tiene su propio `system_prompt`, token y tipo de servicio, aislados por `bot_id`.

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.11 |
| Framework | FastAPI + Uvicorn |
| Base de datos | Supabase (PostgreSQL) |
| IA | Google Gemini (`gemini-2.5-flash-lite`, `gemini-2.5-flash`) |
| WhatsApp | WhatsApp Cloud API (Meta) |
| Infraestructura | Docker + Docker Compose |

## Estructura del proyecto

```
ChatBotAI/
├── app/
│   ├── main.py                # App FastAPI y arranque
│   ├── api/
│   │   ├── auth/security_api.py   # Verificación de API key
│   │   └── routes/               # webhook, sessions, bots_info
│   ├── services/
│   │   ├── whatsapp.py        # Cliente WhatsApp Cloud API
│   │   ├── ia_service.py      # Invocación de Gemini
│   │   └── __init__.py
│   ├── database/supabase.py   # Consultas a Supabase
│   ├── workers/proccessor.py  # Orquestador asíncrono
│   ├── schemas/               # Plantillas y esquemas de respuesta
│   └── core/utils.py          # Utilidades (contexto temporal)
├── specs/                     # Especificaciones del proyecto (spec-driven)
├── docs/constitution.md       # Principios del proyecto
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Requisitos

- Python 3.11+ (o Docker)
- Proyecto en Supabase con las tablas `bots`, `conversations`, `messages` y `leads`
- API key de Google Gemini
- Cuenta Meta for Developers con WhatsApp Cloud API configurada

## Instalación y ejecución

### Con Docker (recomendado)

```bash
docker compose up        # arranca en :8000 con recarga automática
docker compose down      # apagar
```

### En local

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Túnel público (para el webhook de Meta)

```bash
cloudflared tunnel --url http://localhost:8000
```

> La URL del túnel es **efímera**: al reiniciar cambia y debe actualizarse en el panel de Meta.

### Configurar el webhook en Meta

- **Callback URL**: `<url_del_tunel>/webhook`
- **Verify token**: el valor de `TOKEN_WEBHOOK` en tu `.env`

## Variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_KEY=<publishable key>
GEMINI_API_KEY=<gemini api key>
API_KEY_SECRETO=<clave para cabecera X-API-KEY>
TOKEN_WEBHOOK=<verify token de Meta>
DEV_API_URL_BASE=http://api:8000    # http://127.0.0.1:8000 en local
PORT=8000
```

| Variable | Descripción |
|---|---|
| `SUPABASE_URL` | URL del proyecto Supabase (debe terminar en `.supabase.co`, **no** `.supabase.com`) |
| `SUPABASE_KEY` | Clave publishable/anon de Supabase |
| `GEMINI_API_KEY` | API key de Google Gemini |
| `API_KEY_SECRETO` | Clave para los endpoints protegidos con `X-API-KEY` |
| `TOKEN_WEBHOOK` | Verify token del webhook de Meta |
| `DEV_API_URL_BASE` | URL base para llamadas internas (`http://api:8000` en Docker, `http://127.0.0.1:8000` en local) |
| `PORT` | Puerto de arranque (por defecto 8000) |

## API

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/webhook` | verify token | Verificación del webhook de Meta |
| POST | `/webhook` | — | Recepción de mensajes (texto y audio) |
| GET | `/api/v1/sessions/{phone}` | `X-API-KEY` | Sesión activa del usuario |
| POST | `/api/v1/sessions/update` | `X-API-KEY` | Actualizar plantilla/metadata de sesión |
| GET | `/api/v1/sessions/history` | `X-API-KEY` | Últimos 20 mensajes |
| GET | `/api/v1/bots_info/id/{phone_id}` | — | Token del bot |
| GET | `/api/v1/bots_info/bot_data/{bot_id}` | — | Prompt y tipo de servicio del bot |

Documentación interactiva en `/docs` (Swagger UI).

## Troubleshooting

- **`SUPABASE_URL` inválida**: asegúrate de que termine en `.supabase.co`, no `.supabase.com`.
- **Upserts fallan con `42501`**: revisa las políticas RLS de la tabla; el backend necesita permisos de escritura.
- **Hostname `api` no resuelve**: solo funciona dentro de la red de Docker Compose; en local usa `http://127.0.0.1:8000`.

## Autor

Desarrollado por [Fer10K](https://github.com/Fer10K). Interfaz y mensajes en español.
