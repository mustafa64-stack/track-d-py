"""Learner loop for Learnova: BKT per topic, saved history, adaptive selection, report."""
import json
import math
import os
import time
from dataclasses import asdict, is_dataclass

from bkt import update_bkt

STATE_DIR = "learner_data"
INIT_MASTERY = 0.3
TARGET = 0.8   # topics above this count as learned
WEAK = 0.6     # topics below this go in the weak-topic report


def _q(question):
    return asdict(question) if is_dataclass(question) else dict(question)


def new_state(student_id):
    return {"student_id": student_id, "mastery": {}, "answers": [],
            "seen_questions": [], "diagnostic_done": False}


def _path(student_id):
    return os.path.join(STATE_DIR, f"{student_id}.json")


def load_state(student_id):
    if os.path.exists(_path(student_id)):
        with open(_path(student_id), encoding="utf-8") as f:
            return json.load(f)
    return new_state(student_id)


def save_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(_path(state["student_id"]), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_mastery(state, topic_id):
    return state["mastery"].get(topic_id, INIT_MASTERY)


def is_correct(question, selected):
    q = _q(question)
    answer, sel = str(q.get("answer", "")).strip(), str(selected).strip()
    if q.get("type") == "numerical":
        try:
            return math.isclose(float(sel), float(answer), rel_tol=1e-2, abs_tol=1e-6)
        except ValueError:
            return False
    return sel.lower() == answer.lower()


def record_answer(state, question, selected, correct=None):
    """Update mastery for the question's topic and log the answer. Call save_state() after."""
    q = _q(question)
    if correct is None:
        correct = is_correct(q, selected)
    topic = q["topic_id"]
    before = get_mastery(state, topic)
    after = update_bkt(before, correct)
    state["mastery"][topic] = after
    qid = q.get("question_id") or q.get("id")
    if qid not in state["seen_questions"]:
        state["seen_questions"].append(qid)
    state["answers"].append({
        "time": time.time(), "question_id": qid, "topic_id": topic,
        "stem": q.get("stem"), "selected": str(selected), "answer": q.get("answer"),
        "correct": bool(correct), "difficulty": q.get("difficulty"),
        "source_ref": q.get("source_ref"),
        "mastery_before": before, "mastery_after": after,
    })
    return {"correct": bool(correct), "explanation": q.get("explanation"),
            "source_ref": q.get("source_ref"),
            "mastery_before": before, "mastery_after": after}


def difficulty_for(mastery):
    return "easy" if mastery < 0.4 else "medium" if mastery < 0.7 else "hard"


def next_topics(state, topic_ids, k=3):
    unassessed = [t for t in topic_ids if t not in state["mastery"]]
    weak = sorted([t for t in topic_ids
                   if t in state["mastery"] and state["mastery"][t] < TARGET],
                  key=lambda t: state["mastery"][t])
    picks = (unassessed + weak)[:k]
    return picks or sorted(topic_ids, key=lambda t: get_mastery(state, t))[:k]


def diagnostic_plan(topic_ids, per_topic=2):
    """(topic_id, difficulty) pairs; generate one question for each with your pipeline."""
    levels = ["easy", "medium"]
    return [(t, levels[i % 2]) for t in topic_ids for i in range(per_topic)]


def load_topic_ids(path="topic_tree.json", main_only=True):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    topics = data.get("topics", data) if isinstance(data, dict) else data
    ids = []
    for t in topics:
        if not isinstance(t, dict):
            continue
        tid = t.get("topic_id") or t.get("id")
        if tid is None or (main_only and t.get("parent_id")):
            continue
        ids.append(tid)
    return ids or (load_topic_ids(path, False) if main_only else [])


def build_report(state, names=None):
    names = names or {}
    per = {}
    for a in state["answers"]:
        d = per.setdefault(a["topic_id"], {"n": 0, "ok": 0})
        d["n"] += 1
        d["ok"] += int(a["correct"])
    topics = sorted(
        ({"topic_id": t, "name": names.get(t, t), "mastery": round(get_mastery(state, t), 2),
          "accuracy": round(d["ok"] / d["n"], 2), "attempts": d["n"]} for t, d in per.items()),
        key=lambda x: x["mastery"])
    misconceptions = [{"topic_id": a["topic_id"], "question": a["stem"],
                       "chose": a["selected"], "correct_answer": a["answer"],
                       "source": a["source_ref"]}
                      for a in state["answers"] if not a["correct"]]
    return {"topics": topics,
            "weak_topics": [t for t in topics if t["mastery"] < WEAK],
            "misconceptions": misconceptions[-10:]}