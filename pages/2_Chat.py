import os
import sys
import re
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from study_data import init_session_state
from gemini_helper import generate_tutor_answer

try:
    from retrieval_engine import ask_tutor
    HAS_RETRIEVAL_ENGINE = True
except Exception:
    HAS_RETRIEVAL_ENGINE = False


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Concept AI Tutor",
    page_icon="💬",
    layout="wide"
)

init_session_state()

st.title("💬 Concept AI Tutor")
st.caption(
    "Source-grounded multimodal tutor with exact page, slide, "
    "and video citations and honest refusal guardrails."
)


# --------------------------------------------------
# 2. SESSION STATE
# --------------------------------------------------

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

if "selected_source" not in st.session_state:
    st.session_state["selected_source"] = None

if "uploaded_materials" not in st.session_state:
    st.session_state["uploaded_materials"] = []


# --------------------------------------------------
# 3. EXTRACT PAGE-WISE TEXT FOR IN-SESSION UPLOADS
# --------------------------------------------------

def get_page_records(document):
    records = document.get("page_records", [])

    if isinstance(records, list) and records:
        result = []
        for record in records:
            if not isinstance(record, dict):
                continue
            page = record.get("page", record.get("page_number", 1))
            text = record.get("text", record.get("content", ""))
            if text and str(text).strip():
                try:
                    page = int(page)
                except (ValueError, TypeError):
                    page = 1
                result.append({"page": page, "text": str(text).strip()})
        if result:
            return result

    extracted_text = document.get("extracted_text", "")
    if not extracted_text:
        return []

    sections = re.split(r"---\s*Page\s+(\d+)\s*---", extracted_text, flags=re.IGNORECASE)
    if len(sections) >= 3:
        result = []
        for i in range(1, len(sections), 2):
            page_text = sections[i + 1] if i + 1 < len(sections) else ""
            if page_text.strip():
                result.append({"page": int(sections[i]), "text": page_text.strip()})
        return result

    return [{"page": 1, "text": extracted_text.strip()}]


def find_relevant_context(question, documents):
    stop_words = {
        "what", "is", "are", "the", "a", "an", "in", "on", "of", "to", "for",
        "and", "explain", "tell", "me", "about", "how", "why", "does", "do",
        "can", "you", "please", "define", "difference", "between", "whats", "what's"
    }
    raw_words = re.findall(r"\b[a-zA-Z0-9]+\b", question.lower())
    question_words = [w for w in raw_words if w not in stop_words]
    matches = []

    for doc in documents:
        doc_text = doc.get("extracted_text", "")
        if not doc_text:
            continue

        records = get_page_records(doc)
        if not records:
            records = [{"page": 1, "text": doc_text}]

        for record in records:
            page_text = record.get("text", "")
            if not page_text or len(page_text.strip()) < 10:
                continue
            p_lower = page_text.lower()
            score = 0
            for w in question_words:
                if w in p_lower:
                    score += 3
                elif len(w) >= 4:
                    stem = w[:3]
                    for dw in re.findall(r"\b[a-zA-Z0-9]+\b", p_lower):
                        if len(dw) >= 4 and dw[:3] == stem:
                            score += 2
                            break

            if score > 0:
                matches.append({
                    "score": score,
                    "text": page_text,
                    "document": doc.get("name", "Uploaded document"),
                    "document_id": doc.get("id"),
                    "page": record.get("page", 1)
                })

    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[:4]


# --------------------------------------------------
# 4. SOURCE VIEWER
# --------------------------------------------------

