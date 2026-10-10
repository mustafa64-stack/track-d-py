import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai
from google.genai import types
from youtube_transcript_api import YouTubeTranscriptApi
load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
def ingest_video(video_id):
    """Member A's video parser. Chunks transcripts by timestamp."""
    source_id = f"yt_{video_id}"
    supabase.table("sources").upsert({
        "id": source_id, "title": "Lecture Video", "modality": "youtube"
    }).execute()
    transcript = YouTubeTranscriptApi().fetch(video_id).to_raw_data()
    chunk_text = ""
    start_time = transcript[0]['start']
    chunk_count = 1
    for i, line in enumerate(transcript):
        chunk_text += line['text'] + " "
        end_time = line['start'] + line['duration']
        if (end_time - start_time >= 30) or (i == len(transcript) - 1):
            resp = client.models.embed_content(
                model="gemini-embedding-001", contents=chunk_text.strip(),
                config=types.EmbedContentConfig(output_dimensionality=1000)
            )
            
            supabase.table("chunks").upsert({
                "id": f"{source_id}_c{chunk_count}",
                "source_id": source_id,
                "modality": "youtube",
                "text": chunk_text.strip(),
                "start_sec": float(start_time),
                "end_sec": float(end_time),
                "embedding": resp.embeddings[0].values
            }).execute()
            chunk_text = ""
            if i + 1 < len(transcript): start_time = transcript[i+1]['start']
            chunk_count += 1
            time.sleep(3)
