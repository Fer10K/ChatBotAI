from google.genai.types import HttpxAsyncClient
from app.services.whatsapp import show_typing_icon, get_audio_bytes, send_response_to_meta, clean_number
from app.services.ia_service import get_response_for_text, get_response_for_audio
from app.database.supabase import (
    get_history,
    get_set_sesion,
    update_lead_data,
    update_sesion,
    save_whapp_data_on_supabase,
)
import os
from dotenv import load_dotenv

load_dotenv()

async def set_background_task(phone_id: str, phone_number: str, message_id:str, user_name:str, user_message:str = None, audio_id: str=None):
    user_transcription= ""
    supabase_content=""

    phone_number= clean_number(phone_number)

    headers={"X-API-KEY": os.getenv("API_KEY_SECRETO")}

    try:
#------------------------------------------------------- GET BOT DATA------------------------------------------------------------------
        async with HttpxAsyncClient() as client:
            response=await client.get(
                f"{os.getenv('DEV_API_URL_BASE')}/api/v1/bots_info/id/{phone_id}",
                params={"phone_id": phone_id},
                headers=headers
            )
            bot_credentials=response.json()

        async with HttpxAsyncClient() as client:
            response=await client.get(
                f"{os.getenv('DEV_API_URL_BASE')}/api/v1/bots_info/bot_data/{bot_credentials['bot_id']}",
                params={"bot_id": bot_credentials["bot_id"]},
                headers=headers
            )
            bot_data=response.json()

        bot_id      = bot_credentials["bot_id"]
        whapp_token = bot_credentials["whatsapp_token"]
        whapp_id    = phone_id

        print("Back: Get bot data")
        system_prompt =bot_data["system_prompt"]
        service_type = bot_data["service_type"]


#------------------------------------------------------- SHOW TYPING ICON------------------------------------------------------------------
        print("Back: Show icon")
        await show_typing_icon(message_id, whapp_token, phone_id)


#------------------------------------------------------- GET DATA FROM DATABASE------------------------------------------------------------------
        print("Back: Get history")
        history_messages= await get_history(bot_id, phone_number)
        print("Back: Get sesion")
        loaded_metadata = await get_set_sesion(bot_id, phone_number)


        #------------------------------------------------------- GET RESPONSE------------------------------------------------------------------
        if user_message:
            print("Back: Send to ia service for text")
            json_ia_response=await get_response_for_text(loaded_metadata, system_prompt, user_message, service_type, history_messages)
            ia_response=json_ia_response.get("text_response")
        else:
            print("Back: Send to ia service for audio")
            audio_bytes=await get_audio_bytes(audio_id, whapp_token)
            json_ia_response=await get_response_for_audio(audio_bytes, system_prompt, history_messages)
            ia_response=json_ia_response["respuesta"]
            user_transcription=json_ia_response["transcripcion_usuario"]



        #------------------------------------------------------- SEND RESPONSE TO META------------------------------------------------------------------
        print("Back: Return to meta")
        print(ia_response)
        await send_response_to_meta(phone_number, ia_response, whapp_token, whapp_id)


        #------------------------------------------------------- SAVE DATA ON SUPABASE------------------------------------------------------------------
        print("Back: Update session")
        await update_lead_data(phone=phone_number, bot_id=bot_id, name=user_name, chat_summary=ia_response[:255])
        await update_sesion(bot_id, phone_number, json_ia_response.get("updated_template"))


        print("Back: Save data")
        if user_transcription != "":
            supabase_content= user_transcription
        else:
            supabase_content = user_message
        await save_whapp_data_on_supabase(bot_id, supabase_content, "user", phone_number)
        await save_whapp_data_on_supabase(bot_id, ia_response, "model", phone_number)



    except Exception as e:
        raise RuntimeError(f"Back: Error on set background task: {e}")
