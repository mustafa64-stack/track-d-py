
import unittest

from question_deduplicator import (
    generate_question_hash,
    deduplicate_questions,
)


class TestQuestionDeduplicator(unittest.TestCase):

    def test_same_question_has_same_hash(self):
        q1 = {
            "id": "one",
            "type": "MCQ",
            "stem": "What does the dot product produce?",
        }

        q2 = {
            "id": "two",
            "type": "MCQ",
            "stem": "  WHAT DOES THE DOT PRODUCT PRODUCE?  ",
        }

        self.assertEqual(
            generate_question_hash(q1),
            generate_question_hash(q2),
        )

    def test_different_questions_have_different_hashes(self):
        q1 = {
            "type": "MCQ",
            "stem": "What does the dot product produce?",
        }

        q2 = {
            "type": "MCQ",
            "stem": "What does the cross product produce?",
        }

        self.assertNotEqual(
            generate_question_hash(q1),
            generate_question_hash(q2),
        )

    def test_duplicates_are_removed(self):
        questions = [
            {
                "id": "one",
                "type": "MCQ",
                "stem": "What does the dot product produce?",
            },
            {
                "id": "two",
                "type": "MCQ",
                "stem": "WHAT DOES THE DOT PRODUCT PRODUCE?",
            },
            {
                "id": "three",
                "type": "MCQ",
                "stem": "What does the cross product produce?",
            },
        ]

        unique, duplicates = deduplicate_questions(questions)

        self.assertEqual(len(unique), 2)
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]["id"], "two")

    def test_existing_hashes_are_respected(self):
        question = {
            "id": "new",
            "type": "MCQ",
            "stem": "What does the dot product produce?",
        }

        existing = {generate_question_hash(question)}

        unique, duplicates = deduplicate_questions(
            [question],
            existing_hashes=existing,
        )

        self.assertEqual(len(unique), 0)
        self.assertEqual(len(duplicates), 1)

    def test_empty_stem_is_rejected(self):
        with self.assertRaises(ValueError):
            generate_question_hash({
                "type": "MCQ",
                "stem": "   ",
            })


if __name__ == "__main__":
    unittest.main()
