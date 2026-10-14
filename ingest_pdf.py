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
    GEMINI_EMBEDDING_MODEL,
    EMBEDDING_DIM,
    PAGES_DIR
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

PDF_FILE = "opticsbook.pdf"
SOURCE_ID = "pdf_001"

def ingest_pdf(max_pages=50):
    print("Registering PDF source in Supabase...")
    supabase.table("sources").upsert({
        "id": SOURCE_ID,
        "title": "Optics Textbook",
        "modality": "pdf"
    }).execute()

    doc = pymupdf.open(PDF_FILE)
    total_pages = min(max_pages, len(doc))
    print(f"Reading {PDF_FILE} (processing first {total_pages} of {len(doc)} pages)...")

    for i in range(total_pages):
        page_idx = i + 1
        page = doc[i]
        try:
            text = page.get_text().strip()
            if not text:
                continue
            page_rel_path = f"assets/pages/page_{page_idx}.png"
            page_full_path = os.path.join(PAGES_DIR, f"page_{page_idx}.png")
            if not os.path.exists(page_full_path):
                pix = page.get_pixmap(dpi=150)
                pix.save(page_full_path)
            resp = client.models.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM)
            )
            embedding = resp.embeddings[0].values

            chunk_id = f"{SOURCE_ID}_p{page_idx}"
            supabase.table("chunks").upsert({
                "id": chunk_id,
                "source_id": SOURCE_ID,
                "modality": "pdf",
                "text": text,
                "page": page_idx,
                "image_ref": page_rel_path,
                "embedding": embedding
            }).execute()

            print(f"  [{page_idx}/{total_pages}] Saved chunk & preview for page {page_idx}")
            time.sleep(1)

        except Exception as err:
            print(f"  [!] Skipped page {page_idx} due to error: {err}")
            time.sleep(2)

    print("Finished ingesting PDF pages.")

if __name__ == "__main__":
    ingest_pdf(max_pages=50)