SERVICE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "text_response": {"type": "STRING", "description": "Mensaje para el cliente"},
        "updated_template": {
            "type": "OBJECT",
            "properties": {
                "item_id": {"type": "STRING"},
                "item_name": {"type": "STRING"},
                "date": {"type": "STRING"},
                "time": {"type": "STRING"},
                "confirmed": {"type": "BOOLEAN"}
            }
        },
        "action_required": {
            "type": "STRING",
            "enum": ["none", "show_services", "show_hours", "confirm_booking"]
        }
    },
    "required": ["text_response", "updated_template", "action_required"]
}

PRODUCT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "text_response": {"type": "STRING"},
        "updated_template": {
            "type": "OBJECT",
            "properties": {
                "items": {"type": "ARRAY", "items": {"type": "OBJECT"}},
                "delivery_method": {"type": "STRING"},
                "address": {"type": "STRING"},
                "confirmed": {"type": "BOOLEAN"}
            }
        },
        "action_required": {
            "type": "STRING",
            "enum": ["none", "show_products", "confirm_order"]
        }
    },
    "required": ["text_response", "updated_template", "action_required"]
}