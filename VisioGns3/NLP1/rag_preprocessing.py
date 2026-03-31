import os
import json
from pathlib import Path

try:
    import tiktoken
    use_tiktoken = True
except ImportError:
    print("⚠️ tiktoken not installed — using character-based chunking instead.")
    use_tiktoken = False


# --- CONFIG --- #
BASE_DIR = Path(__file__).resolve().parent

# FIX: rag_documents_creation.py writes to knowledge_base2, NOT knowledge_base.
# Using knowledge_base here caused RAG to run on stale/missing data.
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base2"

# Fallback: if knowledge_base2 doesn't exist, try knowledge_base
if not KNOWLEDGE_BASE_DIR.exists():
    fallback = BASE_DIR / "knowledge_base"
    if fallback.exists():
        print(f"⚠️ knowledge_base2 not found — falling back to {fallback}")
        KNOWLEDGE_BASE_DIR = fallback
    else:
        raise FileNotFoundError(
            f"Neither 'knowledge_base2' nor 'knowledge_base' found in {BASE_DIR}.\n"
            f"Run rag_documents_creation.py first to generate the knowledge base."
        )

OUTPUT_FILE = BASE_DIR / "rag_preprocessed_chunks.json"

CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


def read_all_docs(directory: Path):
    """Recursively read all .md and .json files in the knowledge base directory."""
    docs = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".md") or f.endswith(".json"):
                file_path = Path(root) / f
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        text = file.read()
                        docs.append({"path": str(file_path), "text": text})
                except Exception as e:
                    print(f"⚠️ Error reading {file_path}: {e}")
    return docs


def chunk_text(text: str, chunk_size: int, overlap: int):
    """Split text into overlapping chunks."""
    if use_tiktoken:
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        chunks = []
        for i in range(0, len(tokens), chunk_size - overlap):
            chunk = enc.decode(tokens[i:i + chunk_size])
            chunks.append(chunk)
        return chunks
    else:
        step = chunk_size * 4
        overlap_chars = overlap * 4
        chunks = []
        for i in range(0, len(text), step - overlap_chars):
            chunks.append(text[i:i + step])
        return chunks


def preprocess_docs():
    """Read all knowledge base files, chunk them, and store as JSON for embeddings."""
    print(f"🔍 Scanning knowledge base at: {KNOWLEDGE_BASE_DIR}")
    all_docs = read_all_docs(KNOWLEDGE_BASE_DIR)

    if not all_docs:
        raise RuntimeError(
            f"No .md or .json files found in {KNOWLEDGE_BASE_DIR}.\n"
            f"Run rag_documents_creation.py first."
        )

    preprocessed = []
    for doc in all_docs:
        chunks = chunk_text(doc["text"], CHUNK_SIZE, CHUNK_OVERLAP)
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                preprocessed.append({
                    "chunk_id": f"{Path(doc['path']).stem}_{i}",
                    "text": chunk.strip(),
                    "metadata": {
                        "source_file": Path(doc["path"]).name,
                        "source_path": doc["path"],
                        "chunk_index": i
                    }
                })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(preprocessed, f, indent=4, ensure_ascii=False)

    print(f"✅ {len(preprocessed)} chunks created and saved to {OUTPUT_FILE}")
    print(f"   (from {len(all_docs)} source files in {KNOWLEDGE_BASE_DIR})")


if __name__ == "__main__":
    preprocess_docs()