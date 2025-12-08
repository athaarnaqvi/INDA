# run_pipeline.py
"""
One-click runner for INDA Topology Extraction Pipeline.
Run this file directly in VS Code (Run ▶).

What it does automatically:
- Ensures correct backend (Ollama)
- Loads RAG + Phi-3.5
- Prompts user for input
- Generates machines.txt and connections.json
"""

import os
import sys
import shutil
import traceback
from topology_generator import TopologyGenerator
from output_writer import write_outputs

# ----------------------------------------------------
# CONFIG (edit ONLY if paths change)
# ----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.dirname(BASE_DIR)

CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")
GENERATED_FILES_DIR = os.path.join(
    PROJECT_ROOT,
    "Generated_files"
)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_BACKEND = "ollama"
TOP_K = 3


# ----------------------------------------------------
# ENVIRONMENT SETUP
# ----------------------------------------------------
def setup_environment():
    print("\n[SETUP] Initializing environment...")

    # Force backend internally (no terminal export needed)
    os.environ["LLM_BACKEND"] = LLM_BACKEND

    # Check Ollama existence
    if shutil.which("ollama") is None:
        print("\n[ERROR] Ollama not found.")
        print("→ Install Ollama and ensure 'ollama' is in PATH.\n")
        sys.exit(1)

    # Quick phi3.5 presence hint (non-fatal)
    print("[SETUP] Using mistral via Ollama\n")


# ----------------------------------------------------
# MAIN PIPELINE
# ----------------------------------------------------
def main():
    print("=" * 60)
    print(" INDA | LLM + RAG Network Topology Generator")
    print("=" * 60)

    # Step 1: Setup environment
    setup_environment()

    # Step 2: Get prompt via input()
    print("\nEnter topology description:")
    print("(Example: 3 switches, 2 routers, all switches connected to both routers)\n")
    user_prompt = input(">> ").strip()

    if not user_prompt:
        print("\n[ERROR] Empty prompt. Exiting.")
        return

    # Step 3: Initialize pipeline
    print("\n[PIPELINE] Loading RAG + LLM...")
    generator = TopologyGenerator(
        chroma_path=CHROMA_PATH,
        embed_model=EMBEDDING_MODEL
    )

    # Step 4: Generate topology
    print("\n[PIPELINE] Generating topology...\n")
    try:
        result = generator.generate(user_prompt, top_k=TOP_K)
    except Exception as e:
        print("[FAILED] Pipeline execution error:")
        traceback.print_exc()
        return

    # Step 5: Write outputs
    machines_path, connections_path = write_outputs(
    result,
    output_dir=GENERATED_FILES_DIR
)
    print("\n[SUCCESS] Topology generated!")
    print(f"→ Machines file: {machines_path}")
    print(f"→ Connections file: {connections_path}")

    print("\nDone ✅")


# ----------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------
if __name__ == "__main__":
    main()
