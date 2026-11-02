
"""
CogniStream - Phase 4: retrieval part of RAG (Member 3 owns rag/).

Steps: load documents -> split into chunks -> embed -> store -> search.

Embedding backends:
  1. sentence-transformers
  2. TF-IDF

Vector store: FAISS if installed, otherwise NumPy cosine search.
"""

import json
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DOC_DIR = ROOT / "docs"
REPORT_FILES = [
    ROOT / "reports" / "eda_findings.md",
    ROOT / "reports" / "data_quality_report.md",
]
INDEX_DIR = ROOT / "rag" / "index"

MAX_CHARS = 900

MIN_SCORE = {
    "tfidf": 0.12,
    "sentence-transformers": 0.30,
}


# ---------- 1. Load and chunk documents ----------

def load_documents():
    """Load Markdown documents from docs and reports folders."""
    docs = []

    for path in sorted(DOC_DIR.glob("*.md")):
        docs.append((
            f"docs/{path.name}",
            path.read_text(encoding="utf-8")
        ))

    for path in REPORT_FILES:
        if path.exists():
            docs.append((
                f"reports/{path.name}",
                path.read_text(encoding="utf-8")
            ))

    if not docs:
        raise FileNotFoundError(
            "No documents found. Expected markdown files in the docs/ folder."
        )

    return docs


def _split_long(text):
    """Split text into pieces of at most MAX_CHARS."""
    pieces = []

    for para in text.split("\n\n"):
        para = para.strip()

        if not para:
            continue

        if len(para) <= MAX_CHARS:
            pieces.append(para)
            continue

        words = para.split()
        buf = ""

        for word in words:
            while len(word) > MAX_CHARS:
                if buf:
                    pieces.append(buf)
                    buf = ""

                pieces.append(word[:MAX_CHARS])
                word = word[MAX_CHARS:]

            if not word:
                continue

            if buf and len(buf) + len(word) + 1 > MAX_CHARS:
                pieces.append(buf)
                buf = word
            else:
                buf = f"{buf} {word}".strip()

        if buf:
            pieces.append(buf)

    return pieces


def chunk_document(source, text):
    """Split one Markdown document by headings and text length."""
    sections = []
    heading = "(intro)"
    buf = []

    for line in text.splitlines():
        if line.startswith("#"):
            sections.append((heading, "\n".join(buf)))
            heading = line.lstrip("# ").strip()
            buf = []
        else:
            buf.append(line)

    sections.append((heading, "\n".join(buf)))

    chunks = []

    for heading, body in sections:
        if not body.strip():
            continue

        for piece in _split_long(body):
            chunks.append({
                "source": source,
                "heading": heading,
                "text": piece,
            })

    return chunks


def build_chunks():
    """Build document chunks and assign unique IDs."""
    chunks = []

    for source, text in load_documents():
        chunks.extend(chunk_document(source, text))

    for i, chunk in enumerate(chunks):
        chunk["id"] = i

    return chunks


def _embed_text(chunk):
    return f"{chunk['heading']}. {chunk['text']}"


# ---------- 2. Embedding backends ----------

class TfidfBackend:
    name = "tfidf"

    def __init__(self, texts):
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.vec = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )

        self.vec.fit(texts)

    def encode(self, texts):
        return self.vec.transform(texts).toarray().astype("float32")


class SentenceTransformerBackend:
    name = "sentence-transformers"

    def __init__(self):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def encode(self, texts):
        return np.asarray(
            self.model.encode(
                list(texts),
                normalize_embeddings=True
            ),
            dtype="float32",
        )


def choose_backend(texts):
    """Choose the available embedding backend."""
    if os.getenv("COGNISTREAM_EMBEDDINGS", "").lower() != "tfidf":
        try:
            return SentenceTransformerBackend()
        except Exception:
            pass

    return TfidfBackend(texts)


# ---------- 3. Retriever ----------

class Retriever:

    def __init__(self, chunks, backend, vectors):
        self.chunks = chunks
        self.backend = backend
        self.vectors = vectors

        self.backend_name = backend.name
        self.min_score = MIN_SCORE[backend.name]

        self.store = "numpy"

        try:
            import faiss

            self.faiss_index = faiss.IndexFlatIP(
                vectors.shape[1]
            )

            self.faiss_index.add(vectors)
            self.store = "faiss"

        except Exception:
            self.faiss_index = None

    def search(self, query, k=4):
        """Return top-k matching document chunks."""
        if not self.chunks:
            return []

        q = self.backend.encode([query])

        if self.faiss_index is not None:
            scores, idx = self.faiss_index.search(
                q,
                min(k, len(self.chunks))
            )

            pairs = list(zip(idx[0], scores[0]))

        else:
            sims = self.vectors @ q[0]
            order = np.argsort(-sims)[:k]

            pairs = [
                (i, sims[i])
                for i in order
            ]

        return [
            dict(
                self.chunks[int(i)],
                score=round(float(score), 3)
            )
            for i, score in pairs
            if i >= 0
        ]


# ---------- 4. Save and load index ----------

def save_index(retriever):
    """Save chunks, metadata and vectors."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    (INDEX_DIR / "chunks.json").write_text(
        json.dumps(retriever.chunks, indent=1),
        encoding="utf-8",
    )

    (INDEX_DIR / "meta.json").write_text(
        json.dumps({
            "backend": retriever.backend_name
        }),
        encoding="utf-8",
    )

    np.save(
        INDEX_DIR / "vectors.npy",
        retriever.vectors
    )


def build_retriever(save=True):
    """Build the retriever using current project documents."""
    chunks = build_chunks()
    texts = [_embed_text(chunk) for chunk in chunks]

    backend = choose_backend(texts)
    vectors = backend.encode(texts)

    result = Retriever(chunks, backend, vectors)

    if save:
        save_index(result)

    return result


def load_or_build():
    """Rebuild the index from current documents."""
    return build_retriever(save=True)
