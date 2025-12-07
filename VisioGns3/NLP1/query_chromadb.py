# from sentence_transformers import SentenceTransformer
# import chromadb

# DB_PATH = "/home/athaar/INDA/VisioGns3/NLP1/chroma_db"

# print("Loading embedding model...")
# model = SentenceTransformer("all-MiniLM-L6-v2")   # FIXED

# client = chromadb.PersistentClient(path=DB_PATH)
# collection = client.get_collection("network_docs")

# while True:
#     query = input("\nEnter your query: ")

#     if query.lower() in ["exit", "quit"]:
#         break

#     embedding = model.encode([query]).tolist()

#     results = collection.query(
#         query_embeddings=embedding,
#         n_results=3
#     )

#     print("\n--- RESULTS ---")
#     for i, doc in enumerate(results["documents"][0]):
#         print(f"\nResult {i+1}:")
#         print(doc)
#         print(f"Score: {results['distances'][0][i]}")


from rag_pipeline import RAGPipeline
from sentence_transformers import SentenceTransformer

rag = RAGPipeline(
    chroma_path="/home/athaar/INDA/VisioGns3/NLP1/chroma_db",
    model_path="all-MiniLM-L6-v2"
)

results = rag.search("Draw a topology containing 3 switches and 2 routers with all the switches connected to both routers and routers connected to each other")
context = rag.format_context(results)

print(context)