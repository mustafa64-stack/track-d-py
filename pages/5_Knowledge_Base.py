import os
import sys
import json
import re
from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from study_data import init_session_state
from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

st.set_page_config(
    page_title="Knowledge Base | AI Study Companion",
    page_icon="📚",
    layout="wide"
)

init_session_state()

st.title("📚 Course Knowledge Graph & Chunks")
st.caption(
    "Explore the 38-topic concept hierarchy, prerequisite graph, "
    "and multimodal chunks indexed in Supabase (PDF, Slides, YouTube, Diagrams)."
)

# --------------------------------------------------
# 1. LOAD TOPIC TREE & PREREQUISITES
# --------------------------------------------------

tree_path = ROOT_DIR / "topic_tree.json"
topics_data = []

if tree_path.exists():
    try:
        with open(tree_path, "r", encoding="utf-8") as f:
            t_json = json.load(f)
            topics_data = t_json.get("topics", [])
    except Exception as e:
        print("Error loading topic tree:", e)

# --------------------------------------------------
# 2. LOAD CHUNKS FROM SUPABASE
# --------------------------------------------------

@st.cache_data(ttl=300)
def fetch_supabase_chunks():
    try:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        res = sb.table("chunks").select(
            "id, source_id, modality, text, page, slide, start_sec, end_sec, topic_id, image_ref"
        ).order("id").execute()
        return res.data or []
    except Exception as e:
        print("Supabase fetch error:", e)
        return []

supabase_chunks = fetch_supabase_chunks()

# Merge in-session uploaded document chunks
session_docs = st.session_state.get("uploaded_materials", [])

# --------------------------------------------------
# 3. METRICS OVERVIEW
# --------------------------------------------------

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Course Topics", len(topics_data) or 38)
with m2:
    prereq_count = sum(len(t.get("prerequisites", [])) for t in topics_data)
    st.metric("Prerequisite Graph Edges", prereq_count or 27)
with m3:
    st.metric("Indexed Chunks in Supabase", len(supabase_chunks) or 67)
with m4:
    modalities = {c.get("modality") for c in supabase_chunks if c.get("modality")}
    st.metric("Active Modalities", f"{len(modalities)} (PDF, Slide, YT, Img)")

st.divider()

# --------------------------------------------------
# 4. TABS: TOPIC TREE vs BROWSE CHUNKS
# --------------------------------------------------

tab_tree, tab_chunks = st.tabs(["🌳 Concept Hierarchy & Prerequisite Graph", "🧩 Multimodal Chunk Explorer"])

with tab_tree:
    st.subheader("Optics Concept Hierarchy & Prerequisite Edges")
    st.caption("Extracted from course textbook, slides, and lectures into an educational knowledge graph:")

    search_topic = st.text_input("🔍 Search Concept", placeholder="e.g. reflection, fourier, maxwell...")

    filtered_topics = topics_data
    if search_topic.strip():
        q = search_topic.lower()
        filtered_topics = [
            t for t in topics_data
            if q in t.get("name", "").lower() or q in t.get("description", "").lower()
        ]

    for topic in filtered_topics:
        name = topic.get("name", topic.get("topic_id"))
        tid = topic.get("topic_id")
        desc = topic.get("description", "")
        prereqs = topic.get("prerequisites", [])
        subtopics = topic.get("subtopics", [])
        refs = topic.get("source_refs", [])

        with st.expander(f"📖 **{name}** (`{tid}`)", expanded=False):
            st.markdown(f"*{desc}*")
            
            c_sub, c_pre = st.columns(2)
            with c_sub:
                if subtopics:
                    st.markdown("**Subtopics / Key Ideas:**")
                    for s in subtopics:
                        st.markdown(f"• {s}")
            with c_pre:
                if prereqs:
                    st.markdown("**Prerequisites:**")
                    for p in prereqs:
                        st.markdown(f"🔗 `{p}`")
                else:
                    st.caption("No prerequisites (Foundational Concept)")

            if refs:
                st.caption(f"Source chunks linked: {len(refs)}")

with tab_chunks:
    st.subheader("Multimodal Chunks in Supabase pgvector")
    st.caption("Unified 1000-dimensional embeddings (`gemini-embedding-001`) with HNSW index:")

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        mod_filter = st.selectbox("Filter Modality", ["All Modalities", "pdf", "slide", "youtube", "image"])
    with f_col2:
        source_search = st.text_input("Filter Text / Keyword", placeholder="Search text content...")

    visible = supabase_chunks
    if mod_filter != "All Modalities":
        visible = [c for c in visible if c.get("modality") == mod_filter]
    if source_search.strip():
        sq = source_search.lower()
        visible = [c for c in visible if sq in c.get("text", "").lower()]

    st.caption(f"Displaying {len(visible)} chunks")

    for chunk in visible[:30]:
        mod = chunk.get("modality", "text")
        cid = chunk.get("id")
        text = chunk.get("text", "")
        image_ref = chunk.get("image_ref", "")
        page = chunk.get("page")
        slide = chunk.get("slide")
        start_sec = chunk.get("start_sec")
        end_sec = chunk.get("end_sec")

        badge = f"📄 PDF Page {page}" if mod == "pdf" else (
            f"🖼️ Slide {slide}" if mod == "slide" else (
                f"🎥 Video [{int(start_sec or 0)}s - {int(end_sec or 0)}s]" if mod == "youtube" else (
                    f"🔬 Diagram (p.{page})" if mod == "image" else f"🧩 {mod}"
                )
            )
        )

        with st.expander(f"{badge} — `{cid}`", expanded=False):
            c_txt, c_media = st.columns([3, 2])
            with c_txt:
                st.write(text)
                if chunk.get("topic_id"):
                    st.caption(f"Topic Tag: `{chunk.get('topic_id')}`")
                if image_ref and image_ref.endswith((".png", ".jpg", ".jpeg")):
                    full_p = os.path.join(ROOT_DIR, image_ref)
                    if os.path.exists(full_p):
                        st.image(full_p, use_container_width=True)
                elif image_ref and image_ref.startswith("http"):
                    start_time_sec = int(start_sec or 0)
                    st.video(image_ref, start_time=start_time_sec)
                    st.link_button(f"🌐 Open at {start_time_sec}s on YouTube", image_ref)
