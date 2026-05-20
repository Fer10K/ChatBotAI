from fastapi import APIRouter, HTTPException
from app.database.supabase import get_bot_data, get_bot_credentials

router = APIRouter()

@router.get("/id/{phone_id}")
async def get_bots_credentials(phone_id: str):
    res = await get_bot_credentials(phone_id)
    if res:
        return {"bot_id": res.bot_id, "whatsapp_token": res.access_token}
    else:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

@router.get("/bot_data/{bot_id}")
async def get_bots_data(bot_id):
    res = await get_bot_data(bot_id)
    if res:
        return {"system_prompt": res.system_prompt, "service_type": res.service_type}
    else:
        return {"system_prompt": None, "service_type": None}
    