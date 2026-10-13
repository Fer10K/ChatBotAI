import os
import logging
from supabase import create_client
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

async def get_set_sesion(bot_id: str, phone_num: str):
    response=supabase.table("conversations").select("metadata, updated_at").eq("bot_id", bot_id).eq("num_phone", phone_num).execute()

    if response.data:
        session_data=response.data[0]
        metadata = session_data['metadata']
        updated_at_str = session_data['updated_at']
        last_update = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        saved_date_str = metadata.get('date')

        if (now - last_update) > timedelta(minutes=15):
            print("Error, Plantilla caducada (1/2)")
            return None


        if saved_date_str and saved_date_str != "null":
            saved_date = datetime.strptime(saved_date_str, "%Y-%m-%d").date()
            if saved_date < datetime.now().date():
                print("Error, Plantilla caducada (2/2)")
                return None
        return metadata
    return None


async def update_sesion(bot_id: str, num_phone: str, metadata):
    try:
        supabase.table("conversations").upsert(
            {
                "bot_id": bot_id,
                "num_phone": num_phone,
                "metadata": metadata,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }, on_conflict="bot_id, num_phone"
        ).execute()

    except Exception as e:
        raise RuntimeError(f"Error: updatig sesion: {e}")



async def get_bot_credentials(phone_id):
    res = supabase.table("bots").select("id, access_token").eq("phone_id", phone_id).execute()

    return res.data[0] if res.data else None


async def update_lead_data(phone: str, bot_id: str, name: str, chat_summary: str):
    try:
        supabase.table("leads").upsert({
            "bot_id": bot_id,
            "name": name,
            "phone": phone,
            "chat_summary": chat_summary
        }, on_conflict="phone").execute()
    except Exception as e:
        logger.error(f"Back: error updating lead table: {e}")
        


async def save_whapp_data_on_supabase(bot_id:str, content:str, role:str, phone:str):
    try:
        supabase.table("messages").insert({
            "bot_id": bot_id,
            "content":content,
            "role": role,
            "phone": phone
        }).execute()

    except Exception as e:
        raise RuntimeError(f"Back: error saving data: {e}")



async def get_bot_data(bot_id: str):
    try:
        bot_data=supabase.table("bots").select("system_prompt, service_type").eq("id", bot_id).execute()
        print(bot_data)
        if not bot_data.data:

            logger.warning(f"Bot not found: {bot_id}")
            raise ValueError("Bot not found")
            
        return bot_data.data[0]
    except Exception as e:
        logger.error(f"Back: error getting bot data: {e}")



async def get_history(bot_id: str, phone_number: str):
    try:
        res= supabase.table("messages") \
            .select("role, content") \
            .eq("bot_id", bot_id) \
            .eq("phone", phone_number) \
            .order("created_at", desc=True) \
            .limit(20) \
            .execute()

        history=[]

        for msg in reversed(res.data):
            history.append({"sender": msg['role'], "text": msg['content']})

        return history
    except Exception as e:
        logger.error(f"Back: error getting history: {e}")
        return []