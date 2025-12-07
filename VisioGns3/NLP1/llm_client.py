# llm_client.py
import os
import subprocess
import shlex

LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama")  # "ollama" or "test"

def query_phi35(prompt: str, timeout: int = 300) -> str:
    """
    Query local phi3.5 via chosen backend.
    - If LLM_BACKEND=ollama, uses: ollama run phi3.5 (stdin -> model)
      (Assumes ollama CLI is installed and model 'phi3.5' is available)
    - If LLM_BACKEND=test, returns prompt (useful for debugging)
    """
    if LLM_BACKEND == "ollama":
        # Use subprocess: pass prompt via stdin and capture stdout
        # ollama run <model> reads from stdin when no args are given
        try:
            proc = subprocess.run(
                ["ollama", "run", "phi3.5"],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=True
            )
            return proc.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"LLM process failed: {e.stderr}") from e
    else:
        # Test mode - return the last JSON-like block if present, or an empty template
        # Helpful for local unit testing without a real model.
        sample = """
{
  "machines": ["switch 1", "switch 2", "switch 3", "router 1", "router 2"],
  "connections": [
    {"from": "router 1", "to": "switch 1", "from_adapter_number": 0, "to_adapter_number": 0},
    {"from": "router 1", "to": "switch 2", "from_adapter_number": 1, "to_adapter_number": 0},
    {"from": "router 1", "to": "switch 3", "from_adapter_number": 2, "to_adapter_number": 0},
    {"from": "router 1", "to": "router 2", "from_adapter_number": 3, "to_adapter_number": 0},
    {"from": "router 2", "to": "switch 1", "from_adapter_number": 1, "to_adapter_number": 1},
    {"from": "router 2", "to": "switch 2", "from_adapter_number": 2, "to_adapter_number": 1},
    {"from": "router 2", "to": "switch 3", "from_adapter_number": 3, "to_adapter_number": 1}
  ]
}
"""
        return sample
