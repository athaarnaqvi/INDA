import os
import json
from sentence_transformers import SentenceTransformer
import chromadb

# ---------------- CONFIG ---------------- #
BASE_DIR = "/home/fiza-wajid/INDA/VisioGns3/NLP1"
CHUNKS_JSON = os.path.join(BASE_DIR, "rag_preprocessed_chunks.json")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "network_docs"

# ---------------- LOAD CHUNKS ---------------- #
print(f"Loading chunks from: {CHUNKS_JSON}")
with open(CHUNKS_JSON, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks from {CHUNKS_JSON}")

# ---------------- EMBEDDING ---------------- #
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")  # local, lightweight

texts = [c["text"] for c in chunks]
print("Generating embeddings...")
embeddings = model.encode(texts, show_progress_bar=True)

# ---------------- CHROMA DB (new API) ---------------- #
# ✅ new-style client initialization
client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# Delete existing collection if exists
if COLLECTION_NAME in [c.name for c in client.list_collections()]:
    client.delete_collection(COLLECTION_NAME)

collection = client.create_collection(name=COLLECTION_NAME)

# Add chunks to ChromaDB
for c, emb in zip(chunks, embeddings):
    collection.add(
        ids=[c["chunk_id"]],
        embeddings=[emb.tolist()],
        metadatas=[c["metadata"]],
        documents=[c["text"]]
    )

print(f"✅ ChromaDB stored at {CHROMA_DB_DIR} with {len(chunks)} documents.")
