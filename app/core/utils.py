from datetime import datetime
import pytz

def get_contexto_temporal():
    tz = pytz.timezone('America/Mexico_City')
    ahora = datetime.now(tz)
    return ahora.strftime('%A, %d de %B de %Y, %H:%M')