# schema_validator.py
import json
from jsonschema import validate, ValidationError

TOPOLOGY_SCHEMA = {
    "type": "object",
    "required": ["machines", "connections"],
    "properties": {
        "machines": {
            "type": "array",
            "items": {"type": "string"}
        },
        "connections": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["from", "to", "from_adapter_number", "to_adapter_number"],
                "properties": {
                    "from": {"type": "string"},
                    "to": {"type": "string"},
                    "from_adapter_number": {"type": "integer", "minimum": 0},
                    "to_adapter_number": {"type": "integer", "minimum": 0}
                }
            }
        }
    }
}

def validate_topology(obj):
    try:
        validate(instance=obj, schema=TOPOLOGY_SCHEMA)
        return True, None
    except ValidationError as e:
        return False, str(e)
