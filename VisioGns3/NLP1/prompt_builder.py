# def build_prompt(user_prompt: str, rag_context: str) -> str:
#     return f"""
# You are a network topology generator.

# STRICT RULES:
# - Only valid JSON.
# - List ALL machines and ALL connections explicitly in the JSON.
# - Do NOT use ellipses (...), shortcuts, or comments.
# - Use double quotes for all strings.
# - Include every connection exactly as the user requested.
# - I have to store your output as JSON, so it must be complete and perfectly formatted.
# JSON FORMAT (EXACT):
# {{
#   "machines": ["router 1", "switch 1"],
#   "connections": [
#     {{
#       "from": "switch 1",
#       "to": "router 1"
#     }}
#   ]
# }}


# User Request:
# {user_prompt}

# IMPORTANT: Output the **full list** of machines and connections explicitly, even if it is very long. Do not print anything else just the json.
# """




# # Context:
# # {rag_context}

def build_prompt(user_input: str, rag_context: str) -> str:
    """
    Builds the final prompt for the LLM with strict JSON instructions.
    """
    return f"""
You are a network topology generator. Based on the user's description and the examples provided, output the network topology
as valid JSON ONLY with the following structure:

{{
  "machines": ["router 1", "router 2", ...],
  "connections": [
    {{
      "from": "router 1",
      "to": "router 2"
    }},
    ...
  ]
}}

Do not include any comments, explanations, or ellipsis (...). Include **all machines and all connections explicitly**.

User description: {user_input}

Context from examples:
{rag_context}
"""