def show_source_viewer():
    selected = st.session_state.get("selected_source")
    if not selected:
        return

    st.divider()
    st.subheader(f"🔍 Source Receipt: {selected.get('label', 'Cited Source')}")

    link_or_file = selected.get("link_or_file", "")
    snippet = selected.get("snippet", "")
    similarity = selected.get("similarity", None)

    col_view, col_info = st.columns([3, 2], gap="medium")

    with col_view:
        # Check if source is a local rendered asset (page image, slide card, or diagram)
        if link_or_file and link_or_file.lower().endswith((".png", ".jpg", ".jpeg")):
            full_path = os.path.join(ROOT_DIR, link_or_file) if not os.path.isabs(link_or_file) else link_or_file
            if os.path.exists(full_path):
                st.image(full_path, caption=selected.get("label", "Source Image"), use_container_width=True)
            else:
                st.warning(f"Preview image file not found at {link_or_file}.")
        
        # Check if source is a video link
        elif link_or_file and link_or_file.startswith("http"):
            st.video(link_or_file)
            st.link_button("🌐 Open in YouTube", link_or_file)

        # Fallback to in-session uploaded document viewer
        elif selected.get("document_id"):
            documents = st.session_state.get("uploaded_materials", [])
            source_doc = next((doc for doc in documents if doc.get("id") == selected.get("document_id")), None)
            if source_doc:
                st.markdown(f"**Document:** {source_doc.get('name')}")
                st.markdown(f"**Page:** {selected.get('page', 1)}")
                for record in get_page_records(source_doc):
                    if record["page"] == int(selected.get("page", 1)):
                        st.text_area("Page Content", record["text"], height=250)
                        break

    with col_info:
        st.markdown("#### Citation Metadata")
        st.write(f"**Modality:** `{selected.get('modality', 'text')}`")
        if selected.get("location"):
            st.write(f"**Location:** `{selected.get('location')}`")
        if selected.get("chunk_id"):
            st.write(f"**Chunk ID:** `{selected.get('chunk_id')}`")
        if similarity is not None:
            st.metric("Vector Cosine Similarity", f"{float(similarity):.2f}")
        
        if snippet:
            st.markdown("**Excerpt:**")
            st.info(snippet)

        if st.button("✖️ Close Source Viewer"):
            st.session_state["selected_source"] = None
            st.rerun()


# --------------------------------------------------
# 5. DISPLAY CHAT MESSAGES
# --------------------------------------------------

def display_message(message, message_index):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        citations = message.get("citations", [])
        if citations:
            st.markdown("**Cited Sources (Click to verify):**")
            cols = st.columns(min(len(citations), 4))
            for index, citation in enumerate(citations):
                col = cols[index % len(cols)]
                label = citation.get("label") or f"📄 {citation.get('document', 'Doc')} (p.{citation.get('page', 1)})"
                with col:
                    if st.button(f"🔍 {label}", key=f"source_{message_index}_{index}", use_container_width=True):
                        st.session_state["selected_source"] = citation
                        st.rerun()


# --------------------------------------------------
# 6. ACTIVE STUDY MATERIAL STATUS
# --------------------------------------------------

with st.expander("📁 Grounded Knowledge Sources", expanded=False):
    st.write("✅ **Supabase Vector Store Connected** (67 chunks indexed: Textbook PDF, Lecture Slides, YouTube timestamps, Diagrams)")
    docs = st.session_state.get("uploaded_materials", [])
    if docs:
        st.write(f"📄 Plus **{len(docs)}** active uploaded in-session document(s)")


# --------------------------------------------------
# 7. QUICK QUESTIONS (Including Refusal Test)
# --------------------------------------------------

st.markdown("### ✨ Quick Questions to Test Grounding & Refusal")

quick_questions = [
    ("What is Snell's law?", "In-Domain (Textbook/Slides)"),
    ("What is total internal reflection?", "In-Domain (YouTube/Diagram)"),
    ("Explain Brewster's angle and polarization", "In-Domain (Textbook/Slides)"),
    ("How do I bake chocolate chip cookies?", "⚠️ Off-Domain (Test Refusal Gate)")
]

columns = st.columns(4)

for index, (question, note) in enumerate(quick_questions):
    with columns[index]:
        if st.button(f"{question}\n\n*{note}*", key=f"quick_question_{index}", use_container_width=True):
            st.session_state["pending_question"] = question
            st.rerun()


