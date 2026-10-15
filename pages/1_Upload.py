
import sys
import io
from pathlib import Path
from datetime import datetime
from pptx import Presentation
from docx import Document

import streamlit as st
from pypdf import PdfReader

# --------------------------------------------------
# 1. Project path and imports
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from study_data import init_session_state, AVAILABLE_TOPICS


# --------------------------------------------------
# 2. Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Upload Study Material",
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
            "page_count": 10,
            "extracted_text": "Lecture 1 to 10 slide cards covering Snell's law, Fermat's principle, Brewster's angle, and Huygens' principle.",
            "page_records": [{"page_number": i, "text": f"Slide {i} card preview and notes"} for i in range(1, 11)],
            "file_bytes": None,
            "status": "Indexed in Supabase pgvector"
        },
        {
            "id": "yt_001",
            "name": "Optics_Lecture_Reflection_Refraction.youtube",
            "size_kb": 0,
            "upload_time": "Pre-Ingested",
            "topic": "Electromagnetic Waves",
            "tag": "Video Lecture",
            "page_count": 4,
            "extracted_text": "Timestamped lecture video transcript sliced into 35-second deep-link chunks with exact start and end timestamps.",
            "page_records": [],
            "file_bytes": None,
            "status": "Deep-Linked & Indexed"
        }
    ]
    st.session_state["sample_materials_initialized"] = True


# --------------------------------------------------
# 4. Page heading
# --------------------------------------------------

st.title("📚 Upload Study Material")

st.write(
    "Upload your study files to prepare them for "
    "source-grounded learning."
)

st.info(
    "PDF, TXT, PPTX and DOCX files support text extraction. "
    "Old PPT files must first be converted to PPTX."
)


# --------------------------------------------------
# 5. Upload form
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Choose a study file",
    type=["pdf", "pptx", "ppt", "txt", "docx"],
    help="Supported extraction: PDF, TXT, PPTX and DOCX."
)

col1, col2 = st.columns(2)

with col1:
    selected_topic = st.selectbox(
        "Select Topic",
        AVAILABLE_TOPICS
    )

with col2:
    selected_tag = st.text_input(
        "Add a tag (optional)",
        placeholder="e.g. Unit 1, Important Notes"
    )


# --------------------------------------------------
# 6. Process uploaded file
# --------------------------------------------------

if st.button(
    "⚙️ Process File",
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

                from docx import Document

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


# --------------------------------------------------
# 7. Show uploaded materials
# --------------------------------------------------

st.divider()
st.subheader("📂 Your Study Materials")

materials = st.session_state["uploaded_materials"]

if not materials:
    st.info("No study materials added yet.")

else:
    st.caption(f"Total files: {len(materials)}")

    for index, material in enumerate(materials):

        with st.expander(
            f"📄 {material['name']} — {material['status']}",
            expanded=False
        ):

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Topic:** {material['topic']}")
                st.write(f"**Tag:** {material['tag']}")
                st.write(f"**Size:** {material['size_kb']} KB")

            with col2:
                st.write(f"**Pages/Sections:** {material['page_count']}")
                st.write(f"**Uploaded:** {material['upload_time']}")
                st.write(f"**Status:** {material['status']}")

            if material.get("extracted_text", "").strip():

                st.markdown("**Extracted Text Preview**")

                st.text(material["extracted_text"][:2000])

                if len(material["extracted_text"]) > 2000:
                    st.caption(
                        "Preview limited to the first 2,000 characters."
                    )

                with st.expander("View page-wise or slide-wise text"):
                    for page in material.get("page_records", []):

                        st.markdown(
                            f"**Page/Slide {page['page_number']}**"
                        )

                        st.text(
                            page.get("text", "")[:1500]
                            or "No readable text on this page or slide."
                        )

            if (
                material["name"].lower().endswith(".pdf")
                and material.get("file_bytes")
            ):
                st.success(
                    "Original PDF is saved in this session "
                    "for the Source Viewer."
                )

            if st.button(
                "🗑️ Delete File",
                key=f"delete_{material['id']}"
            ):
                st.session_state["uploaded_materials"].pop(index)
                st.rerun()
