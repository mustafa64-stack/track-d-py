import tempfile
import unittest

import learner_loop as ll

Q = {"question_id": "q1", "type": "mcq", "stem": "s", "options": ["A", "B"], "answer": "A",
     "explanation": "e", "topic_id": "t1", "source_ref": "p.3", "difficulty": "easy"}


class TestLearnerLoop(unittest.TestCase):
    def setUp(self):
        ll.STATE_DIR = tempfile.mkdtemp()

    def test_correct_raises_wrong_lowers(self):
        up = ll.record_answer(ll.new_state("a"), Q, "A")
        down = ll.record_answer(ll.new_state("b"), Q, "B")
        self.assertGreater(up["mastery_after"], ll.INIT_MASTERY)
        self.assertLess(down["mastery_after"], ll.INIT_MASTERY)

    def test_mastery_is_per_topic(self):
        s = ll.new_state("a")
        ll.record_answer(s, Q, "A")
        self.assertNotIn("t2", s["mastery"])

    def test_persistence(self):
        s = ll.new_state("a")
        ll.record_answer(s, Q, "A")
        ll.save_state(s)
        self.assertEqual(ll.load_state("a")["mastery"], s["mastery"])

    def test_numeric_check(self):
        n = dict(Q, type="numerical", answer="3.14")
        self.assertTrue(ll.is_correct(n, "3.1400"))
        self.assertFalse(ll.is_correct(n, "2"))

    def test_next_topics_weakest_first(self):
        s = ll.new_state("a")
        s["mastery"] = {"t1": 0.7, "t2": 0.2, "t3": 0.5}
        self.assertEqual(ll.next_topics(s, ["t1", "t2", "t3"], k=2), ["t2", "t3"])

    def test_report_lists_weak_topic_and_misconception(self):
        s = ll.new_state("a")
        ll.record_answer(s, Q, "B")
        r = ll.build_report(s)
        self.assertEqual(r["weak_topics"][0]["topic_id"], "t1")
        self.assertEqual(r["misconceptions"][0]["chose"], "B")


if __name__ == "__main__":
    unittest.main()