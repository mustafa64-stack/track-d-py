import unittest
from unittest.mock import patch

from assessment_pipeline import run_assessment_pipeline


class TestAssessmentPipeline(unittest.TestCase):

    @patch("assessment_pipeline.verify_question")
    @patch("assessment_pipeline.generate_questions")
    def test_pipeline_accepts_verified_question(
        self, mock_generate, mock_verify
    ):
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

        mock_generate.return_value = [question]

        mock_verify.return_value = {
            **question,
            "verified": True,
            "correct": True,
            "source_supported": True,
            "expected_answer": "A scalar",
            "proposed_answer": "A scalar",
        }

        result = run_assessment_pipeline(
            context="The dot product of two vectors produces a scalar.",
            topic="Vectors and Scalars",
            topic_id="vectors_and_scalars",
            source_ref="sample_vectors_passage",
            question_type="MCQ",
            difficulty="easy",
            count=1,
        )

        self.assertEqual(len(result["questions"]), 1)
        self.assertTrue(result["questions"][0]["verified"])


if __name__ == "__main__":
    unittest.main()