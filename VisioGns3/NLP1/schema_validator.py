# schema_validator.py
#
# FIX: The old validator required "from_adapter_number" and "to_adapter_number"
# but nothing in the pipeline generates or uses those fields. The schema now
# matches the actual output format: just "from" and "to" in connections.

import json
from jsonschema import validate, ValidationError

TOPOLOGY_SCHEMA = {
    "type": "object",
    "required": ["machines", "connections"],
    "properties": {
        "machines": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string"}
        },
        "connections": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["from", "to"],
                "additionalProperties": False,
                "properties": {
                    "from": {"type": "string"},
                    "to": {"type": "string"}
                }
            }
        }
    },
    "additionalProperties": False
}


def validate_topology(obj: dict) -> tuple:
    """
    Validate a topology dict against the schema.
    Returns (True, None) on success, (False, error_message) on failure.
    """
    try:
        validate(instance=obj, schema=TOPOLOGY_SCHEMA)
        return True, None
    except ValidationError as e:
        return False, str(e.message)


def validate_topology_semantics(obj: dict) -> list:
    """
    Additional semantic checks beyond JSON schema:
    - No self-connections (device connected to itself)
    - All connection endpoints exist in machines list
    - No duplicate connections (undirected)

    Returns a list of warning strings (empty = all good).
    """
    warnings = []
    machine_set = set(obj.get("machines", []))
    connections = obj.get("connections", [])

    seen_edges = set()
    for i, conn in enumerate(connections):
        src = conn.get("from", "")
        dst = conn.get("to", "")

        if src == dst:
            warnings.append(f"Connection {i}: self-loop on '{src}'")

        if src not in machine_set:
            warnings.append(f"Connection {i}: 'from' device '{src}' not in machines list")

        if dst not in machine_set:
            warnings.append(f"Connection {i}: 'to' device '{dst}' not in machines list")

        edge = (min(src, dst), max(src, dst))
        if edge in seen_edges:
            warnings.append(f"Connection {i}: duplicate edge between '{src}' and '{dst}'")
        else:
            seen_edges.add(edge)

    return warnings