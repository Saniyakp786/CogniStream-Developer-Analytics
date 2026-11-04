import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from rag import retriever


class TestIndexPersistence(unittest.TestCase):

    def setUp(self):
        self.chunks = [
            {
                "id": 0,
                "source": "docs/project.md",
                "heading": "Overview",
                "text": "CogniStream analyzes developer productivity."
            }
        ]

        self.vectors = np.array(
            [[0.5, 0.8, 0.2]],
            dtype="float32"
        )

        self.fake_retriever = SimpleNamespace(
            chunks=self.chunks,
            backend_name="tfidf",
            vectors=self.vectors
        )

    def test_save_index_creates_required_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(retriever, "INDEX_DIR", Path(temp_dir)):
                retriever.save_index(self.fake_retriever)

                self.assertTrue((Path(temp_dir) / "chunks.json").exists())
                self.assertTrue((Path(temp_dir) / "meta.json").exists())
                self.assertTrue((Path(temp_dir) / "vectors.npy").exists())

    def test_saved_chunks_match_original_chunks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(retriever, "INDEX_DIR", Path(temp_dir)):
                retriever.save_index(self.fake_retriever)

                saved_chunks = json.loads(
                    (Path(temp_dir) / "chunks.json").read_text(
                        encoding="utf-8"
                    )
                )

                self.assertEqual(saved_chunks, self.chunks)

    def test_saved_metadata_contains_backend_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(retriever, "INDEX_DIR", Path(temp_dir)):
                retriever.save_index(self.fake_retriever)

                metadata = json.loads(
                    (Path(temp_dir) / "meta.json").read_text(
                        encoding="utf-8"
                    )
                )

                self.assertEqual(metadata["backend"], "tfidf")

    def test_saved_vectors_match_original_vectors(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(retriever, "INDEX_DIR", Path(temp_dir)):
                retriever.save_index(self.fake_retriever)

                saved_vectors = np.load(
                    Path(temp_dir) / "vectors.npy"
                )

                np.testing.assert_array_equal(
                    saved_vectors,
                    self.vectors
                )


if __name__ == "__main__":
    unittest.main()