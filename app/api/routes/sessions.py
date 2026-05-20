from fastapi import APIRouter, Depends, HTTPException
from google.genai.types import VertexAISearchDict
from app.database.supabase import get_set_sesion, update_sesion, get_history
from app.api.auth.security_api import verificar_api_key

router = APIRouter()

@router.get("/{phone_number}", dependencies=[Depends(verificar_api_key)])
async def get_sessions(bot_id: str, phone_number: str):
    metadata = await get_set_sesion(bot_id, phone_number)
    if metadata:
        return {"status": "active", "metadata": metadata}
    else:
        return {"status": "inactive", "metadata": None}


@router.post("/update", dependencies=[Depends(verificar_api_key)])
async def modify_session_template(bot_id: str, phone_number: str, metadata: dict):
    try:
        await update_sesion(bot_id, phone_number, metadata)
        return {"status": "updated", "message": "Successfully updated session template"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating session template: {e}")

@router.get("/history", dependencies=[Depends(verificar_api_key)])
async def get_db_history(bot_id: str, phone_number: str):
    res= await get_history(bot_id, phone_number)
    return