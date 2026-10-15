
import sys
import io
import re
from pathlib import Path
from datetime import datetime
from pptx import Presentation
try:
    from docx import Document
except ImportError:
    Document = None

import streamlit as st
from pypdf import PdfReader

# --------------------------------------------------
# 1. Project path and imports
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from study_data import init_session_state, AVAILABLE_TOPICS

try:
    from ingest_youtube import ingest_video, extract_video_id
    HAS_YT_INGEST = True
except Exception as e:
    HAS_YT_INGEST = False
    print("YouTube ingest import warning:", e)


# --------------------------------------------------
# 2. Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Upload Study Material | AI Study Companion",
    page_icon="📚",
    layout="wide"
)

init_session_state()


# --------------------------------------------------
# 3. Initialize uploaded materials
# --------------------------------------------------

if "uploaded_materials" not in st.session_state:
    st.session_state["uploaded_materials"] = []

if "sample_materials_initialized" not in st.session_state:
    st.session_state["uploaded_materials"] = [
        {
            "id": "pdf_001",
            "name": "Physics_of_Light_and_Optics_Textbook.pdf",
            "size_kb": 8677,
            "upload_time": "Pre-Ingested",
            "topic": "Physics of Light and Optics",
            "tag": "Textbook",
            "modality": "pdf",
            "page_count": 50,
            "extracted_text": "Physics of Light and Optics by Justin Peatross and Michael Ware. Covers electromagnetic phenomena, wave equations, reflection, refraction, polarization, and Fourier optics.",
            "page_records": [{"page_number": i, "text": f"Chapter content for page {i}"} for i in range(1, 51)],
            "file_bytes": None,
            "status": "Indexed in Supabase pgvector"
        },
        {
            "id": "slides_001",
            "name": "Optics_Lecture_Slides.pptx",
            "size_kb": 37,
            "upload_time": "Pre-Ingested",
            "topic": "Wave Optics",
            "tag": "Lecture Slides",
            "modality": "slide",
            "page_count": 10,
            "extracted_text": "Lecture 1 to 10 slide cards covering Snell's law, Fermat's principle, Brewster's angle, and Huygens' principle.",
            "page_records": [{"page_number": i, "text": f"Slide {i} card preview and notes"} for i in range(1, 11)],
            "file_bytes": None,
            "status": "Indexed in Supabase pgvector"
        },
        {
            "id": "yt_fD1544bM_c4",
            "name": "Optics Lecture: Reflection, Snell's Law & Wave Theory (fD1544bM_c4)",
            "size_kb": 0,
            "upload_time": "Pre-Ingested",
            "topic": "Electromagnetic Waves",
            "tag": "Video Lecture",
            "modality": "youtube",
            "video_id": "fD1544bM_c4",
            "video_url": "https://www.youtube.com/watch?v=fD1544bM_c4",
            "page_count": 9,
            "extracted_text": "Timestamped lecture video transcript covering Snell's Law, Total Internal Reflection, Brewster's angle, and Huygens' principle.",
            "page_records": [
                {"page_number": 1, "start_sec": 0, "end_sec": 25, "url": "https://www.youtube.com/watch?v=fD1544bM_c4&t=0s", "text": "[00:00 - 00:25] Welcome to our lecture on Optics. Fundamental nature of light as an electromagnetic wave."},
                {"page_number": 2, "start_sec": 25, "end_sec": 55, "url": "https://www.youtube.com/watch?v=fD1544bM_c4&t=25s", "text": "[00:25 - 00:55] In vacuum, electromagnetic waves travel at universal constant c = 3x10^8 m/s."},
                {"page_number": 3, "start_sec": 55, "end_sec": 90, "url": "https://www.youtube.com/watch?v=fD1544bM_c4&t=55s", "text": "[00:55 - 01:30] Boundary between dielectric media: simultaneous reflection and refraction."},
                {"page_number": 4, "start_sec": 90, "end_sec": 125, "url": "https://www.youtube.com/watch?v=fD1544bM_c4&t=90s", "text": "[01:30 - 02:05] Law of reflection: angle of incidence equals angle of reflection."},
                {"page_number": 5, "start_sec": 125, "end_sec": 165, "url": "https://www.youtube.com/watch?v=fD1544bM_c4&t=125s", "text": "[02:05 - 02:45] Snell's Law: n1*sin(theta1) = n2*sin(theta2), where refractive index is n = c/v."},
                {"page_number": 6, "start_sec": 165, "end_sec": 210, "url": "https://www.youtube.com/watch?v=fD1544bM_c4&t=165s", "text": "[02:45 - 03:30] Critical angle condition: theta2 becomes 90 degrees."},
                {"page_number": 7, "start_sec": 210, "end_sec": 250, "url": "https://www.youtube.com/watch?v=fD1544bM_c4&t=210s", "text": "[03:30 - 04:10] Total Internal Reflection (TIR): all energy reflected back into denser medium, fiber optics principle."},
                {"page_number": 8, "start_sec": 250, "end_sec": 295, "url": "https://www.youtube.com/watch?v=fD1544bM_c4&t=250s", "text": "[04:10 - 04:55] Polarization by reflection at Brewster's angle: reflected light is completely linearly polarized."},
                {"page_number": 9, "start_sec": 295, "end_sec": 345, "url": "https://www.youtube.com/watch?v=fD1544bM_c4&t=295s", "text": "[04:55 - 05:45] Huygens' Principle: every wavefront point acts as secondary wavelet source."}
            ],
            "file_bytes": None,
            "status": "Deep-Linked & Indexed (9 timestamped chapters in Supabase)"
        }
    ]
    st.session_state["sample_materials_initialized"] = True


