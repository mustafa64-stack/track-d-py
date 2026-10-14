import os
import time
import pymupdf
from supabase import create_client, Client
from google import genai
from google.genai import types
from config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    GEMINI_API_KEY,
    GEMINI_FLASH_MODEL,
    GEMINI_EMBEDDING_MODEL,
    EMBEDDING_DIM,
    DIAGRAMS_DIR
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

PDF_FILE = "opticsbook.pdf"
SOURCE_ID = "pdf_002_diagrams"

def extract_and_embed_diagrams(max_pages=20):
    print("Registering diagram source in Supabase...")
    supabase.table("sources").upsert({
        "id": SOURCE_ID,
        "title": "Optics Textbook Figures & Diagrams",
        "modality": "image"
    }).execute()

    doc = pymupdf.open(PDF_FILE)
    print(f"Scanning {PDF_FILE} (first {max_pages} pages) for diagrams and figures...")
    found_diagrams = 0

    for page_num in range(min(max_pages, len(doc))):
        page_idx = page_num + 1
        page = doc[page_num]
        images = page.get_images(full=True)

        for img_idx, img_info in enumerate(images):
            xref = img_info[0]
            raw_img = doc.extract_image(xref)
            width, height = raw_img["width"], raw_img["height"]

            # Ignore small icons or dividers
            if width < 120 or height < 120:
                continue

            found_diagrams += 1
            print(f"Found diagram #{found_diagrams} on page {page_idx} ({width}x{height}px)")

            img_bytes = raw_img["image"]
            ext = raw_img["ext"]
            filename = f"diagram_p{page_idx}_img{img_idx}.{ext}"
            saved_path = os.path.join(DIAGRAMS_DIR, filename)
            rel_path = f"assets/diagrams/{filename}"

            with open(saved_path, "wb") as f:
                f.write(img_bytes)

            try:

                vision_resp = client.models.generate_content(
                    model=GEMINI_FLASH_MODEL,
                    contents=[
                        "Analyze this physics diagram from an optics textbook. "
                        "Identify the rays, angles, optical boundaries, and physical laws shown "
                        "(e.g., Snell's Law, reflection, refraction, Brewster's angle, or polarization). "
                        "Explain what physical behavior it illustrates so a student can search for it.",
                        types.Part.from_bytes(data=img_bytes, mime_type=f"image/{ext}")
                    ]
                )
                diagram_description = vision_resp.text.strip()

                embed_resp = client.models.embed_content(
                    model=GEMINI_EMBEDDING_MODEL,
                    contents=f"[DIAGRAM on Page {page_idx}]: {diagram_description}",
                    config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM)
                )
                embedding = embed_resp.embeddings[0].values

                chunk_id = f"{SOURCE_ID}_p{page_idx}_d{img_idx}"
                supabase.table("chunks").upsert({
                    "id": chunk_id,
                    "source_id": SOURCE_ID,
                    "modality": "image",
                    "text": f"[DIAGRAM DESCRIPTION (Page {page_idx})]: {diagram_description}",
                    "page": page_idx,
                    "image_ref": rel_path,
                    "embedding": embedding
                }).execute()

                print(f"  Saved diagram chunk {chunk_id}")
                time.sleep(1)

            except Exception as err:
                print(f"  [!] Failed to process diagram on page {page_idx}: {err}")
                time.sleep(2)

    print(f"Diagram extraction done ({found_diagrams} diagrams processed).")

if __name__ == "__main__":
    extract_and_embed_diagrams(max_pages=20)