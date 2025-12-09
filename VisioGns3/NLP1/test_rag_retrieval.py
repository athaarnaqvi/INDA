#!/usr/bin/env python3
"""
RAG Diagnostic Tool - Test if your RAG system is retrieving relevant examples.
Run this to verify RAG is working before testing the full pipeline.
"""

import os
import sys
from rag_pipeline import RAGPipeline

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def test_rag_retrieval():
    """Test RAG retrieval with sample queries."""
    
    print("="*70)
    print(" RAG SYSTEM DIAGNOSTIC TEST")
    print("="*70)
    
    # Initialize RAG
    try:
        print("\n[1/3] Initializing RAG pipeline...")
        rag = RAGPipeline(chroma_path=CHROMA_PATH, model_path=EMBEDDING_MODEL)
        print("✅ RAG pipeline initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize RAG: {e}")
        return False
    
    # Test queries
    test_queries = [
        "3 switches and 2 routers, all switches connected to both routers",
        "5 computers connected to one switch",
        "ring topology with 4 devices",
        "star topology with router at center",
        "tree topology with hierarchical structure"
    ]
    
    print("[2/3] Testing retrieval with sample queries...\n")
    print("-"*70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: {query}")
        print("-"*70)
        
        try:
            # Search
            results = rag.search(query, top_k=3)
            
            # Show what was retrieved
            print(f"✅ Retrieved {len(results['documents'][0])} documents\n")
            
            for j, (doc, score) in enumerate(zip(results['documents'][0], 
                                                  results['distances'][0]), 1):
                print(f"   Result {j} (distance: {score:.4f}):")
                # Show first 150 characters
                preview = doc[:150].replace('\n', ' ')
                print(f"   {preview}...\n")
            
            # Format context
            context = rag.format_context(results)
            print(f"📊 Formatted context length: {len(context)} characters")
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            continue
    
    print("\n" + "="*70)
    print("[3/3] Testing context formatting...")
    print("="*70)
    
    # Test with a specific query
    test_query = "create a network with 3 PCs and 1 switch"
    print(f"\n📝 Test Query: {test_query}\n")
    
    try:
        results = rag.search(test_query, top_k=3)
        context = rag.format_context(results)
        
        print("📋 FORMATTED CONTEXT:")
        print("-"*70)
        print(context[:500])  # Show first 500 chars
        if len(context) > 500:
            print(f"\n... [{len(context) - 500} more characters]")
        print("-"*70)
        
        print("\n✅ Context formatting successful")
        
    except Exception as e:
        print(f"❌ Context formatting failed: {e}")
        return False
    
    print("\n" + "="*70)
    print(" DIAGNOSTIC COMPLETE")
    print("="*70)
    print("\n✅ RAG system is working correctly!")
    print("\nNext steps:")
    print("  1. If retrieval looks good, run: python run_pipeline.py")
    print("  2. If results seem irrelevant, try rebuilding ChromaDB:")
    print("     python local_embeddings_chromadb.py")
    print()
    
    return True


def check_prerequisites():
    """Check if all required files exist."""
    print("Checking prerequisites...")
    
    checks = {
        "ChromaDB": CHROMA_PATH,
        "Knowledge Base": os.path.join(BASE_DIR, "knowledge_base"),
        "Preprocessed Chunks": os.path.join(BASE_DIR, "rag_preprocessed_chunks.json")
    }
    
    all_good = True
    for name, path in checks.items():
        if os.path.exists(path):
            print(f"  ✅ {name}: {path}")
        else:
            print(f"  ❌ {name} NOT FOUND: {path}")
            all_good = False
    
    if not all_good:
        print("\n⚠️  Missing files detected. Please run:")
        print("  1. python rag_documents_creation.py")
        print("  2. python rag_preprocessing.py")
        print("  3. python local_embeddings_chromadb.py")
        return False
    
    print()
    return True


if __name__ == "__main__":
    print()
    
    if not check_prerequisites():
        sys.exit(1)
    
    try:
        success = test_rag_retrieval()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)