import json
import re
from typing import Dict, List, Tuple

from rag_pipeline import RAGPipeline
from prompt_builder import build_prompt
from llm_client import query_llm


class TopologyGenerator:
    """
    High-level wrapper around a retrieval-augmented generation (RAG) pipeline for creating network topologies.

    Steps:
    1. RAGPipeline retrieves relevant knowledge base examples.
    2. A structured prompt is built and sent to the LLM.
    3. The LLM JSON output is parsed, validated, deduplicated, and heuristically completed.
    """

    def __init__(self, chroma_path: str, embed_model: str):
        self.rag = RAGPipeline(chroma_path=chroma_path, model_path=embed_model)

    # -------------------------------------------------------------------------
    # JSON extraction and cleaning
    # -------------------------------------------------------------------------
    def _extract_json_text(self, text: str) -> str:
        # Strategy 1: fenced code block
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        # Strategy 2: brace counting from first '{'
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
        raise ValueError("No complete JSON object found in LLM output.")

    def _clean_json_text(self, json_text: str) -> str:
        json_text = re.sub(r',\s*(\}|\])', r'\1', json_text)
        json_text = re.sub(r'//.*?\n', '\n', json_text)
        json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)
        return json_text

    def _safe_parse(self, text: str) -> Dict:
        try:
            json_text = self._extract_json_text(text)
            json_text = self._clean_json_text(json_text)
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            try:
                repaired = re.sub(r'}\s*{', '},{', json_text)
                repaired = repaired.replace('\\n', ' ').replace('\\t', ' ')
                return json.loads(repaired)
            except Exception:
                raise RuntimeError(
                    f"JSON parse failed after cleanup.\nError: {e}\nCleaned JSON:\n{json_text[:500]}..."
                )

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------
    def _validate_output(self, parsed: Dict) -> Dict:
        if 'machines' not in parsed or 'connections' not in parsed:
            raise RuntimeError("Invalid topology: missing 'machines' or 'connections'")
        if not isinstance(parsed['machines'], list):
            raise RuntimeError("'machines' must be a list")
        if not isinstance(parsed['connections'], list):
            raise RuntimeError("'connections' must be a list")

        machine_set = set(parsed['machines'])
        for idx, conn in enumerate(parsed['connections']):
            if not isinstance(conn, dict):
                raise RuntimeError(f"Connection {idx} is not a dict")
            if 'from' not in conn or 'to' not in conn:
                raise RuntimeError(f"Connection {idx} missing 'from' or 'to'")
            if conn['from'] not in machine_set:
                print(f"[WARN] 'from' device '{conn['from']}' not in machines list")
            if conn['to'] not in machine_set:
                print(f"[WARN] 'to' device '{conn['to']}' not in machines list")
        return parsed

    # -------------------------------------------------------------------------
    # Deduplication — KEY FIX: removes duplicates added by bad LLM runs or
    # previous heuristic passes that polluted the context via RAG retrieval.
    # Treats A→B and B→A as the same undirected edge.
    # -------------------------------------------------------------------------
    def _deduplicate_connections(self, connections: List[Dict]) -> List[Dict]:
        seen: set = set()
        result = []
        for conn in connections:
            # Strip extra keys (e.g. adapter numbers from old schema) — keep only from/to
            edge = (
                min(conn['from'], conn['to']),
                max(conn['from'], conn['to'])
            )
            if edge not in seen:
                seen.add(edge)
                result.append({"from": conn['from'], "to": conn['to']})
        return result

    # -------------------------------------------------------------------------
    # Heuristic completion — only fires when the user explicitly states a
    # structural requirement that the LLM missed.  Uses broad keyword matching
    # to be robust to paraphrasing.
    # -------------------------------------------------------------------------
    def _connection_exists(self, connections: List[Dict], a: str, b: str) -> bool:
        for c in connections:
            if (c['from'] == a and c['to'] == b) or (c['from'] == b and c['to'] == a):
                return True
        return False

    def _apply_heuristics(self, validated: Dict, user_prompt: str) -> Dict:
        lower = user_prompt.lower()
        connections = validated['connections']
        machines = validated['machines']

        routers = [m for m in machines if m.lower().startswith('router')]
        switches = [m for m in machines if m.lower().startswith('switch')]
        non_routers = [m for m in machines if not m.lower().startswith('router')]

        # --- Routers connected to each other (full mesh among routers) ---
        router_mesh_phrases = [
            'routers connected to each other',
            'router connected to router',
            'routers interconnected',
            'routers linked to each other',
            'routers form a ring',          # ring among routers
        ]
        if any(p in lower for p in router_mesh_phrases) and len(routers) >= 2:
            for i in range(len(routers)):
                for j in range(i + 1, len(routers)):
                    if not self._connection_exists(connections, routers[i], routers[j]):
                        connections.append({"from": routers[i], "to": routers[j]})
                        print(f"[HEURISTIC] Added missing router-router link: {routers[i]} → {routers[j]}")

        # --- "connected to both routers" — every non-router links to every router ---
        both_router_phrases = [
            'connected to both routers',
            'connected to all routers',
            'each switch connected to both routers',
            'switches connected to both routers',
        ]
        if any(p in lower for p in both_router_phrases) and routers:
            targets = switches if switches else non_routers  # prefer switches as per typical use
            for device in targets:
                for router in routers:
                    if not self._connection_exists(connections, router, device):
                        connections.append({"from": router, "to": device})
                        print(f"[HEURISTIC] Added missing link: {router} → {device}")

        # --- Ring topology among a single device type ---
        ring_phrases = ['ring', 'loop', 'circular', 'ring configuration', 'ring topology']
        if any(p in lower for p in ring_phrases):
            # Determine which group forms the ring
            ring_group: List[str] = []
            if 'router' in lower and routers:
                ring_group = routers
            elif 'switch' in lower and switches:
                ring_group = switches
            else:
                ring_group = machines  # fall back to all machines

            if len(ring_group) >= 3:
                for i in range(len(ring_group)):
                    a = ring_group[i]
                    b = ring_group[(i + 1) % len(ring_group)]
                    if not self._connection_exists(connections, a, b):
                        connections.append({"from": a, "to": b})
                        print(f"[HEURISTIC] Added ring link: {a} → {b}")

        validated['connections'] = connections
        return validated

    # -------------------------------------------------------------------------
    # Main entry point
    # -------------------------------------------------------------------------
    def generate(self, user_prompt: str, top_k: int = 5) -> Dict:
        """
        Generate a topology for the given user_prompt using RAG + LLM.

        top_k is capped at 5 to avoid flooding the LLM with too many examples,
        which was a key cause of degraded performance on simple topologies after
        large-topology testing.
        """
        # Cap top_k — large context from big-topology examples confuses the model
        top_k = min(top_k, 5)

        print(f"\n[TOPOLOGY GENERATOR] Processing: {user_prompt}")

        # 1. RAG retrieval
        print("[RAG] Searching knowledge base...")
        rag_results = self.rag.search(user_prompt, top_k=top_k)
        context = self.rag.format_context(rag_results)
        retrieved_count = len(rag_results['documents'][0]) if rag_results and 'documents' in rag_results else 0
        print(f"[RAG] Retrieved {retrieved_count} relevant documents")

        # 2. Build prompt
        llm_prompt = build_prompt(user_prompt, context)
        print("[LLM] Sending prompt to language model...")
        print(f"[DEBUG] Prompt length: {len(llm_prompt)} characters")

        # 3. Query LLM
        raw_output = query_llm(llm_prompt)
        print(f"[LLM] Received response ({len(raw_output)} characters)")
        print(f"[DEBUG] First 200 chars: {raw_output[:200]}")

        # 4. Parse
        try:
            parsed = self._safe_parse(raw_output)
            print("[PARSER] Successfully parsed JSON")
        except Exception as e:
            print(f"[ERROR] Failed to parse LLM output: {e}")
            print(f"[DEBUG] Raw output:\n{raw_output}")
            raise RuntimeError(f"Failed to parse LLM output as JSON: {e}")

        # 5. Validate
        try:
            validated = self._validate_output(parsed)
        except Exception as e:
            print(f"[ERROR] Validation failed: {e}")
            raise RuntimeError(f"Invalid topology structure: {e}")

        # 6. Deduplicate BEFORE heuristics (removes any LLM duplicates)
        before = len(validated['connections'])
        validated['connections'] = self._deduplicate_connections(validated['connections'])
        after = len(validated['connections'])
        if before != after:
            print(f"[DEDUP] Removed {before - after} duplicate connections")

        # 7. Apply heuristics to fill structural gaps
        validated = self._apply_heuristics(validated, user_prompt)

        # 8. Deduplicate again after heuristics (safety net)
        validated['connections'] = self._deduplicate_connections(validated['connections'])

        print(f"[DONE] {len(validated['machines'])} machines, {len(validated['connections'])} connections")
        return validated