import os
from fastapi import HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv

load_dotenv()

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

def verificar_api_key(api_key: str = Depends(api_key_header)):

    if api_key != os.getenv("API_KEY_SECRETO", "TOKEN_TEMPORAL"):
        raise HTTPException(status_code=403, detail = "No autorizado: API key invalida")
    return api_key