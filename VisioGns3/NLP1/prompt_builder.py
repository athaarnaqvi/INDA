def build_prompt(user_prompt: str, rag_context: str) -> str:
    return f"""
You are a network topology generator.

STRICT RULES:
- Only valid JSON.
- List ALL machines and ALL connections explicitly in the JSON.
- Do NOT use ellipses (...), shortcuts, or comments.
- Use double quotes for all strings.
- Include every connection exactly as the user requested.
- I have to store your output as JSON, so it must be complete and perfectly formatted.
JSON FORMAT (EXACT):
{{
  "machines": ["router 1", "switch 1"],
  "connections": [
    {{
      "from": "switch 1",
      "to": "router 1"
    }}
  ]
}}

Context:
{rag_context}

User Request:
{user_prompt}

IMPORTANT: Output the **full list** of machines and connections explicitly, even if it is very long.
"""