# --------------------------------------------------
# 4. Page heading
# --------------------------------------------------

st.title("📚 Ingest & Manage Study Material")

st.caption(
    "Multimodal ingestion for textbooks (PDF), slide decks (PPTX), lecture notes, "
    "and YouTube video lectures with timestamp deep links."
)

tab_upload, tab_youtube = st.tabs([
    "📄 Upload Documents (PDF, PPTX, DOCX, TXT)",
    "🎥 Ingest YouTube Video Lecture"
])

with tab_upload:
    st.write(
        "Upload your study files to prepare them for "
        "source-grounded learning and pgvector indexing."
    )

    uploaded_file = st.file_uploader(
        "Choose a study file",
        type=["pdf", "pptx", "ppt", "txt", "docx"],
        help="Supported extraction: PDF, TXT, PPTX and DOCX."
    )

    col1, col2 = st.columns(2)

    with col1:
        selected_topic = st.selectbox(
            "Select Topic",
            AVAILABLE_TOPICS,
            key="doc_selected_topic"
        )

    with col2:
        selected_tag = st.text_input(
            "Add a tag (optional)",
            placeholder="e.g. Unit 1, Important Notes",
            key="doc_selected_tag"
        )

    if st.button(
        "⚙️ Process Document",
        type="primary",
        use_container_width=True
    ):

        if uploaded_file is None:
            st.warning("Please upload a file first.")

    else:
        file_name = uploaded_file.name
        file_extension = Path(file_name).suffix.lower()
        original_file_bytes = uploaded_file.getvalue()

        extracted_text = ""
        page_records = []
        page_count = 0
        status = "Extraction unavailable"

        progress_bar = st.progress(0)
        status_text = st.empty()

        try:

            # ------------------------------------------
            # PDF extraction
            # ------------------------------------------

            if file_extension == ".pdf":

                status_text.write("Opening PDF...")

                pdf_reader = PdfReader(
                    io.BytesIO(original_file_bytes)
                )

                page_count = len(pdf_reader.pages)
                all_pages_text = []

                for index, page in enumerate(pdf_reader.pages):

                    page_number = index + 1

                    status_text.write(
                        f"Processing PDF page "
                        f"{page_number} of {page_count}..."
                    )

                    page_text = page.extract_text() or ""

                    page_records.append({
                        "page_number": page_number,
                        "text": page_text
                    })

                    all_pages_text.append(
                        f"--- Page {page_number} ---\n{page_text}"
                    )

                    progress_bar.progress(
                        int(page_number / max(page_count, 1) * 100)
                    )

                extracted_text = "\n\n".join(all_pages_text)

                status = (
                    "Extracted"
                    if extracted_text.strip()
                    else "No text found"
                )

            # ------------------------------------------
            # TXT extraction
            # ------------------------------------------

            elif file_extension == ".txt":

                status_text.write("Reading text file...")

                extracted_text = original_file_bytes.decode(
                    "utf-8",
                    errors="replace"
                )

                page_records.append({
                    "page_number": 1,
                    "text": extracted_text
                })

                page_count = 1
                progress_bar.progress(100)

                status = (
                    "Extracted"
                    if extracted_text.strip()
                    else "No text found"
                )

            # ------------------------------------------
            # PPTX extraction
            # ------------------------------------------

            elif file_extension == ".pptx":

                from pptx import Presentation

                status_text.write("Opening PowerPoint presentation...")

                presentation = Presentation(
                    io.BytesIO(original_file_bytes)
                )

                page_count = len(presentation.slides)
                all_slides_text = []

                for index, slide in enumerate(presentation.slides):

                    slide_number = index + 1
                    slide_parts = []

                    status_text.write(
                        f"Processing slide {slide_number} "
                        f"of {page_count}..."
                    )

                    for shape in slide.shapes:

                        # Text boxes and ordinary text shapes
                        if getattr(shape, "has_text_frame", False):
                            shape_text = shape.text.strip()

                            if shape_text:
                                slide_parts.append(shape_text)

                        # Tables inside slides
                        if getattr(shape, "has_table", False):
                            for row in shape.table.rows:
                                cells = [
                                    cell.text.strip()
                                    for cell in row.cells
                                ]

                                if any(cells):
                                    slide_parts.append(
                                        " | ".join(cells)
                                    )

                    slide_text = "\n".join(slide_parts)

                    page_records.append({
                        "page_number": slide_number,
                        "text": slide_text
                    })

                    all_slides_text.append(
                        f"--- Page {slide_number} ---\n{slide_text}"
                    )

                    progress_bar.progress(
                        int(slide_number / max(page_count, 1) * 100)
                    )

                extracted_text = "\n\n".join(all_slides_text)

                status = (
                    "Extracted"
                    if extracted_text.strip()
                    else "No text found"
                )

            # ------------------------------------------
            # DOCX extraction
            # ------------------------------------------

            elif file_extension == ".docx":
                if Document is None:
                    st.error("python-docx is not installed in the environment.")
                    status = "Failed: python-docx missing"
                    extracted_text = ""
                else:
                    status_text.write("Reading Word document...")
                    document = Document(
                        io.BytesIO(original_file_bytes)
                    )

                text_parts = []

                total_items = (
                    len(document.paragraphs)
                    + len(document.tables)
                )

                total_items = max(total_items, 1)
                processed_items = 0

                # Extract paragraphs
                for paragraph in document.paragraphs:

                    paragraph_text = paragraph.text.strip()

                    if paragraph_text:
                        text_parts.append(paragraph_text)

                    processed_items += 1

                    progress_bar.progress(
                        min(
                            int(processed_items / total_items * 100),
                            100
                        )
                    )

                    status_text.write(
                        f"Processing Word content "
                        f"{processed_items} of {total_items}..."
                    )

                # Extract tables
                for table in document.tables:

                    for row in table.rows:
                        cells = [
                            cell.text.strip()
                            for cell in row.cells
                        ]

                        if any(cells):
                            text_parts.append(" | ".join(cells))

                    processed_items += 1

                    progress_bar.progress(
                        min(
                            int(processed_items / total_items * 100),
                            100
                        )
                    )

                extracted_text = "\n".join(text_parts)

                # DOCX does not provide reliable page boundaries
                # through python-docx, so save the text as one section.
                page_records.append({
                    "page_number": 1,
                    "text": extracted_text
                })

                page_count = 1

                status = (
                    "Extracted"
                    if extracted_text.strip()
                    else "No text found"
                )

            # ------------------------------------------
            # Old PPT format
            # ------------------------------------------

            elif file_extension == ".ppt":

                status = "Convert PPT to PPTX"

                st.warning(
                    "This is an older .ppt file. "
                    "Open it in PowerPoint and use Save As → "
                    "PowerPoint Presentation (.pptx), then upload it again."
                )

            # ------------------------------------------
            # Save file details
            # ------------------------------------------

            new_doc = {
                "id": (
                    f"doc_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                ),
                "name": file_name,
                "size_kb": round(
                    len(original_file_bytes) / 1024, 2
                ),
                "upload_time": datetime.now().strftime(
                    "%d-%m-%Y %H:%M"
                ),
                "topic": selected_topic,
                "tag": selected_tag.strip() or "General",
                "page_count": page_count,
                "extracted_text": extracted_text,
                "page_records": page_records,

                # Keep original bytes for supported source viewing
                "file_bytes": (
                    original_file_bytes
                    if file_extension in [".pdf", ".pptx", ".docx", ".txt"]
                    else None
                ),

                "status": status
            }

            # Avoid adding an unsupported PPT file as a processed document
            if file_extension != ".ppt":
                st.session_state["uploaded_materials"].append(new_doc)

            progress_bar.progress(100)
            status_text.empty()

            if status == "Extracted":
                st.success(
                    f"✅ {file_name} processed successfully!"
                )

            elif status == "No text found":
                st.warning(
                    "The file was added, but no readable text "
                    "was extracted. Scanned PDFs and image-only "
                    "slides may need OCR."
                )

            elif status == "Convert PPT to PPTX":
                st.info("Convert the file to PPTX and upload it again.")

            st.rerun()

        except ImportError as error:
            progress_bar.empty()
            status_text.empty()

            st.error(
                "A required library is missing. Install the libraries "
                "using the commands shown below, then restart Streamlit."
            )

        except Exception as error:
            progress_bar.empty()
            status_text.empty()

            st.error(f"File processing failed: {error}")


with tab_youtube:
    st.write(
        "Ingest YouTube video lectures into your knowledge base. "
        "Extracts timestamped chapters, generates 1000-dimensional Gemini embeddings, "
        "and saves deep-link citations into Supabase pgvector."
    )

    yt_url = st.text_input(
        "YouTube Lecture URL or Video ID",
        value="https://www.youtube.com/watch?v=fD1544bM_c4",
        help="Paste a YouTube URL (e.g. https://www.youtube.com/watch?v=fD1544bM_c4) or 11-char ID",
        key="yt_lecture_url"
    )

    col_yt1, col_yt2 = st.columns(2)
    with col_yt1:
        yt_title = st.text_input(
            "Lecture Video Title",
            value="Optics Lecture: Reflection, Snell's Law & Wave Theory",
            key="yt_lecture_title"
        )
    with col_yt2:
        yt_topic = st.selectbox(
            "Associated Concept / Topic",
            AVAILABLE_TOPICS,
            index=AVAILABLE_TOPICS.index("Electromagnetic Waves") if "Electromagnetic Waves" in AVAILABLE_TOPICS else 0,
            key="yt_lecture_topic"
        )

    if yt_url.strip():
        with st.expander("📺 Video Lecture Preview", expanded=True):
            st.video(yt_url.strip())

    if st.button("🚀 Ingest & Index YouTube Lecture", type="primary", use_container_width=True, key="btn_ingest_yt"):
        if not yt_url.strip():
            st.warning("Please enter a YouTube video URL or ID.")
        else:
            with st.spinner("🤖 Fetching transcript, generating Gemini embeddings, and indexing into Supabase pgvector..."):
                try:
                    res = ingest_video(
                        video_id=yt_url.strip(),
                        title=yt_title.strip() or "Optics Lecture",
                        topic_id=yt_topic.lower().replace(" ", "_")
                    )
                    clean_id = res["video_id"]
                    chunks = res.get("chunks", [])
                    new_doc = {
                        "id": f"yt_{clean_id}",
                        "name": f"{res['title']} ({clean_id})",
                        "size_kb": 0,
                        "upload_time": datetime.now().strftime("%d-%m-%Y %H:%M"),
                        "topic": yt_topic,
                        "tag": "Video Lecture",
                        "modality": "youtube",
                        "video_id": clean_id,
                        "video_url": res.get("video_url") or f"https://www.youtube.com/watch?v={clean_id}",
                        "page_count": len(chunks),
                        "extracted_text": "\n\n".join([f"[{int(c['start_sec'])}s - {int(c['end_sec'])}s] {c['text']}" for c in chunks]),
                        "page_records": [
                            {
                                "page_number": idx + 1,
                                "start_sec": c["start_sec"],
                                "end_sec": c["end_sec"],
                                "url": c["url"],
                                "text": f"[{int(c['start_sec'])}s - {int(c['end_sec'])}s] {c['text']}"
                            }
                            for idx, c in enumerate(chunks)
                        ],
                        "file_bytes": None,
                        "status": f"Indexed ({len(chunks)} timestamped chapters in Supabase)"
                    }

                    # Update or append in session state
                    existing_idx = next((i for i, m in enumerate(st.session_state["uploaded_materials"]) if m.get("id") == new_doc["id"] or m.get("video_id") == clean_id), None)
                    if existing_idx is not None:
                        st.session_state["uploaded_materials"][existing_idx] = new_doc
                    else:
                        st.session_state["uploaded_materials"].append(new_doc)

                    st.success(f"✅ Successfully ingested & indexed {len(chunks)} timestamped chapters for '{res['title']}'! ({res.get('transcript_source', 'Indexed')})")
                    st.rerun()
                except Exception as yt_err:
                    st.error(f"Failed to ingest YouTube video: {yt_err}")


# --------------------------------------------------
# 7. Show uploaded materials
# --------------------------------------------------

st.divider()
st.subheader("📂 Your Study Materials")

materials = st.session_state["uploaded_materials"]

if not materials:
    st.info("No study materials added yet.")

else:
    st.caption(f"Total materials: {len(materials)}")

    for index, material in enumerate(materials):
        is_yt = (
            material.get("modality") == "youtube"
            or material.get("tag") == "Video Lecture"
            or material.get("video_id")
            or str(material.get("name", "")).endswith(".youtube")
        )
        icon = "🎥" if is_yt else ("🖼️" if material.get("tag") == "Lecture Slides" else "📄")

        with st.expander(
            f"{icon} {material['name']} — {material['status']}",
            expanded=False
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Topic:** {material['topic']}")
                st.write(f"**Tag:** {material['tag']}")
                st.write(f"**Size:** {material['size_kb']} KB" if not is_yt else "**Format:** YouTube Video")

            with col2:
                st.write(f"**Sections / Chapters:** {material['page_count']}")
                st.write(f"**Uploaded:** {material['upload_time']}")
                st.write(f"**Status:** {material['status']}")

            # If it is a YouTube video, embed interactive player and chapters
            if is_yt:
                v_url = material.get("video_url") or f"https://www.youtube.com/watch?v={material.get('video_id', 'fD1544bM_c4')}"
                st.markdown("#### 📺 Lecture Video Player")
                st.video(v_url)

                st.markdown("#### ⏱️ Timestamped Chapters & Citations")
                records = material.get("page_records", [])
                if records:
                    for r in records:
                        c_time, c_btn = st.columns([4, 1])
                        with c_time:
                            st.write(f"• **Chapter {r['page_number']}:** {r.get('text', '')}")
                        with c_btn:
                            st.link_button("▶️ Watch", r.get("url") or v_url)
                else:
                    st.info("Video chapters indexed in Supabase.")

            elif material.get("extracted_text", "").strip():
                st.markdown("**Extracted Text Preview**")
                st.text(material["extracted_text"][:2000])

                if len(material["extracted_text"]) > 2000:
                    st.caption("Preview limited to the first 2,000 characters.")

                with st.expander("View page-wise or slide-wise text"):
                    for page in material.get("page_records", []):
                        st.markdown(f"**Page/Slide {page['page_number']}**")
                        st.text(page.get("text", "")[:1500] or "No readable text on this page or slide.")

            if (
                material["name"].lower().endswith(".pdf")
                and material.get("file_bytes")
            ):
                st.success(
                    "Original PDF is saved in this session for the Source Viewer."
                )

            if st.button(
                "🗑️ Remove Material",
                key=f"delete_{material['id']}"
            ):
                st.session_state["uploaded_materials"].pop(index)
                st.rerun()
