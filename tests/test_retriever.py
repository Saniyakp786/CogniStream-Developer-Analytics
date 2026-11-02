
import unittest
from unittest.mock import patch
from rag import retriever


class TestRetriever(unittest.TestCase):

    def test_chunk_document_creates_chunks(self):
        text = "# Overview\nCogniStream analyzes developer productivity."

        chunks = retriever.chunk_document("test.md", text)

        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[0]["source"], "test.md")
        self.assertEqual(chunks[0]["heading"], "Overview")

    def test_empty_document_returns_no_chunks(self):
        chunks = retriever.chunk_document("empty.md", "")

        self.assertEqual(chunks, [])

    def test_long_text_is_split(self):
        text = "A" * 2000

        chunks = retriever._split_long(text)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(
            all(len(chunk) <= retriever.MAX_CHARS for chunk in chunks)
        )

    def test_build_chunks_assigns_ids(self):
        sample_docs = [
            ("docs/test.md", "# Testing\nSample document content.")
        ]

        with patch("rag.retriever.load_documents", return_value=sample_docs):
            chunks = retriever.build_chunks()

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["id"], 0)
        self.assertEqual(chunks[0]["heading"], "Testing")


if __name__ == "__main__":
    unittest.main()
