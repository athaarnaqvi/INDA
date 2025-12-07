# topology_pipeline.py
import json
import re
from rag_pipeline import RAGPipeline
from prompt_builder import build_prompt
from llm_client import query_phi35


class TopologyGenerator:
    def __init__(self, chroma_path: str, embed_model: str):
        self.rag = RAGPipeline(chroma_path=chroma_path, model_path=embed_model)

    def _extract_json_text(self, text: str) -> str:
        """
        Try to extract the first JSON object from arbitrary text.
        Strategy: find the first '{' and the last matching '}' after it.
        This is robust to extra preamble or trailing commentary.
        """
        # find first '{'
        start = text.find('{')
        if start == -1:
            raise ValueError("No JSON object found in LLM output.")
        # naive approach: find last '}' after start
        end = text.rfind('}')
        if end == -1 or end < start:
            raise ValueError("No complete JSON object found in LLM output.")
        return text[start:end+1]

    def _safe_parse(self, text: str):
        """
        Safely parse LLM JSON output by cleaning common corruption.
        """

        # Step 1: Extract JSON block
        json_text = self._extract_json_text(text)

        # Step 2: REMOVE hallucinated garbage like:
        # z: to_adapter_number): 0
        json_text = re.sub(
            r"[a-zA-Z]+:\s*[a-zA-Z_]+\)\s*:\s*\d+",
            "",
            json_text
        )

        # Step 3: Remove trailing commas
        json_text = re.sub(r",\s*([\]}])", r"\1", json_text)

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"JSON parse failed after cleanup.\n"
                f"Cleaned JSON:\n{json_text}"
            )
        

    def generate(self, user_prompt: str, top_k: int = 3):
        # 1. RAG search
        rag_results = self.rag.search(user_prompt, top_k=top_k)
        context = self.rag.format_context(rag_results)

        # 2. Build final prompt
        llm_prompt = build_prompt(user_prompt, context)

        # 3. LLM inference
        raw_output = query_phi35(llm_prompt)

        # 4. Parse JSON safely
        try:
            parsed = self._safe_parse(raw_output)
        except Exception as e:
            raise RuntimeError(f"Failed to parse LLM output as JSON: {e}\nLLM raw output:\n{raw_output}")

        # 5. Validate schema
        if "machines" not in parsed or "connections" not in parsed:
            raise RuntimeError("Invalid topology format")

        for conn in parsed["connections"]:
            if "from" not in conn or "to" not in conn:
                raise RuntimeError("Invalid connection entry")
        return parsed
