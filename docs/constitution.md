# Constitución — ChatBotAI

Principios innegociables. Cualquier tarea, grande o pequeña, pasa por aquí.

## 1. Comprobar, no suponer
Ningún cambio se da por bueno sin una prueba ejecutable que lo demuestre:
`py_compile`, `pyflakes`, `flake8`, import real con el `.env` cargado y
simulación del flujo completo cuando toque. Lo que no se puede verificar se
enuncia como hipótesis, nunca como hecho.
*Este documento nació de ello: un aviso de "errores de sintaxis" resultó ser
nombres indefinidos, y el fallo real de la base de datos era un dominio mal escrito.*

## 2. Cambios mínimos y enfocados
Diagnóstico antes que parche. Arreglar lo que está roto sin reescribir lo que
funciona. No se reescriben archivos completos salvo que estén irreparables.

## 3. Marco antes que código
Leer esta constitución y la spec activa (`specs/NNN-*/`) antes de tocar código.

## 4. Preguntar antes de crear o romper compatibilidad
Preguntar antes de crear archivos nuevos o cambiar el formato de los datos
guardados: cambiarlo sin mantener compatibilidad hace perder las sesiones del
usuario. Los secretos (claves, tokens) nunca se escriben en el repo ni en la memoria.

## 5. Nada nuevo sin consultar
No se añaden dependencias, frameworks ni pasos de build por cuenta propia.

## 6. La app habla español
Textos de la interfaz, mensajes, nombres de usuario y comentarios en español.
