"""
CogniStream - Phase 4: build the document index and show what was indexed.

Run from the project root:
    python rag/ingest.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag import retriever  # noqa: E402


def main():
    r = retriever.build_retriever(save=True)
    sources = sorted({c["source"] for c in r.chunks})
    print(f"Documents indexed : {len(sources)}")
    for s in sources:
        print("   -", s)
    print(f"Chunks            : {len(r.chunks)}")
    print(f"Embedding backend : {r.backend_name}")
    print(f"Vector store      : {r.store}")
    print(f"Saved to          : {retriever.INDEX_DIR}")
    if r.backend_name == "tfidf":
        print("Note: using keyword (TF-IDF) retrieval. For neural embeddings run: "
              "pip install sentence-transformers faiss-cpu")


if __name__ == "__main__":
    main()
