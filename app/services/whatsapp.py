import os
from dotenv import load_dotenv
import httpx

load_dotenv()

def clean_number(phone_number: str):
    clean_number="".join(filter(str.isdigit, phone_number))
    if clean_number.startswith("521") and len(clean_number) == 13:
        clean_number= "52" +clean_number[3:]
    
    return clean_number


async def send_response_to_meta(phone_number: str, ia_response: str, whapp_token: str, whapp_id:str):
    try:
        url=f"https://graph.facebook.com/v25.0/{whapp_id}/messages"
        headers = {
            "Authorization": f"Bearer {whapp_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number.strip(),
            "type": "text",
            "text": {"body": ia_response}
        }

        async with httpx.AsyncClient() as client:
            await client.post(url= url, json=payload, headers=headers)
    except Exception as e:
        raise RuntimeError(f"Back: Error send response to meta: {e}")



async def get_audio_bytes(audio_id, whapp_token:str):
    headers = {"Authorization": f"Bearer {whapp_token}"}

    async with httpx.AsyncClient() as client:
        url_download= f"https://graph.facebook.com/v25.0/{audio_id}"

        response=await client.get(url_download, headers= headers)
        if response.status_code != 200:
            raise RuntimeError(f"Back: Can not get audio url: {response.text}")
        
        data=response.json()
        download_url=data.get("url")

        audio_bytes= await client.get(download_url, headers= headers)

        if audio_bytes.status_code != 200:
            raise RuntimeError("Back: Error downloading audio")

        return audio_bytes.content



async def show_typing_icon(message_id:str, whatsapp_token:str, phone_id:str):
    url = f"https://graph.facebook.com/v25.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {
            "type": "text"
        }
    }

    async with httpx.AsyncClient() as client:
        await client.post(url= url, json= payload, headers=headers)