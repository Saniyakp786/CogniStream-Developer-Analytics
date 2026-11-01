import unittest
from unittest.mock import patch
from rag.assistant import ask


class FakeRetriever:
    min_score = 0.5

    def search(self, question, k=4):
        return [
            {
                "source": "project_overview.md",
                "heading": "Productivity",
                "text": "CogniStream analyzes developer productivity and focus.",
                "score": 0.9
            }
        ]


class TestAssistant(unittest.TestCase):

    def test_empty_question(self):
        result = ask("", None, FakeRetriever())

        self.assertEqual(result["mode"], "empty")
        self.assertEqual(result["sources"], [])
        self.assertIn("Please type a question", result["answer"])

    def test_unrelated_question(self):
        result = ask("What is the capital of India?", None, FakeRetriever())

        self.assertEqual(result["mode"], "no_evidence")
        self.assertEqual(result["sources"], [])

    def test_no_evidence(self):
        class EmptyRetriever:
            min_score = 0.5

            def search(self, question, k=4):
                return []

        with patch("rag.assistant.analytics.wants_numbers", return_value=False):
            result = ask("Tell me about developer productivity", None, EmptyRetriever())

        self.assertEqual(result["mode"], "no_evidence")

    def test_offline_answer(self):
        with patch("rag.assistant.get_api_key", return_value=None):
            with patch("rag.assistant.analytics.wants_numbers", return_value=False):
                result = ask("Explain developer productivity", None, FakeRetriever())

        self.assertEqual(result["mode"], "offline")
        self.assertIn("Relevant project documentation", result["answer"])


if __name__ == "__main__":
    unittest.main()