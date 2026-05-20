APPOINTMENT_TEMPLATE = {
    "intent": "appointment",
    "data": {
        "item_id": None,
        "item_name": None,
        "date": None,
        "time": None,
        "confirmed": False
    }
}

UPDATE_SESSION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "item_id": {"type": "STRING"},
        "item_name": {"type": "STRING"},
        "date": {"type": "STRING"},
        "time": {"type": "STRING"},
        "confirmed": {"type": "BOOLEAN"}
    }
}