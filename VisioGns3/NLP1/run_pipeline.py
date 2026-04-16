#!/usr/bin/env python3
"""
Entry point for the INDA topology extraction pipeline.

This script wires together the environment setup, user interaction, RAG pipeline
initialisation and topology generation. It has been updated to make better use
of retrieval‑augmented generation (RAG) and provide clearer instructions to
the language model.
"""

import os
import sys
import shutil
import traceback
import json

from topology_generator import TopologyGenerator


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
# Determine the base directory relative to this file. All data (chroma db, output
# files) are resolved relative to this location.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Location of the ChromaDB directory. If this does not exist, the user must
# create it using local_embeddings_chromadb.py.
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")
# Name of the sentence transformer model used to generate embeddings.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
# LLM backend environment variable (e.g. "ollama"). This script will set
# LLM_BACKEND in the environment so that llm_client knows which backend to use.
LLM_BACKEND = "groq"
# Number of documents to retrieve from the knowledge base. A larger value can
# provide the LLM with more examples at the cost of longer prompts.
TOP_K = 5

# ---------------------------------------------------------------------------
# GENERATED FILE PATHS (NLP → GNS3 PIPELINE)
# ---------------------------------------------------------------------------

VISIOGNS3_DIR = os.path.dirname(BASE_DIR)
GENERATED_FILES_DIR = os.path.join(VISIOGNS3_DIR, "Generated_files")

MACHINES_OUTPUT = os.path.join(GENERATED_FILES_DIR, "machine_names.txt")
CONNECTIONS_OUTPUT = os.path.join(GENERATED_FILES_DIR, "pre_Connections.json")

# ---------------------------------------------------------------------------
# OUTPUT WRITER
# ---------------------------------------------------------------------------
def write_outputs(result: dict, machines_path: str = "machines.txt", connections_path: str = "connections.json") -> tuple:
    """
    Write the resulting topology to files. Machines are written as plain text
    (one per line) and connections are written as a pretty‑printed JSON list.

    :param result: Dictionary with 'machines' and 'connections'.
    :param machines_path: Path of the text file to write machines.
    :param connections_path: Path of the JSON file to write connections.
    :returns: A tuple of (machines_path, connections_path).
    """
    machines = result.get("machines", [])
    connections = result.get("connections", [])
    # Write machines
    with open(machines_path, "w") as f:
        for m in machines:
            f.write(f"{m}\n")
    # Write connections
    with open(connections_path, "w") as f:
        json.dump(connections, f, indent=4)
    return machines_path, connections_path


# ---------------------------------------------------------------------------
# ENVIRONMENT SETUP
# ---------------------------------------------------------------------------
def setup_environment() -> None:
    """
    Perform one‑time environment checks and configuration before running the
    topology generator. This includes verifying the presence of the LLM
    backend and the ChromaDB directory.
    """
    print("\n" + "=" * 60)
    print(" INDA | Network Topology Generator")
    print("=" * 60)
    print("\n[SETUP] Initializing environment...")

    # Force LLM backend for llm_client
    os.environ["LLM_BACKEND"] = LLM_BACKEND

    # Check for ChromaDB directory
    if not os.path.exists(CHROMA_PATH):
        print(f"\n[ERROR] ChromaDB not found at: {CHROMA_PATH}")
        print("→ Run: python local_embeddings_chromadb.py")
        sys.exit(1)
    print(f"[SETUP] Using LLM backend: {LLM_BACKEND} (API-based, no local server required)")
    print(f"[SETUP] ChromaDB path: {CHROMA_PATH}")
    print(f"[SETUP] Embedding model: {EMBEDDING_MODEL}")
    print(f"[SETUP] RAG context size: {TOP_K} documents\n")


# ---------------------------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the interactive topology generation pipeline."""
    setup_environment()
    # Prompt the user for a network description
    print("=" * 60)
    print(" Enter Network Topology Description")
    print("=" * 60)
    print("\nExamples:")
    print("  • 3 switches and 2 routers, all switches connected to both routers")
    print("  • 5 PCs connected to a switch")
    print("  • Star topology with router 1 at center and 4 servers")
    print("\nYour description:")
    user_prompt = input(">> ").strip()
    if not user_prompt:
        print("\n[ERROR] Empty prompt. Exiting.")
        return
    print("\n" + "=" * 60)
    # Initialize topology generator
    try:
        print("\n[INIT] Loading RAG pipeline...")
        generator = TopologyGenerator(chroma_path=CHROMA_PATH, embed_model=EMBEDDING_MODEL)
        print("[INIT] Pipeline loaded successfully\n")
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize pipeline:")
        traceback.print_exc()
        return
    # Generate topology
    print("=" * 60)
    print(" Generating Topology")
    print("=" * 60)
    try:
        result = generator.generate(user_prompt, top_k=TOP_K)
    except Exception:
        print(f"\n[ERROR] Pipeline execution failed:")
        traceback.print_exc()
        print("\n" + "=" * 60)
        print(" Troubleshooting Tips")
        print("=" * 60)
        print("1. Ensure your groq_API_KEY is set correctly in .env")
        print("2. Check internet connection (groq is API-based)")
        print("3. Verify the ChromaDB directory exists: ls -la chroma_db/")
        print("4. If JSON parsing fails, simplify the prompt")
        return
    # Write outputs
    print("\n" + "=" * 60)
    print(" Writing Output Files")
    print("=" * 60)
    try:
        os.makedirs(GENERATED_FILES_DIR, exist_ok=True)

        machines_path, connections_path = write_outputs(
            result,
            MACHINES_OUTPUT,
            CONNECTIONS_OUTPUT
        )
        print(f"\n[SUCCESS] Topology generated!")
        print("\n📄 Output Files:")
        print(f"   → Machines: {machines_path}")
        print(f"   → Connections: {connections_path}")
        print("\n📊 Summary:")
        print(f"   → {len(result['machines'])} devices")
        print(f"   → {len(result['connections'])} connections")
        # Display preview of devices and connections
        print("\n📋 Devices Preview:")
        for device in result['machines'][:5]:
            print(f"   • {device}")
        if len(result['machines']) > 5:
            remaining = len(result['machines']) - 5
            print(f"   • ... and {remaining} more")
        print("\n🔗 Connections Preview:")
        for conn in result['connections'][:3]:
            print(f"   • {conn['from']} → {conn['to']}")
        if len(result['connections']) > 3:
            remaining = len(result['connections']) - 3
            print(f"   • ... and {remaining} more")
        print("\n" + "=" * 60)
        print(" ✅ Pipeline Complete!")
        print("=" * 60 + "\n")
    except Exception:
        print(f"\n[ERROR] Failed to write output files:")
        traceback.print_exc()
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Pipeline stopped by user.")
        sys.exit(0)
    except Exception:
        print(f"\n[FATAL ERROR] Unexpected error:")
        traceback.print_exc()
        sys.exit(1)