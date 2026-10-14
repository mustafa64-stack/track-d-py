import os
import time
from supabase import create_client, Client
from google import genai
from google.genai import types
from youtube_transcript_api import YouTubeTranscriptApi
from config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    GEMINI_API_KEY,
    GEMINI_EMBEDDING_MODEL,
    EMBEDDING_DIM
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

# Fallback transcript in case YouTube blocks or rate limits during live demo
DEMO_LECTURE_TRANSCRIPT = [
    {"start": 0.0, "duration": 25.0, "text": "Welcome to our lecture on Optics. Today we begin with the fundamental nature of light as an electromagnetic wave traveling through space."},
    {"start": 25.0, "duration": 30.0, "text": "In vacuum, electromagnetic waves travel at the universal constant c, 3 times 10 to the 8 meters per second, consisting of mutually perpendicular oscillating electric and magnetic fields."},
    {"start": 55.0, "duration": 35.0, "text": "When light encounters a boundary between two transparent dielectric media, two simultaneous phenomena occur: reflection and refraction."},
    {"start": 90.0, "duration": 35.0, "text": "The law of reflection states that the angle of incidence theta i equals the angle of reflection theta r, both measured with respect to the surface normal."},
    {"start": 125.0, "duration": 40.0, "text": "Refraction is governed by Snell's Law, which states that n1 times the sine of theta 1 equals n2 times the sine of theta 2, where n is the refractive index c over v."},
    {"start": 165.0, "duration": 45.0, "text": "When light travels from a denser medium to a rarer medium, n1 greater than n2, the refracted ray bends away from the normal. At a specific angle called the critical angle, theta 2 becomes 90 degrees."},
    {"start": 210.0, "duration": 40.0, "text": "For any angle of incidence greater than the critical angle, all energy is reflected back into the denser medium. This phenomenon is Total Internal Reflection, the principle behind fiber optics."},
    {"start": 250.0, "duration": 45.0, "text": "Next we consider polarization by reflection. At Brewster's angle, the reflected light is completely linearly polarized perpendicular to the plane of incidence, because the reflected and refracted rays are orthogonal."},
    {"start": 295.0, "duration": 50.0, "text": "According to Huygens' Principle, every point on a wavefront acts as a source of secondary wavelets. The envelope of these wavelets reconstructs the subsequent wavefront, explaining diffraction and interference."},
    {"start": 345.0, "duration": 45.0, "text": "In thin films, interference between rays reflected from top and bottom surfaces produces vibrant fringes, as seen in soap bubbles and anti-reflection optical lens coatings."}
]

def ingest_video(video_id="fD1544bM_c4"):
    """
    Downloads transcript, slices it into 30-45s chunks with timestamps,
    and uploads vectors to Supabase with deep-link URLs.
    """
    source_id = f"yt_{video_id}"
    print(f"Registering video {video_id} in Supabase...")
    supabase.table("sources").upsert({
        "id": source_id,
        "title": "Optics Lecture: Reflection and Wave Optics",
        "modality": "youtube"
    }).execute()

    transcript_items = []
    try:
        print(f"Fetching transcript from YouTube ({video_id})...")
        transcript_items = YouTubeTranscriptApi().fetch(video_id).to_raw_data()
        print(f"Got {len(transcript_items)} lines from YouTube.")
    except Exception as err:
        print(f"Live fetch unavailable ({err}), falling back to local lecture transcript.")
        transcript_items = DEMO_LECTURE_TRANSCRIPT

    chunk_text = ""
    start_time = transcript_items[0]['start']
    chunk_count = 1

    for i, line in enumerate(transcript_items):
        chunk_text += line['text'] + " "
        end_time = line['start'] + line['duration']

        # Slice roughly every 35 seconds or at the very end
        if (end_time - start_time >= 35) or (i == len(transcript_items) - 1):
            content = chunk_text.strip()
            print(f"  Embedding chunk {chunk_count}: [{int(start_time)}s - {int(end_time)}s]")

            try:
                resp = client.models.embed_content(
                    model=GEMINI_EMBEDDING_MODEL,
                    contents=f"[LECTURE VIDEO {video_id} ({int(start_time)}s-{int(end_time)}s)]: {content}",
                    config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM)
                )

                chunk_id = f"{source_id}_c{chunk_count}"
                supabase.table("chunks").upsert({
                    "id": chunk_id,
                    "source_id": source_id,
                    "modality": "youtube",
                    "text": content,
                    "start_sec": float(start_time),
                    "end_sec": float(end_time),
                    "image_ref": f"https://www.youtube.com/watch?v={video_id}&t={int(start_time)}s",
                    "embedding": resp.embeddings[0].values
                }).execute()

                chunk_count += 1
                time.sleep(1)

            except Exception as embed_err:
                print(f"  [!] Failed to embed chunk {chunk_count}: {embed_err}")
                time.sleep(2)

            chunk_text = ""
            if i + 1 < len(transcript_items):
                start_time = transcript_items[i + 1]['start']

    print(f"Video ingestion complete ({chunk_count - 1} chunks saved).")

if __name__ == "__main__":
    ingest_video()
