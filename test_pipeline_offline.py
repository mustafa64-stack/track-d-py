import unittest
from unittest.mock import patch

from assessment_pipeline import run_assessment_pipeline
from question_deduplicator import generate_question_hash


SAMPLE_CONTEXT = """
A vector has both magnitude and direction.
A scalar has magnitude but no direction.
The dot product of two vectors produces a scalar.
"""


def fake_embed(texts):
    # Offline stand-in for the Gemini embedding call.
    return [[1.0, 0.0] for _ in texts]


def make_question(stem, answer="A scalar"):
    return {
        "id": stem,
        "type": "MCQ",
        "stem": stem,
        "options": [
            "A scalar",
            "A vector",
            "Both",
            "Neither",
        ],
        "answer": answer,
        "explanation": "Supported by the sample material.",
        "topic_id": "vectors_and_scalars",
        "source_ref": "sample_source",
        "difficulty": "easy",
        "verified": False,
        "hash": "",
        "embedding": None,
    }


def make_verification(correct=True, supported=True, answer="A scalar"):
    return {
        "correct": correct,
        "expected_answer": answer,
        "proposed_answer": "A scalar",
        "explanation": "Mock verification result.",
        "source_supported": supported,
    }


class TestOfflinePipeline(unittest.TestCase):

    @patch("assessment_pipeline.verify_question")
    @patch("assessment_pipeline.generate_questions")
    def test_accepts_verified_question(
        self, mock_generate, mock_verify
    ):
        question = make_question("What does the dot product produce?")
        mock_generate.return_value = [question]
        mock_verify.return_value = make_verification()

        result = run_assessment_pipeline(
            context=SAMPLE_CONTEXT,
            topic="Vectors",
            topic_id="vectors_and_scalars",
            source_ref="sample_source",
            count=1,
            embed_fn=fake_embed,
        )

        self.assertEqual(len(result["questions"]), 1)
        self.assertEqual(len(result["rejected"]), 0)
        self.assertTrue(result["questions"][0]["verified"])
        self.assertTrue(result["questions"][0]["hash"])

    @patch("assessment_pipeline.verify_question")
    @patch("assessment_pipeline.generate_questions")
    def test_rejects_incorrect_answer(
        self, mock_generate, mock_verify
    ):
        question = make_question("What does the dot product produce?")
        mock_generate.return_value = [question]
        mock_verify.return_value = make_verification(
            correct=False
        )

        result = run_assessment_pipeline(
            context=SAMPLE_CONTEXT,
            topic="Vectors",
            topic_id="vectors_and_scalars",
            source_ref="sample_source",
            count=1,
            max_attempts=1,
            embed_fn=fake_embed,
        )

        self.assertEqual(len(result["questions"]), 0)
        self.assertEqual(len(result["rejected"]), 1)

    @patch("assessment_pipeline.verify_question")
    @patch("assessment_pipeline.generate_questions")
    def test_rejects_unsupported_question(
        self, mock_generate, mock_verify
    ):
        question = make_question("What does the dot product produce?")
        mock_generate.return_value = [question]
        mock_verify.return_value = make_verification(
            supported=False
        )

        result = run_assessment_pipeline(
            context=SAMPLE_CONTEXT,
            topic="Vectors",
            topic_id="vectors_and_scalars",
            source_ref="sample_source",
            count=1,
            max_attempts=1,
            embed_fn=fake_embed,
        )

        self.assertEqual(len(result["questions"]), 0)
        self.assertEqual(len(result["rejected"]), 1)

    @patch("assessment_pipeline.verify_question")
    @patch("assessment_pipeline.generate_questions")
    def test_removes_duplicate_questions(
        self, mock_generate, mock_verify
    ):
        first = make_question("What does the dot product produce?")
        second = make_question(
            "WHAT DOES THE DOT PRODUCT PRODUCE?"
        )

        mock_generate.return_value = [first, second]
        mock_verify.return_value = make_verification()

        result = run_assessment_pipeline(
            context=SAMPLE_CONTEXT,
            topic="Vectors",
            topic_id="vectors_and_scalars",
            source_ref="sample_source",
            count=2,
            max_attempts=1,
            embed_fn=fake_embed,
        )

        self.assertEqual(len(result["questions"]), 1)
        self.assertEqual(len(result["rejected"]), 1)
        self.assertEqual(
            result["rejected"][0]["rejection_reason"],
            "Duplicate question detected.",
        )

    @patch("assessment_pipeline.verify_question")
    @patch("assessment_pipeline.generate_questions")
    def test_retries_until_a_question_passes(
        self, mock_generate, mock_verify
    ):
        bad = make_question("A question that fails verification?")
        good = make_question("A question that passes verification?")

        mock_generate.side_effect = [[bad], [good]]
        mock_verify.side_effect = [
            make_verification(correct=False),
            make_verification(),
        ]

        result = run_assessment_pipeline(
            context=SAMPLE_CONTEXT,
            topic="Vectors",
            topic_id="vectors_and_scalars",
            source_ref="sample_source",
            count=1,
            max_attempts=3,
            embed_fn=fake_embed,
        )

        self.assertEqual(result["stats"]["attempts"], 2)
        self.assertEqual(len(result["questions"]), 1)
        self.assertEqual(len(result["rejected"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)