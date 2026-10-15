
import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client
from google import genai
from google.genai import types

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY]):
    raise SystemExit("Missing credentials in your .env file.")

PROMPT_FILE = BASE / "concept_extraction_prompt.txt"
OUTPUT_FILE = BASE / "topic_tree.json"
BATCH_SIZE = 8

db = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)


def choose_model():
    print("Checking Gemini models available to your API key...")

    try:
        models = list(client.models.list())
    except Exception as error:
        raise SystemExit(
            f"Could not list Gemini models: {type(error).__name__}: {error}"
        )

    available = []

    for item in models:
        name = getattr(item, "name", None)
        actions = getattr(item, "supported_actions", None) or []

        if name and "generateContent" in actions:
            available.append(name)

    # Prefer the model explicitly recommended by the previous API error.
    preferences = [
        "gemini-3.5-flash",
        "gemini-3.8-flash",
        "gemini-3.1-flash",
        "gemini-2.5-flash",
    ]

    for preferred in preferences:
        for name in available:
            if name == preferred or name.endswith("/" + preferred):
                print("Selected available model:", name)
                return name

    flash_models = [
        name for name in available if "flash" in name.lower()
    ]

    if flash_models:
        print("Selected available Flash model:", flash_models[0])
        return flash_models[0]

    print("\nNo supported Flash model was found.")
    print("Models available for generateContent:")
    for name in available:
        print("-", name)

    raise SystemExit("Please check the available models listed above.")


def fetch_chunks():
    print("Retrieving chunks from Supabase...")
    rows = []
    start = 0

    while True:
        response = (
            db.table("chunks")
            .select(
                "id, source_id, modality, text, page, slide, "
                "start_sec, end_sec"
            )
            .not_.is_("text", "null")
            .order("id")
            .range(start, start + 999)
            .execute()
        )

        batch = response.data or []

        rows.extend(
            row for row in batch
            if isinstance(row.get("text"), str)
            and row["text"].strip()
        )

        if len(batch) < 1000:
            break

        start += 1000

    return rows


def parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def extract_batch(model, prompt_template, rows, batch_number, total):
    material = []

    for row in rows:
        material.append({
            "chunk_id": row["id"],
            "source_id": row.get("source_id"),
            "modality": row.get("modality"),
            "page": row.get("page"),
            "slide": row.get("slide"),
            "start_sec": row.get("start_sec"),
            "end_sec": row.get("end_sec"),
            "text": row["text"][:2000],
        })

    prompt = f"""
{prompt_template}

Batch {batch_number} of {total}.
Course: Physics of Light and Optics.

Extract only concepts supported by the supplied source material.
The material may cover only part of the course. Do not invent
concepts, source references, or prerequisite relationships.

Return valid JSON containing:
- course_name
- topics: a list of topic objects

Each topic must include:
- topic_id: unique snake_case identifier
- name
- description
- subtopics: list of strings
- key_concepts: list of objects containing concept_id, name,
  description, source_refs
- prerequisites: list of topic IDs, or [] if uncertain
- source_refs: list of objects containing chunk_id and page

Use exact chunk IDs and page numbers from the supplied material.
Return JSON only.

SOURCE MATERIAL:
{json.dumps(material, ensure_ascii=False)}
"""

    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response.")

            result = parse_json(response.text)

            if not isinstance(result.get("topics"), list):
                raise ValueError("Gemini response has no topics list.")

            return result["topics"]

        except Exception as error:
            print(
                f"Batch {batch_number}, attempt {attempt}: "
                f"{type(error).__name__}: {error}"
            )

            # A retired/unavailable model or invalid request will not
            # be fixed by retrying.
            message = str(error).lower()
            if any(term in message for term in [
                "not found", "not supported", "invalid argument",
                "permission denied", "unauthorized"
            ]):
                raise

            if attempt == 3:
                raise

            time.sleep(attempt * 3)


def merge_topics(items):
    merged = {}

    for item in items:
        topic_id = item.get("topic_id")

        if not isinstance(topic_id, str) or not topic_id.strip():
            continue

        if topic_id not in merged:
            merged[topic_id] = {
                "topic_id": topic_id,
                "name": item.get("name", topic_id),
                "description": item.get("description", ""),
                "subtopics": [],
                "key_concepts": [],
                "source_refs": [],
                "prerequisites": [],
            }

        target = merged[topic_id]

        for field in [
            "subtopics", "key_concepts",
            "source_refs", "prerequisites"
        ]:
            values = item.get(field, [])
            if not isinstance(values, list):
                continue

            for value in values:
                if value not in target[field]:
                    target[field].append(value)

        if not target["description"] and item.get("description"):
            target["description"] = item["description"]

    valid_ids = set(merged)

    for topic in merged.values():
        topic["prerequisites"] = [
            value for value in topic["prerequisites"]
            if isinstance(value, str)
            and value in valid_ids
            and value != topic["topic_id"]
        ]

    return list(merged.values())


def main():
    if not PROMPT_FILE.exists():
        raise SystemExit("concept_extraction_prompt.txt is missing.")

    model = choose_model()
    prompt_template = PROMPT_FILE.read_text(encoding="utf-8")
    rows = fetch_chunks()

    if not rows:
        raise SystemExit("No usable chunks found.")

    batches = [
        rows[i:i + BATCH_SIZE]
        for i in range(0, len(rows), BATCH_SIZE)
    ]

    print(f"Retrieved {len(rows)} chunks.")
    print(f"Processing {len(batches)} batches.")

    all_topics = []

    for index, batch in enumerate(batches, start=1):
        print(f"\nProcessing batch {index}/{len(batches)}...")

        new_topics = extract_batch(
            model, prompt_template, batch, index, len(batches)
        )

        all_topics.extend(new_topics)
        print("Topics collected so far:", len(all_topics))

    topics = merge_topics(all_topics)

    if not topics:
        raise SystemExit("No topics generated. Existing file preserved.")

    valid_chunk_ids = {str(row["id"]) for row in rows}
    unknown_refs = []

    for topic in topics:
        for ref in topic["source_refs"]:
            if not isinstance(ref, dict):
                continue

            chunk_id = ref.get("chunk_id")
            if (
                chunk_id is not None
                and str(chunk_id) not in valid_chunk_ids
            ):
                unknown_refs.append(str(chunk_id))

    output = {
        "course_name": "Physics of Light and Optics",
        "chunks_processed": len(rows),
        "topics": topics,
    }

    serialized = json.dumps(output, indent=2, ensure_ascii=False)
    json.loads(serialized)  # Validate before saving.

    # Preserve the existing output before replacing it.
    if OUTPUT_FILE.exists():
        backup = BASE / "topic_tree.previous.json"
        backup.write_text(
            OUTPUT_FILE.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        print("Previous topic tree backed up.")

    OUTPUT_FILE.write_text(serialized + "\n", encoding="utf-8")

    print("\nExtraction completed!")
    print("Chunks processed:", len(rows))
    print("Unique topics:", len(topics))
    print("Unknown source references:", len(unknown_refs))
    print("Saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\nExtraction stopped.")
        print(type(error).__name__ + ":", error)
        print("The previous topic tree has not been replaced.")
