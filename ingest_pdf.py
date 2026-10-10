import os
import pymupdf
import time
from dotenv import load_dotenv
from supabase import create_client,Client
from google import genai
from google.genai import types
load_dotenv()
supabase: Client=create_client(os.getenv("SUPABASE_URL"),os.getenv("SUPABASE_KEY"))
client=genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
pdf_path="opticsbook.pdf"
source_id="pdf_001"
print("Registering pdf in database....")
supabase.table("sources").upsert({
    "id":source_id,
    "title":"Sample guide",
    "modality":"pdf"
}).execute()
doc=pymupdf.open(pdf_path)
print(f"Opened {pdf_path}. Total pages: {len(doc)}")
for page_num in range(50):
    try:
        text=doc[page_num].get_text().strip()
        if not text:
            continue
        print(f"Processing page {page_num + 1}...")
        response=client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=1000)
        )
        embedding=response.embeddings[0].values
        chunk_id=f"{source_id}_p{page_num+1}"
        supabase.table("chunks").upsert({
            "id":chunk_id,
            "source_id":source_id,
            "modality":"pdf",
            "text":text,
            "page":page_num+1,
            "embedding":embedding
        }).execute()
        time.sleep(3)
    except Exception as e:
        print(f"-------Network blip on page {page_num + 1},skipping! Error: {e}-----------")
        time.sleep(3)
print("Success!Pdf text and embeddings are saved in Supabase.")