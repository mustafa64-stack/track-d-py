import os
import sys
import random
from pathlib import Path
from datetime import datetime
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from study_data import init_session_state, AVAILABLE_TOPICS, QUESTION_BANK
from gemini_helper import generate_quiz_questions

try:
    from retrieval_engine import get_all_topics, get_chunks_for_topic, retrieve_chunks
    from learner_loop import load_state, save_state, record_answer, get_mastery, difficulty_for
    from question_generator import generate_questions
    from question_verifier import verify_question
    HAS_MEMBER_B = True
except Exception as e:
    HAS_MEMBER_B = False
    print("Member B import warning:", e)

st.set_page_config(
    page_title="Adaptive Practice Quiz | StudyX",
    page_icon="📝",
    layout="wide"
)

init_session_state()

student_name = st.session_state.get("student_name", "Student").strip() or "Student"
learner_state = load_state(student_name) if HAS_MEMBER_B else {}

# Session state defaults
defaults = {
    "quiz_questions": [],
    "quiz_submitted": False,
    "quiz_answers": {},
    "quiz_topic": "",
    "quiz_topic_id": "",
    "quiz_difficulty": "Easy",
    "bkt_results": []
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def get_fallback_questions(topic, count):
    """Get predefined questions without using an AI API."""
    bank = QUESTION_BANK.get(topic, [])
    if not bank:
        # Generic optics fallback
        return [
            {
                "question": "What does Snell's Law govern in wave optics?",
                "options": ["Refraction at an interface", "Blackbody radiation", "Photoelectric effect", "Compton scattering"],
                "answer": "Refraction at an interface",
                "explanation": "Snell's Law describes the relationship between angles of incidence and refraction.",
                "topic_id": "reflection_and_refraction"
            },
            {
                "question": "At what condition does Total Internal Reflection occur?",
                "options": ["Angle of incidence > critical angle", "Angle of incidence < critical angle", "Only in vacuum", "When light travels into a denser medium"],
                "answer": "Angle of incidence > critical angle",
                "explanation": "When traveling from a denser to rarer medium, TIR occurs when theta_i > theta_c.",
                "topic_id": "total_internal_reflection"
            }
        ][:count]

    questions = []
    for item in bank:
        if not isinstance(item, dict):
            continue
        q_text = item.get("question")
        options = item.get("options")
        answer = item.get("answer", item.get("correct_answer"))
        explanation = item.get("explanation", "")
        if not q_text or not isinstance(options, list) or len(options) != 4:
            continue
        if answer not in options:
            continue
        questions.append({
            "question": q_text,
            "options": options,
            "answer": answer,
            "explanation": explanation,
            "topic_id": topic.lower().replace(" ", "_")
        })

    random.shuffle(questions)
    return questions[:count]


# Load topics from Supabase if available
registered_topics = []
topic_name_to_id = {}

if HAS_MEMBER_B:
    try:
        db_topics = get_all_topics()
        for t in db_topics:
            tid = t.get("id")
            name = t.get("name", tid)
            registered_topics.append(name)
            topic_name_to_id[name] = tid
    except Exception:
        pass

combined_topics = registered_topics if registered_topics else AVAILABLE_TOPICS

st.title("📝 Source-Grounded Adaptive Quiz")
st.caption("AI-generated questions verified against course material with Bayesian Knowledge Tracing (BKT) student modeling.")

c1, c2, c3 = st.columns([2, 1, 1])

with c1:
    selected_topic_name = st.selectbox("Select Concept / Topic", combined_topics)
    selected_topic_id = topic_name_to_id.get(selected_topic_name, selected_topic_name.lower().replace(" ", "_"))

# Check student's current BKT mastery
current_mastery = get_mastery(learner_state, selected_topic_id) if HAS_MEMBER_B else 0.3
recommended_diff = difficulty_for(current_mastery).capitalize() if HAS_MEMBER_B else "Easy"

with c2:
    selected_diff = st.selectbox(
        "Difficulty",
        ["Easy", "Medium", "Hard"],
        index=["Easy", "Medium", "Hard"].index(recommended_diff) if recommended_diff in ["Easy", "Medium", "Hard"] else 0
    )

with c3:
    num_questions = st.number_input("Question Count", min_value=1, max_value=10, value=3, step=1)

# Display current mastery banner
if HAS_MEMBER_B:
    st.info(f"Student: **{student_name}** • Current BKT Mastery on *{selected_topic_name}*: **{current_mastery*100:.1f}%** (Recommended difficulty: **{recommended_diff}**)")

def is_substantive_chunk(c):
    """Filters out Table of Contents, indices, and frontmatter chunks."""
    text = c.get("text", "")
    page = c.get("page")
    if c.get("modality") == "pdf" and page is not None and int(page) <= 10:
        return False
    if "CONTENTS" in text or "Table of Contents" in text or ". . . ." in text or "......" in text:
        return False
    if len(text.strip()) < 50:
        return False
    return True

if st.button("🚀 Generate Adaptive Quiz", type="primary"):
    questions = []
    used_fallback = False

    with st.spinner("Generating source-grounded questions with two-step LLM verification..."):
        # 1. Attempt generation from Supabase chunks for this topic
        context_chunks = []
        if HAS_MEMBER_B:
            try:
                chunks = get_chunks_for_topic(selected_topic_id, limit=5)
                if not chunks:
                    chunks = retrieve_chunks(selected_topic_name, match_count=6, threshold=0.1)
                
                clean_chunks = [c for c in chunks if is_substantive_chunk(c)]
                context_chunks = [c.get("text", "") for c in clean_chunks if c.get("text")]
            except Exception as e:
                print("Error retrieving chunks for quiz:", e)

        # 2. Or from session uploaded materials
        if not context_chunks:
            for mat in st.session_state.get("uploaded_materials", []):
                t = mat.get("extracted_text", "")
                if t and "CONTENTS" not in t and ". . ." not in t:
                    context_chunks.append(t)

        study_text = "\n\n".join(context_chunks)

        if study_text:
            try:
                # Use Member B's generator
                raw_qs = generate_questions(
                    context=study_text[:8000],
                    topic=selected_topic_name,
                    topic_id=selected_topic_id,
                    question_type="MCQ",
                    difficulty=selected_diff.lower(),
                    count=int(num_questions)
                )
                bad_phrases = [
                    "which section", "what is the title", "which appendix", "table of contents",
                    "according to the contents", "chapter 13", "section 13", "title of section",
                    "listed under chapter", "follows the stefan-boltzmann"
                ]
                for q in raw_qs:
                    stem_lower = q.get("stem", "").lower()
                    if any(bp in stem_lower for bp in bad_phrases):
                        continue
                    questions.append({
                        "question": q["stem"],
                        "options": q["options"],
                        "answer": q["answer"],
                        "explanation": q.get("explanation", ""),
                        "topic_id": selected_topic_id,
                        "source_ref": q.get("source_ref", "")
                    })
            except Exception as gen_err:
                print("Generation error:", gen_err)
                try:
                    # Fallback to gemini_helper quiz generator
                    raw_qs = generate_quiz_questions(
                        topic=selected_topic_name,
                        study_material=study_text,
                        num_questions=int(num_questions),
                        difficulty=selected_diff
                    )
                    for q in raw_qs:
                        q["topic_id"] = selected_topic_id
                    questions = raw_qs
                except Exception as fb_err:
                    print("Gemini helper error:", fb_err)
                    used_fallback = True

        # If questions are fewer than requested due to filtering, top-up with curated bank
        if len(questions) < int(num_questions):
            needed = int(num_questions) - len(questions)
            fallback_qs = get_fallback_questions(selected_topic_name, needed)
            existing_stems = {q["question"] for q in questions}
            for fb in fallback_qs:
                if fb["question"] not in existing_stems:
                    questions.append(fb)
            used_fallback = True

    if questions:
        st.session_state["quiz_questions"] = questions
        st.session_state["quiz_topic"] = selected_topic_name
        st.session_state["quiz_topic_id"] = selected_topic_id
        st.session_state["quiz_difficulty"] = selected_diff
        st.session_state["quiz_submitted"] = False
        st.session_state["quiz_answers"] = {}
        st.session_state["quiz_results_data"] = None

        if used_fallback:
            st.warning("Generated from fallback practice material.")
        else:
            st.success("✅ AI-verified questions generated directly from course excerpts!")
    else:
        st.error("Could not generate questions for this topic.")

questions = st.session_state.get("quiz_questions", [])

if questions:
    st.divider()
    st.subheader(f"Quiz: {st.session_state.get('quiz_topic', selected_topic_name)}")
    st.caption(f"Difficulty: {st.session_state.get('quiz_difficulty', selected_diff)} • Total Questions: {len(questions)}")

    with st.form("quiz_form"):
        user_answers = {}
        for index, question in enumerate(questions):
            q_text = question.get("question", "")
            st.markdown(f"""
            <div style="background: var(--secondary-background-color); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 12px; padding: 16px 20px; margin-top: 14px; margin-bottom: 8px;">
                <span style="font-size: 0.8rem; font-weight: 700; color: #818cf8; text-transform: uppercase; letter-spacing: 0.05em;">Question {index + 1} of {len(questions)}</span>
                <div style="font-size: 1.05rem; font-weight: 600; color: var(--text-color); margin-top: 6px;">{q_text}</div>
            </div>
            """, unsafe_allow_html=True)
            options = question.get("options", [])
            user_answers[index] = st.radio(
                f"Select answer for Question {index + 1}:",
                options,
                key=f"q_{index}",
                index=None
            )
            st.write("")
        submitted = st.form_submit_button("Submit Assessment & Update Mastery", type="primary", use_container_width=True)

    if submitted:
        st.session_state["quiz_answers"] = user_answers
        score = 0
        total = len(questions)
        weak_concepts = []
        detailed_results = []

        for index, question in enumerate(questions):
            correct_answer = question.get("answer", "")
            user_answer = user_answers.get(index)
            is_correct = bool(
                user_answer and str(user_answer).strip().casefold() == str(correct_answer).strip().casefold()
            )
            if is_correct:
                score += 1
            else:
                weak_concepts.append(st.session_state.get("quiz_topic", "Concept"))

            bkt_info = None
            if HAS_MEMBER_B:
                bkt_res = record_answer(
                    state=learner_state,
                    question={
                        "topic_id": question.get("topic_id", selected_topic_id),
                        "stem": question.get("question"),
                        "answer": correct_answer,
                        "difficulty": st.session_state.get("quiz_difficulty", "easy").lower(),
                        "source_ref": question.get("source_ref", "")
                    },
                    selected=user_answer or "",
                    correct=is_correct
                )
                bkt_info = bkt_res

            detailed_results.append({
                "question": question.get("question"),
                "options": question.get("options", []),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question.get("explanation", ""),
                "bkt_info": bkt_info
            })

        if HAS_MEMBER_B:
            save_state(learner_state)

        percentage = (score / total * 100) if total else 0
        if "quiz_history" not in st.session_state:
            st.session_state["quiz_history"] = []

        st.session_state["quiz_history"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "topic": st.session_state.get("quiz_topic", "General"),
            "score": score,
            "total": total,
            "percentage": round(percentage),
            "difficulty": st.session_state.get("quiz_difficulty", "Medium"),
            "weak_concepts": list(set(weak_concepts))
        })

        st.session_state["quiz_results_data"] = {
            "score": score,
            "total": total,
            "percentage": percentage,
            "detailed_results": detailed_results,
            "topic_mastery": get_mastery(learner_state, selected_topic_id) if HAS_MEMBER_B else percentage / 100
        }
        st.session_state["quiz_submitted"] = True

    if st.session_state.get("quiz_submitted") and st.session_state.get("quiz_results_data"):
        res = st.session_state["quiz_results_data"]
        score = res["score"]
        total = res["total"]
        percentage = res["percentage"]

        st.divider()
        st.header("📊 Results & Cognitive Knowledge Tracing")

        for index, item in enumerate(res["detailed_results"]):
            st.markdown(f"**Question {index + 1}**")
            st.write(item["question"])
            if item["is_correct"]:
                st.success(f"✅ Correct! You selected: {item['user_answer']}")
            else:
                st.error(f"❌ Incorrect. Your choice: {item['user_answer'] or 'No answer'}")
                st.info(f"Correct answer: **{item['correct_answer']}**")

            if item.get("explanation"):
                st.caption(f"💡 **Explanation:** {item['explanation']}")

            if item.get("bkt_info"):
                u = item["bkt_info"]
                gain = u['mastery_after'] - u['mastery_before']
                st.caption(f"📈 **BKT Mastery Update:** {u['mastery_before']*100:.1f}% ➔ **{u['mastery_after']*100:.1f}%** ({gain*100:+.1f}%)")

            st.divider()

        st.subheader("🏆 Assessment Score")
        col1, col2, col3 = st.columns(3)
        col1.metric("Score", f"{score} / {total}")
        col2.metric("Accuracy", f"{percentage:.1f}%")
        col3.metric("Topic Mastery (BKT)", f"{res['topic_mastery']*100:.1f}%")

        st.progress(percentage / 100)

        if st.button("🔄 Take Another Quiz"):
            st.session_state["quiz_submitted"] = False
            st.session_state["quiz_answers"] = {}
            st.session_state["quiz_results_data"] = None
            st.rerun()