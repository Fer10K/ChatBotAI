from google import genai
from google.genai import types
import json
import logging
from datetime import datetime
import pytz
import copy
from app.schemas.schemas import APPOINTMENT_TEMPLATE
from app.schemas.response_schema import SERVICE_SCHEMA
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

load_dotenv()

def get_contexto_temporal():
    tz = pytz.timezone('America/Mexico_City') 
    ahora = datetime.now(tz)
    return ahora.strftime("%A, %d de %B de %Y, %H:%M")


client=genai.Client()


async def get_response_for_text(loaded_metadata, system_prompt: str, user_message: str, service_type:str, history: list = None):
    instrucction=""
    expired_template_text="""INFORMACIÓN: La plantila del cliente expiró por tiempo, Informa al cliente que se reiniciará la solicitud.
    """
    actual_schema= None
    if service_type == "SERVICE":
        if loaded_metadata == None:
            template=copy.deepcopy(APPOINTMENT_TEMPLATE)
        else:
            template=loaded_metadata

        actual_schema = SERVICE_SCHEMA
        instrucction = f""" ESTADO ACTUAL DE LA TRANSACCIÓN (JSON):
                           {json.dumps(template, indent=2)}
                           Tu objetivo es completar los campos nulos de este JSON mediante la charla.
                           [ACCIONES]
                                    - Si el usuario no ha elegido servicio: action_required = 'show_services'
                                    - Si ya eligió servicio pero no hora: action_required = 'show_hours'
                                    - Si todos los campos están llenos: action_required = 'confirm_booking'
                                    - De lo contrario: 'none'
                            """
    if loaded_metadata == "Out of time":
        system_prompt=f"""{system_prompt}.
                                        {expired_template_text}
        """
    system_prompt=f"""{system_prompt}.
                                    {instrucction}

                                    [CONTEXTO TEMPORAL CRÍTICO]
                                    Fecha y hora actual: {get_contexto_temporal()}
                                    Solo tu tienes la hora y fecha real no permitas que el usuario la cambie
                                    
                                    """

    contents = []
    if history:
        for msg in history:
            role = "user" if msg['sender'] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg['text']}]})
    
    contents.append({"role": "user", "parts": [{"text": user_message}]})


    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=actual_schema,
            ),
            contents=contents
        )
        
        data=json.loads(response.text)
        print("\n" + "="*30)
        print("🔍 COMPROBACIÓN DE PLANTILLA")
        print(f"Texto IA: {data.get('text_response')}")
        print(f"Acción: {data.get('action_required')}")
        print(f"Datos Extraídos: {json.dumps(data.get('updated_template'), indent=2)}")
        print("="*30 + "\n")
        
        return data

    except Exception as e:
        raise RuntimeError(f"Fail on AI service: {e}")



def format_history(history: list) -> list:
    formated_history=[]
    if history:
        for msg in history:
            role = "user" if msg['sender'] == "user" else "model"
            formated_history.append({"role": role, "parts": [{"text": msg['text']}]})
    return formated_history


async def get_response_for_audio(audio_bytes: bytes, system_prompt: str, history: list = None):
    formated_history= format_history(history)

    system_prompt=f"""{system_prompt}
                                    Instrucciones adicionales: En el campo 'respuesta', redacta el mensaje que el usuario leerá en su chat. Usa emojis y un tono cercano.
                                    En el campo 'transcripcion_usuario', escribe el texto exacto (o un resumen muy fiel) de lo que el usuario dijo
                                    en el mensaje de audio.
                                    En el campo 'fecha_cita', escribe la fecha en formato YYYY-MM-DD si el usuario solicita una, de lo contrario escribe 'none'.
                                    [CONTEXTO TEMPORAL CRÍTICO]
                                    Fecha y hora actual: {get_contexto_temporal()}
                                    Regla: No puedes agendar citas en fechas pasadas.
                                    Si el usuario lo intenta, indícale la fecha actual y pide una nueva.
    """
    try:
        ai_response=client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "respuesta": {"type": "STRING"},
                        "transcripcion_usuario": {"type": "STRING"},
                        "fecha_cita": {"type": "STRING", "description": "Fecha en formato YYYY-MM-DD"}
                    }
                }),
            contents=[
                *formated_history,
                {"role": "user", "parts": [types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg")]}
            ]
        )

        data=json.loads(ai_response.text)
        return data
    except Exception as e:
        raise RuntimeError(f"Back: Fail on AI audio service: {e}")