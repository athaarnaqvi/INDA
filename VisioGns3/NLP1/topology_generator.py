import json
import re
from typing import Dict

from rag_pipeline import RAGPipeline
from prompt_builder import build_prompt
from llm_client import query_llm


class TopologyGenerator:
    """
    High-level wrapper around a retrieval-augmented generation (RAG) pipeline for creating network topologies.

    This class performs the following steps:
    1. Uses RAGPipeline to search a knowledge base for examples relevant to the user's prompt.
    2. Builds a prompt for the LLM that includes the user's description and the retrieved examples.
    3. Queries the LLM for a JSON description of the topology.
    4. Parses and validates the JSON to ensure it matches the expected schema.
    """

    def __init__(self, chroma_path: str, embed_model: str):
        self.rag = RAGPipeline(chroma_path=chroma_path, model_path=embed_model)

    # -------------------------------------------------------------------------
    # Utility functions for JSON extraction and cleaning
    # -------------------------------------------------------------------------
    def _extract_json_text(self, text: str) -> str:
        """
        Attempt to extract the first JSON object from a free‑form string.

        The LLM sometimes returns additional prose or markdown. This function
        searches for a JSON object enclosed in braces and returns the text
        representing that object. If no JSON is found, a ValueError is raised.
        """
        # Strategy 1: Look for fenced JSON code blocks
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(code_block_pattern, text, re.DOTALL)
        if match:
            return match.group(1)

        # Strategy 2: Find first JSON object based on brace counting
        start = text.find('{')
        if start == -1:
            raise ValueError("No JSON object found in LLM output.")
        brace_count = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return text[start:i + 1]
        # If we get here, braces never balanced
        raise ValueError("No complete JSON object found in LLM output.")

    def _clean_json_text(self, json_text: str) -> str:
        """
        Clean up common JSON formatting issues.

        - Remove trailing commas before closing braces or brackets.
        - Strip any stray comments or non‑JSON annotations.
        """
        # Remove trailing commas such as `, }` or `, ]`
        json_text = re.sub(r',\s*(\}|\])', r'\1', json_text)
        # Remove simple inline comments (e.g. // comment)
        json_text = re.sub(r'//.*?\n', '\n', json_text)
        # Remove block comments (/* ... */)
        json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)
        return json_text

    def _safe_parse(self, text: str) -> Dict:
        """
        Attempt to parse a JSON object from the LLM's raw output.

        If parsing fails, try a series of cleanup steps before giving up.
        """
        try:
            json_text = self._extract_json_text(text)
            json_text = self._clean_json_text(json_text)
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            # As a last resort, try to repair common issues
            try:
                # Replace concatenated objects "}{" with "},{"
                repaired = re.sub(r'}\s*{', '},{', json_text)
                repaired = repaired.replace('\\n', ' ').replace('\\t', ' ')
                return json.loads(repaired)
            except Exception:
                raise RuntimeError(
                    f"JSON parse failed after cleanup.\n"
                    f"Error: {e}\n"
                    f"Cleaned JSON:\n{json_text[:500]}..."
                )

    def _validate_output(self, parsed: Dict) -> Dict:
        """
        Validate the LLM's parsed JSON against expected topology schema.

        Ensures 'machines' and 'connections' are lists of the correct types. Warns
        about references to devices not present in the machines list.
        """
        if 'machines' not in parsed or 'connections' not in parsed:
            raise RuntimeError("Invalid topology format: missing 'machines' or 'connections'")
        # Ensure lists
        if not isinstance(parsed['machines'], list):
            raise RuntimeError("'machines' must be a list")
        if not isinstance(parsed['connections'], list):
            raise RuntimeError("'connections' must be a list")
        # Validate connections
        for idx, conn in enumerate(parsed['connections']):
            if not isinstance(conn, dict):
                raise RuntimeError(f"Connection {idx} is not a dictionary")
            if 'from' not in conn or 'to' not in conn:
                raise RuntimeError(f"Connection {idx} missing 'from' or 'to'")
            # Warn if connection references unknown device
            if conn['from'] not in parsed['machines']:
                print(f"Warning: connection 'from' device '{conn['from']}' not in machines list")
            if conn['to'] not in parsed['machines']:
                print(f"Warning: connection 'to' device '{conn['to']}' not in machines list")
        return parsed

    def generate(self, user_prompt: str, top_k: int = 8) -> Dict:
        """
        Generate a topology for the given user_prompt using retrieval‑augmented generation.

        :param user_prompt: Natural language description of the network.
        :param top_k: Number of documents to retrieve from the knowledge base.
        :returns: A dictionary with keys 'machines' and 'connections'.
        """
        print(f"\n[TOPOLOGY GENERATOR] Processing: {user_prompt}")

        # ------------------------------------------------------------------
        # 1. RAG retrieval and context formatting
        # ------------------------------------------------------------------
        print("[RAG] Searching knowledge base...")
        rag_results = self.rag.search(user_prompt, top_k=top_k)
        context = self.rag.format_context(rag_results)
        retrieved_count = len(rag_results['documents'][0]) if rag_results and 'documents' in rag_results else 0
        print(f"[RAG] Retrieved {retrieved_count} relevant documents")

        # ------------------------------------------------------------------
        # 2. Build the LLM prompt
        # ------------------------------------------------------------------
        llm_prompt = build_prompt(user_prompt, context)
        print("[LLM] Sending prompt to language model...")
        print(f"[DEBUG] Prompt length: {len(llm_prompt)} characters")

        # ------------------------------------------------------------------
        # 3. Query the LLM
        # ------------------------------------------------------------------
        raw_output = query_llm(llm_prompt)
        print(f"[LLM] Received response ({len(raw_output)} characters)")
        print(f"[DEBUG] First 200 chars: {raw_output[:200]}")

        # ------------------------------------------------------------------
        # 4. Parse and validate the JSON
        # ------------------------------------------------------------------
        try:
            parsed = self._safe_parse(raw_output)
            print("[PARSER] Successfully parsed JSON")
        except Exception as e:
            print(f"[ERROR] Failed to parse LLM output: {e}")
            print(f"[DEBUG] Raw output:\n{raw_output}")
            raise RuntimeError(f"Failed to parse LLM output as JSON: {e}")

        try:
            validated = self._validate_output(parsed)
        except Exception as e:
            print(f"[ERROR] Validation failed: {e}")
            raise RuntimeError(f"Invalid topology structure: {e}")

        # ------------------------------------------------------------------
        # 5. Optional heuristic post-processing
        # ------------------------------------------------------------------
        # As an extra guard, ensure that explicit statements like "routers connected
        # to each other" or "connected to both routers" are honoured by adding
        # missing connections *without creating duplicates*. We do not add
        # symmetrical duplicates if at least one direction exists between a pair.
        lower_prompt = user_prompt.lower()

        # Helper to check if a connection exists in either direction
        def _connection_exists(a: str, b: str) -> bool:
            for c in validated['connections']:
                if (c['from'] == a and c['to'] == b) or (c['from'] == b and c['to'] == a):
                    return True
            return False

        # If the user explicitly says routers are connected to each other,
        # ensure at least one connection between every pair of routers. We add
        # only a single direction (first->second) when none exists.
        if 'routers connected to each other' in lower_prompt or 'router connected to router' in lower_prompt:
            routers = [m for m in validated['machines'] if m.lower().startswith('router')]
            if len(routers) >= 2:
                for i in range(len(routers)):
                    for j in range(i + 1, len(routers)):
                        if not _connection_exists(routers[i], routers[j]):
                            # Add one connection (routers[i] -> routers[j])
                            validated['connections'].append({"from": routers[i], "to": routers[j]})

        # If a device is "connected to both routers", ensure each non-router has
        # at least one connection to each router. Do not add duplicates if either
        # direction already exists.
        if 'connected to both routers' in lower_prompt:
            routers = [m for m in validated['machines'] if m.lower().startswith('router')]
            others = [m for m in validated['machines'] if not m.lower().startswith('router')]
            for device in others:
                for router in routers:
                    if not _connection_exists(router, device):
                        # Add connection in canonical direction (router -> device)
                        validated['connections'].append({"from": router, "to": device})

        print(f"[VALIDATOR] Output validated: {len(validated['machines'])} machines, {len(validated['connections'])} connections")
        return validated