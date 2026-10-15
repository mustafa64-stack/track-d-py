import json
import unittest
from unittest.mock import patch, MagicMock

from question_generator import generate_questions


class TestQuestionGenerator(unittest.TestCase):

    @patch("question_generator.client.models.generate_content")
    def test_generates_questions_from_response(self, mock_generate):
        question = {
            "id": "test_q1",
            "type": "MCQ",
            "stem": "What does the dot product produce?",
            "options": [
                "A scalar",
                "A vector",
                "A matrix",
                "Nothing",
            ],
            "answer": "A scalar",
            "explanation": "The dot product produces a scalar.",
            "topic_id": "vectors_and_scalars",
            "source_ref": "sample_vectors_passage",
            "difficulty": "easy",
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps([question])
        mock_generate.return_value = mock_response

        questions = generate_questions(
            context="The dot product of two vectors produces a scalar.",
            topic="Vectors and Scalars",
            topic_id="vectors_and_scalars",
            question_type="MCQ",
            difficulty="easy",
            count=1,
        )

        self.assertEqual(len(questions), 1)
        self.assertTrue(questions[0]["id"])
        self.assertEqual(
            questions[0]["source_ref"],
            "sample_vectors_passage",
        )


if __name__ == "__main__":
    unittest.main()