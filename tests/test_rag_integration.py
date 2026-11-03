import unittest
from unittest.mock import patch

import numpy as np

from rag.retriever import Retriever
from rag.assistant import ask


class FakeBackend:
    name = "tfidf"

    def encode(self, texts):
        return np.array([[1.0, 0.0]], dtype="float32")


class TestRAGIntegration(unittest.TestCase):

    def setUp(self):
        self.chunks = [
            {
                "id": 1,
                "source": "project_overview.md",
                "heading": "Productivity",
                "text": "CogniStream analyzes developer productivity and focus."
            }
        ]

        self.backend = FakeBackend()
        self.vectors = np.array([[0.9, 0.1]], dtype="float32")
        self.retriever = Retriever(
            self.chunks,
            self.backend,
            self.vectors
        )

    def test_retriever_search_returns_document(self):
        results = self.retriever.search("developer productivity")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "project_overview.md")
        self.assertGreater(results[0]["score"], 0)

    def test_assistant_uses_retrieved_document(self):
        with patch("rag.assistant.get_api_key", return_value=None):
            with patch(
                "rag.assistant.analytics.wants_numbers",
                return_value=False
            ):
                result = ask(
                    "Explain developer productivity",
                    None,
                    self.retriever
                )

        self.assertEqual(result["mode"], "offline")
        self.assertGreater(len(result["sources"]), 0)
        self.assertIn("Relevant project documentation", result["answer"])

    def test_assistant_filters_low_score_chunks(self):
        class LowScoreRetriever:
            min_score = 0.5

            def search(self, question, k=4):
                return [{
                    "source": "test.md",
                    "heading": "Test",
                    "text": "Low relevance content",
                    "score": 0.1
                }]

        with patch("rag.assistant.analytics.wants_numbers", return_value=False):
            result = ask(
                "Explain developer productivity",
                None,
                LowScoreRetriever()
            )

        self.assertEqual(result["mode"], "no_evidence")
        self.assertEqual(result["sources"], [])

    def test_empty_retriever_returns_no_evidence(self):
        empty_retriever = Retriever(
            [],
            self.backend,
            np.empty((0, 2), dtype="float32")
        )

        with patch("rag.assistant.analytics.wants_numbers", return_value=False):
            result = ask(
                "Explain developer productivity",
                None,
                empty_retriever
            )

        self.assertEqual(result["mode"], "no_evidence")
        self.assertEqual(result["sources"], [])


if __name__ == "__main__":
    unittest.main()