import csv
import random
from statistics import mean

from learner_loop import (INIT_MASTERY, difficulty_for, get_mastery, load_topic_ids,
                          new_state, next_topics, record_answer)

random.seed(7)
try:
    TOPICS = load_topic_ids()[:6]
except Exception:
    TOPICS = [f"t{i}" for i in range(1, 7)]
DIFFS = ["easy", "medium", "hard"]
POOL = {t: [{"question_id": f"{t}-q{i}", "type": "mcq", "stem": "sim", "options": ["A", "B"],
             "answer": "A", "topic_id": t, "difficulty": DIFFS[i % 3], "source_ref": "sim"}
            for i in range(12)] for t in TOPICS}
PROFILES = {"weak": 0.25, "average": 0.5, "strong": 0.75}
SESSIONS, QS = 5, 10


def run(name, base):
    hidden = {t: min(0.95, max(0.05, base + random.uniform(-0.15, 0.15))) for t in TOPICS}
    state, asked, repeats, rows = new_state(name), 0, 0, []
    for s in range(1, SESSIONS + 1):
        for _ in range(QS):
            t = random.choice(next_topics(state, TOPICS, k=3))
            diff = difficulty_for(get_mastery(state, t))
            seen = set(state["seen_questions"])
            unseen = [q for q in POOL[t] if q["question_id"] not in seen]
            cands = [q for q in unseen if q["difficulty"] == diff] or unseen or POOL[t]
            q = random.choice(cands)
            asked += 1
            repeats += q["question_id"] in seen
            correct = random.random() < hidden[t]
            record_answer(state, q, "A" if correct else "B")
            hidden[t] = min(0.95, hidden[t] + 0.04)   # simulated learning from practice
        rows.append({"profile": name, "session": s,
                     "mean_mastery": round(mean(get_mastery(state, t) for t in TOPICS), 3),
                     "mean_true_knowledge": round(mean(hidden.values()), 3),
                     "repetition_rate": round(repeats / asked, 3)})
    return rows


all_rows = [r for n, b in PROFILES.items() for r in run(n, b)]
with open("simulation_results.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=all_rows[0].keys())
    w.writeheader()
    w.writerows(all_rows)

for n in PROFILES:
    r = [x for x in all_rows if x["profile"] == n]
    print(f"{n}: mastery {INIT_MASTERY} -> {r[-1]['mean_mastery']} "
          f"(gain {r[-1]['mean_mastery'] - INIT_MASTERY:+.2f}), "
          f"repetition rate {r[-1]['repetition_rate']}")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for n in PROFILES:
        r = [x for x in all_rows if x["profile"] == n]
        plt.plot([x["session"] for x in r], [x["mean_mastery"] for x in r], marker="o", label=n)
    plt.xlabel("Session"); plt.ylabel("Mean estimated mastery"); plt.legend()
    plt.title("Simulated learners: mastery over 5 sessions")
    plt.savefig("simulation_chart.png", dpi=150)
except ImportError:
    print("matplotlib missing: CSV written, chart skipped")