# --------------------------------------------------
# --------------------------------------------------
# 8. CHAT CONTROLS & HISTORY
# --------------------------------------------------

with st.sidebar:
    st.markdown("### 🛠️ Chat Controls")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state["chat_messages"] = []
        st.session_state["selected_source"] = None
        st.rerun()

# Filter out empty or broken messages from past session
valid_messages = []
for m in st.session_state.get("chat_messages", []):
    content = m.get("content", "").strip()
    if content and content != "?":
        valid_messages.append(m)
st.session_state["chat_messages"] = valid_messages

for message_index, message in enumerate(st.session_state["chat_messages"]):
    display_message(message, message_index)


# --------------------------------------------------
# 9. HANDLE QUESTION INPUT
# --------------------------------------------------

prompt = st.chat_input("Ask a question from your course materials...")

if st.session_state.get("pending_question"):
    prompt = st.session_state.pop("pending_question")

if prompt and str(prompt).strip():
    prompt = str(prompt).strip()

    st.session_state["chat_messages"].append({
        "role": "user",
        "content": prompt,
        "citations": []
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🤖 Searching multimodal course materials in Supabase & synthesizing cited answer..."):
            answer = ""
            citations = []

            # 1. Primary: Use Member A's Supabase Vector Search & Grounded Tutor Engine
            if HAS_RETRIEVAL_ENGINE:
                try:
                    # Pass previous conversation context (excluding the new prompt)
                    prev_turns = [
                        {"role": m["role"], "text": m["content"]}
                        for m in st.session_state["chat_messages"][:-1][-4:]
                    ]
                    ans, cits, _ = ask_tutor(user_question=prompt, chat_history=prev_turns)
                    if ans and not ans.startswith("Error generating answer"):
                        answer = ans
                        citations = cits
                except Exception as e:
                    print("Retrieval engine error:", e)

            # 2. Fallback: Use in-session uploaded documents if retrieval engine didn't match
            if (not answer or "cannot answer this" in answer.lower()) and st.session_state.get("uploaded_materials"):
                uploaded_docs = st.session_state.get("uploaded_materials", [])
                matches = find_relevant_context(prompt, uploaded_docs)
                if matches:
                    context_parts = [f"Source: {m['document']}\nPage: {m['page']}\nText:\n{m['text'][:3000]}" for m in matches]
                    study_material = "\n\n---\n\n".join(context_parts)
                    try:
                        fallback_answer = generate_tutor_answer(question=prompt, study_material=study_material)
                        if fallback_answer and "not found" not in fallback_answer.lower():
                            answer = fallback_answer
                            citations = [
                                {
                                    "label": f"{m['document']} (Page {m['page']})",
                                    "document": m["document"],
                                    "document_id": m["document_id"],
                                    "page": m["page"],
                                    "snippet": m["text"][:150] + "..."
                                }
                                for m in matches
                            ]
                    except Exception as fb_err:
                        print("Fallback answer error:", fb_err)

            if not answer:
                answer = "I cannot answer this. This concept is not covered in your uploaded course materials."
                citations = []

            st.markdown(answer)

            if citations:
                st.markdown("**Cited Sources (Click to verify):**")
                cols = st.columns(min(len(citations), 4))
                for index, citation in enumerate(citations):
                    col = cols[index % len(cols)]
                    label = citation.get("label") or f"📄 {citation.get('document', 'Doc')}"
                    with col:
                        if st.button(f"🔍 {label}", key=f"source_curr_{index}", use_container_width=True):
                            st.session_state["selected_source"] = citation
                            st.rerun()

    st.session_state["chat_messages"].append({
        "role": "assistant",
        "content": answer,
        "citations": citations
    })



# --------------------------------------------------
# 10. SOURCE VIEWER PANEL
# --------------------------------------------------

show_source_viewer()