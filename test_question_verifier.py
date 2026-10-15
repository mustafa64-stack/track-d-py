import json
import unittest
from unittest.mock import patch, MagicMock

from question_verifier import verify_question


class TestQuestionVerifier(unittest.TestCase):

    @patch("question_verifier.client.models.generate_content")
    def test_verifier_uses_model_response(self, mock_generate):
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "proposed_answer": "A scalar",
            "correct": True,
            "explanation": "The dot product produces a scalar.",
            "expected_answer": "A scalar",
            "source_supported": True,
        })
        mock_generate.return_value = mock_response

        question = {
            "id": "test_q1",
            "type": "MCQ",
            "stem": "What does the dot product produce?",
            "options": ["A scalar", "A vector", "A matrix", "Nothing"],
            "answer": "A scalar",
            "explanation": "The dot product produces a scalar.",
            "topic_id": "vectors_and_scalars",
            "source_ref": "sample_vectors_passage",
            "difficulty": "easy",
        }

        result = verify_question(
            question=question,
            context="The dot product of two vectors produces a scalar.",
            source_ref="sample_vectors_passage",
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("verified", result.get("correct", False)))


if __name__ == "__main__":
    unittest.main()