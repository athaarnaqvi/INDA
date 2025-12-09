def build_prompt(user_input: str, rag_context: str) -> str:
    """
    Build the final prompt for the LLM using RAG context and explicit rules.

    The prompt emphasises that *every* connection described by the user must be reflected in the output JSON.
    This helps reduce omissions (hallucinations) in the generated topology.
    """
    return f"""
You are a network topology generator assistant. Your task is to produce a valid JSON object describing the machines and their connections based on the user's network description.

CRITICAL RULES:
1. **Output only valid JSON**. Do not include explanations, markdown, code fences, or any extra text. Respond with a single JSON object.
2. Use **exactly** this JSON structure:
{{
  "machines": ["device_type number", "device_type number", ...],
  "connections": [
    {{"from": "device_type number", "to": "device_type number"}},
    ...
  ]
}}
3. Device naming: Use the format "device_type number" (e.g. "router 1", "switch 2", "pc 3"). Start numbering at 1 for each device type.
4. Valid device types: router, switch, hub, pc, laptop, server, cloud.
5. **List every machine explicitly** – never use "..." or shortcuts.
6. **List every connection explicitly**. If the user states that certain devices are connected (e.g. "routers connected to each other", "all switches connected to both routers"), you must include each of those connections in the output. Do not infer additional connections beyond those described or implied by the user’s description.
7. Use only the keys "from" and "to" in the connections list. Do not include any other properties.

EXAMPLES FROM KNOWLEDGE BASE:
{rag_context}

USER REQUEST:
{user_input}

YOUR RESPONSE (JSON ONLY):"""


def build_prompt_v2(user_input: str, rag_context: str) -> str:
    """
    Enhanced version with clearer structure and examples.
    """
    return f"""
You are a network topology JSON generator. Generate ONLY the JSON output.

STRICT OUTPUT FORMAT:
{{
  "machines": ["router 1", "switch 1", "pc 1", ...],
  "connections": [
    {{"from": "router 1", "to": "switch 1"}},
    {{"from": "switch 1", "to": "pc 1"}},
    ...
  ]
}}

RULES:
- Device names: "device_type number" (router 1, switch 2, pc 3)
- Valid types: router, switch, hub, pc, laptop, server, cloud
- List EVERY machine and EVERY connection
- No "...", no shortcuts, no comments
- ONLY output the JSON object

REFERENCE EXAMPLES:
{rag_context}

USER DESCRIPTION:
{user_input}

OUTPUT:"""