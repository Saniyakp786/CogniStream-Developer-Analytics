"""
CogniStream - Phase 4: the AI assistant.

ask(question, df, retriever, api_key=None) returns a dict:
    {"answer": str, "sources": [..], "mode": "gemini" | "offline" | "no_evidence" | "empty",
     "note": str or None}

How it works
  1. Numeric questions -> Pandas facts from src/kpis.py (rag/analytics.py)
  2. Every question    -> top document chunks from the retriever
  3. If there is no evidence at all -> say so (no language model call, nothing invented)
  4. If a Gemini key exists -> Gemini writes a grounded answer from ONLY that evidence
     Otherwise (or if Gemini fails) -> evidence is shown directly (offline mode)

Privacy: only document chunks and aggregated numbers are sent to Gemini.
Raw dataset rows are never sent.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:  # python-dotenv is optional
    pass

from rag import analytics

DEFAULT_MODEL = "gemini-3.5-flash"  # change with GEMINI_MODEL in .env (check Google AI Studio)
TOP_K = 4

# A question must mention something about this project, otherwise we do not answer from
# the documents. This stops unrelated questions from matching by accident.
DOMAIN_TERMS = [
    "dataset", "data", "productiv", "flow", "focus", "cognitive", "load", "interrupt", "context",
    "developer", "session", "coding", "code", "quality", "metric", "kpi", "score", "task", "project",
    "clean", "bug", "meeting", "break", "experience", "remote", "hybrid", "office", "correl",
    "trend", "dashboard", "definition", "column", "outlier", "duplicate", "missing", "pattern",
    "observed", "insight", "finding", "cogni", "complexity", "overlap", "flag", "limitation",
]


def _about_project(question):
    q = question.lower()
    return any(t in q for t in DOMAIN_TERMS)

SYSTEM_RULES = """You are the analytics assistant of the CogniStream project (developer flow-state and cognitive load analytics).
Answer ONLY from the DOCUMENT CONTEXT and DATA FACTS below.
Rules:
- Never invent a metric definition, formula, number, or source. If the evidence does not contain the answer, say it is not available in the project documents.
- Cite evidence with its label in square brackets, for example [S1] or [D2].
- Clearly separate "Observed in the data" (facts) from "Possible explanation (not proven)".
- Never say that correlation proves causation. Mention that the dataset origin and the formulas of productivity_score and cognitive_load_level are not provided when relevant.
- Use simple English. If the user wrote in Hinglish, answer in simple Hinglish.
- Keep the answer short and clear."""


def get_api_key(explicit=None):
    return explicit or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def _build_prompt(question, chunks, facts):
    parts = [SYSTEM_RULES, "\n=== DOCUMENT CONTEXT ==="]
    for i, c in enumerate(chunks, 1):
        parts.append(f"[S{i}] ({c['source']} > {c['heading']})\n{c['text']}")
    if facts:
        parts.append("\n=== DATA FACTS (calculated with Pandas on the current dashboard filter) ===")
        for i, f in enumerate(facts, 1):
            parts.append(f"[D{i}] {f['label']} (from {f['source']})\n{f['text']}")
    parts.append(f"\n=== QUESTION ===\n{question}")
    return "\n".join(parts)


def _call_gemini(prompt, api_key):
    from google import genai  # imported here so the app works without the package
    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    response = client.models.generate_content(model=model, contents=prompt)
    text = (response.text or "").strip()
    if not text:
        raise ValueError("Gemini returned an empty answer")
    return text


def _offline_answer(chunks, facts):
    lines = []
    if facts:
        lines.append("**Calculated from the data:**")
        for i, f in enumerate(facts, 1):
            lines.append(f"\n[D{i}] {f['label']}\n\n{f['text']}")
    if chunks:
        lines.append("\n**Relevant project documentation:**")
        for i, c in enumerate(chunks[:2], 1):
            lines.append(f"\n[S{i}] ({c['source']} > {c['heading']})\n\n{c['text']}")
    return "\n".join(lines)


def ask(question, df, retriever, api_key=None):
    question = (question or "").strip()
    if not question:
        return {"answer": "Please type a question.", "sources": [], "mode": "empty", "note": None}

    on_topic = _about_project(question)
    facts = analytics.get_facts(question, df) if (on_topic and analytics.wants_numbers(question)) else []
    hits = retriever.search(question, k=TOP_K) if on_topic else []
    chunks = [h for h in hits if h["score"] >= retriever.min_score]

    if not chunks and not facts:
        return {
            "answer": ("I could not find this in the project documents or in the dataset metrics, "
                       "so I will not guess. Try asking about flow-state, productivity score, "
                       "cognitive load, interruptions, or data quality."),
            "sources": [], "mode": "no_evidence", "note": None,
        }

    sources = [{"label": f"S{i}", "kind": "document", "name": f"{c['source']} > {c['heading']}",
                "score": c["score"]} for i, c in enumerate(chunks, 1)]
    sources += [{"label": f"D{i}", "kind": "calculation", "name": f["source"], "score": None}
                for i, f in enumerate(facts, 1)]

    key = get_api_key(api_key)
    note = None
    if key:
        try:
            answer = _call_gemini(_build_prompt(question, chunks, facts), key)
            return {"answer": answer, "sources": sources, "mode": "gemini", "note": None}
        except Exception as err:  # network, quota, wrong model name, bad key ...
            msg = str(err).replace(key, "***")[:200]
            note = f"Gemini was not available ({type(err).__name__}: {msg}). Showing evidence directly."
    else:
        note = "No Gemini API key found, so evidence is shown directly (offline mode)."

    return {"answer": _offline_answer(chunks, facts), "sources": sources, "mode": "offline", "note": note}
