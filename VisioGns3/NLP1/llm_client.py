# llm_client.py
import subprocess

def query_llm(prompt: str, timeout: int = 600):
    """
    Run the local LLM (Qwen2.5-Coder 7B) with the given prompt and return the text output.
    Qwen2.5-Coder is significantly better than Mistral at producing strict JSON output.
    """
    proc = subprocess.run(
        ["ollama", "run", "qwen2.5-coder:7b"],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout
    )
    if proc.returncode != 0:
        raise RuntimeError(f"LLM error:\n{proc.stderr.decode('utf-8')}")
    return proc.stdout.decode("utf-8")