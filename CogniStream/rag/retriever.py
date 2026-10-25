"""
CogniStream - Phase 4: retrieval part of RAG (Member 3 owns rag/).

Steps:  load documents -> split into chunks -> embed -> store -> search.

Embedding backends (chosen automatically):
  1. "sentence-transformers"  (neural embeddings, all-MiniLM-L6-v2)  if installed
  2. "tfidf"                  (keyword-based vectors, scikit-learn)  otherwise
Vector store: FAISS if installed, otherwise plain NumPy cosine search.
Set environment variable COGNISTREAM_EMBEDDINGS=tfidf to force the light backend.
"""
import json
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DOC_DIR = ROOT / "docs"
REPORT_FILES = [ROOT / "reports" / "eda_findings.md", ROOT / "reports" / "data_quality_report.md"]
INDEX_DIR = ROOT / "rag" / "index"
MAX_CHARS = 900
MIN_SCORE = {"tfidf": 0.12, "sentence-transformers": 0.30}


# ---------- 1. load + chunk ----------
def load_documents():
    """Return a list of (source_name, text). Missing optional report files are skipped."""
    docs = []
    for path in sorted(DOC_DIR.glob("*.md")):
        docs.append((f"docs/{path.name}", path.read_text(encoding="utf-8")))
    for path in REPORT_FILES:
        if path.exists():
            docs.append((f"reports/{path.name}", path.read_text(encoding="utf-8")))
    if not docs:
        raise FileNotFoundError("No documents found. Expected markdown files in the docs/ folder.")
    return docs


def _split_long(text):
    """Split text into pieces of at most MAX_CHARS, on blank lines first, then on lines."""
    pieces, buf = [], ""
    units = []
    for para in text.split("\n\n"):
        if len(para) <= MAX_CHARS:
            units.append(para)
        else:
            units.extend(para.split("\n"))
    for unit in units:
        if buf and len(buf) + len(unit) + 1 > MAX_CHARS:
            pieces.append(buf.strip())
            buf = ""
        buf += unit + "\n"
    if buf.strip():
        pieces.append(buf.strip())
    return pieces


def chunk_document(source, text):
    """Split one markdown document by headings, then by length."""
    sections, heading, buf = [], "(intro)", []
    for line in text.splitlines():
        if line.startswith("#"):
            sections.append((heading, "\n".join(buf)))
            heading, buf = line.lstrip("# ").strip(), []
        else:
            buf.append(line)
    sections.append((heading, "\n".join(buf)))

    chunks = []
    for heading, body in sections:
        if not body.strip():
            continue
        for piece in _split_long(body):
            chunks.append({"source": source, "heading": heading, "text": piece})
    return chunks


def build_chunks():
    chunks = []
    for source, text in load_documents():
        chunks.extend(chunk_document(source, text))
    for i, c in enumerate(chunks):
        c["id"] = i
    return chunks


def _embed_text(chunk):
    return f"{chunk['heading']}. {chunk['text']}"


# ---------- 2. embedding backends ----------
class TfidfBackend:
    name = "tfidf"

    def __init__(self, texts):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self.vec.fit(texts)

    def encode(self, texts):
        return self.vec.transform(texts).toarray().astype("float32")  # rows are L2-normalised


class SentenceTransformerBackend:
    name = "sentence-transformers"

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def encode(self, texts):
        return np.asarray(self.model.encode(list(texts), normalize_embeddings=True), dtype="float32")


def choose_backend(texts):
    if os.getenv("COGNISTREAM_EMBEDDINGS", "").lower() != "tfidf":
        try:
            return SentenceTransformerBackend()
        except Exception:  # not installed, or model could not be downloaded
            pass
    return TfidfBackend(texts)


# ---------- 3. the retriever ----------
class Retriever:
    def __init__(self, chunks, backend, vectors):
        self.chunks = chunks
        self.backend = backend
        self.vectors = vectors
        self.backend_name = backend.name
        self.min_score = MIN_SCORE[backend.name]
        self.store = "numpy"
        try:  # optional FAISS
            import faiss
            self.faiss_index = faiss.IndexFlatIP(vectors.shape[1])
            self.faiss_index.add(vectors)
            self.store = "faiss"
        except Exception:
            self.faiss_index = None

    def search(self, query, k=4):
        """Return the top-k chunks as dicts with a 'score' (cosine similarity)."""
        q = self.backend.encode([query])
        if self.faiss_index is not None:
            scores, idx = self.faiss_index.search(q, min(k, len(self.chunks)))
            pairs = list(zip(idx[0], scores[0]))
        else:
            sims = (self.vectors @ q[0])
            order = np.argsort(-sims)[:k]
            pairs = [(i, sims[i]) for i in order]
        return [dict(self.chunks[int(i)], score=round(float(s), 3)) for i, s in pairs if i >= 0]


# ---------- 4. save / load ----------
def save_index(retriever):
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    (INDEX_DIR / "chunks.json").write_text(json.dumps(retriever.chunks, indent=1), encoding="utf-8")
    (INDEX_DIR / "meta.json").write_text(json.dumps({"backend": retriever.backend_name}), encoding="utf-8")
    np.save(INDEX_DIR / "vectors.npy", retriever.vectors)


def build_retriever(save=True):
    chunks = build_chunks()
    texts = [_embed_text(c) for c in chunks]
    backend = choose_backend(texts)
    vectors = backend.encode(texts)
    retriever = Retriever(chunks, backend, vectors)
    if save:
        save_index(retriever)
    return retriever


def load_or_build():
    """Simple and safe: the index is small, so we rebuild it from the current documents."""
    return build_retriever(save=True)
