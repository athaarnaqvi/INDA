def build_prompt(user_input: str, rag_context: str) -> str:
    """
    Build the final prompt for the LLM using RAG context and explicit rules.

    Key design decisions:
    - No contradictions between rules (old version had rule 6 vs rule 7 conflict).
    - Explicitly tells the LLM to count devices and connections before outputting.
    - Does NOT ask for adapter numbers (schema_validator.py is unused; keep schema simple).
    """
    return f"""You are a network topology generator. Output ONLY a single valid JSON object — no explanation, no markdown, no code fences.

JSON FORMAT (use exactly this structure):
{{
  "machines": ["device_type number", ...],
  "connections": [
    {{"from": "device_type number", "to": "device_type number"}},
    ...
  ]
}}

RULES:
1. Device naming: "device_type number" starting at 1 per type. Examples: "router 1", "switch 2", "pc 3".
2. Valid device types: router, switch, hub, pc, laptop, server, cloud.
3. List EVERY machine explicitly — no shortcuts or "...".
4. List EVERY connection explicitly — no shortcuts or "...".
5. Only use "from" and "to" keys in connections. No other keys.
6. Before writing the JSON, mentally count: (a) how many of each device type, (b) which pairs must be connected per the description. Then output exactly those.
7. Do NOT add connections that are not stated or implied by the user's description.
8. Do NOT omit connections that ARE stated or implied by the user's description.

REFERENCE EXAMPLES (retrieved from knowledge base):
{rag_context}

USER REQUEST:
{user_input}

JSON OUTPUT:"""


def build_prompt_v2(user_input: str, rag_context: str) -> str:
    """
    Alternate prompt with even tighter formatting. Use for testing.
    """
    return f"""Generate a JSON network topology. Output ONLY the JSON object, nothing else.

OUTPUT SCHEMA:
{{
  "machines": ["router 1", "switch 1", "pc 1", ...],
  "connections": [
    {{"from": "router 1", "to": "switch 1"}},
    {{"from": "switch 1", "to": "pc 1"}}
  ]
}}

STRICT RULES:
- Device names: lowercase "type number" (e.g. router 1, switch 2, pc 3)
- Valid types: router, switch, hub, pc, laptop, server, cloud
- Include EVERY device and EVERY connection — no omissions, no shortcuts
- Keys in connections: only "from" and "to"
- Count devices and connections mentally before writing

KNOWLEDGE BASE EXAMPLES:
{rag_context}

USER DESCRIPTION:
{user_input}

OUTPUT (JSON only):"""