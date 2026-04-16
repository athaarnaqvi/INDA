# # llm_client.py
# import subprocess

# def query_llm(prompt: str, timeout: int = 600):
#     """
#     Run the local LLM (Qwen2.5-Coder 7B) with the given prompt and return the text output.
#     Qwen2.5-Coder is significantly better than Mistral at producing strict JSON output.
#     """
#     proc = subprocess.run(
#         ["ollama", "run", "qwen2.5-coder:7b"],
#         input=prompt.encode("utf-8"),
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         timeout=timeout
#     )
#     if proc.returncode != 0:
#         raise RuntimeError(f"LLM error:\n{proc.stderr.decode('utf-8')}")
#     return proc.stdout.decode("utf-8")

# llm_client.py
# llm_client.py

import os
import re
import json
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

# ─────────────────────────────────────────────────────────────
# Load environment variables
# ─────────────────────────────────────────────────────────────
dotenv_path = find_dotenv()

if dotenv_path:
    load_dotenv(dotenv_path)
else:
    print("[WARN] No .env file found. Falling back to system environment variables.")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not found.\n"
        "→ Create a .env file or export it as an environment variable.\n"
        "Example:\n"
        "  export GROQ_API_KEY=your_key_here"
    )

# ─────────────────────────────────────────────────────────────
# Initialize Groq client
# ─────────────────────────────────────────────────────────────
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# ─────────────────────────────────────────────────────────────
# Safe JSON parser (VERY IMPORTANT)
# ─────────────────────────────────────────────────────────────
def safe_parse(output: str):
    """
    Ensures valid JSON even if LLM adds extra text
    """
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        # fallback: extract JSON substring
        match = re.search(r"\{.*\}", output, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Invalid JSON from LLM:\n{output}")

# ─────────────────────────────────────────────────────────────
# LLM Query Function
# ─────────────────────────────────────────────────────────────
def query_llm(prompt: str, timeout: int = 60):
    """
    Query Groq API using OpenAI-compatible interface
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # ✅ best for structured output
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict JSON generator.\n"
                        "Output ONLY valid JSON.\n"
                        "Do NOT include explanations, text, or comments.\n"
                        "Ensure the JSON is properly formatted."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=2000
        )

        output = response.choices[0].message.content

        # Optional but recommended: validate JSON here
        parsed = safe_parse(output)

        # Return string (to keep compatibility with your pipeline)
        return json.dumps(parsed, indent=2)

    except Exception as e:
        raise RuntimeError(f"Groq API error:\n{str(e)}")