
import json
from pathlib import Path
from collections import Counter

from dotenv import load_dotenv
from supabase import create_client

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

url = __import__("os").getenv("SUPABASE_URL")
key = __import__("os").getenv("SUPABASE_KEY")

if not url or not key:
    raise SystemExit("Missing Supabase credentials in .env")

db = create_client(url, key)

with (BASE / "topic_tree.json").open(encoding="utf-8") as file:
    tree = json.load(file)

topics = tree.get("topics", [])
topic_ids = {topic["topic_id"] for topic in topics}

# Map source chunk IDs to topics using the tree's topic-level references.
chunk_topics = {}

for topic in topics:
    for ref in topic.get("source_refs", []):
        if not isinstance(ref, dict):
            continue

        chunk_id = ref.get("chunk_id")
        if chunk_id is None:
            continue

        chunk_id = str(chunk_id)
        chunk_topics.setdefault(chunk_id, [])

        if topic["topic_id"] not in chunk_topics[chunk_id]:
            chunk_topics[chunk_id].append(topic["topic_id"])

response = (
    db.table("chunks")
    .select("id, text, page, topic_id")
    .not_.is_("text", "null")
    .execute()
)

chunks = [
    row for row in (response.data or [])
    if isinstance(row.get("text"), str) and row["text"].strip()
]

proposals = []
unmatched = []
ambiguous = []

for chunk in chunks:
    chunk_id = str(chunk["id"])
    candidates = chunk_topics.get(chunk_id, [])

    if len(candidates) == 1:
        proposals.append({
            "chunk_id": chunk_id,
            "page": chunk.get("page"),
            "proposed_topic_id": candidates[0],
            "status": "proposed",
        })
    elif len(candidates) == 0:
        unmatched.append(chunk_id)
    else:
        ambiguous.append({
            "chunk_id": chunk_id,
            "candidate_topic_ids": candidates,
        })

output = {
    "chunks_checked": len(chunks),
    "topics_available": len(topic_ids),
    "proposals": proposals,
    "unmatched_chunk_ids": unmatched,
    "ambiguous_chunks": ambiguous,
}

output_path = BASE / "chunk_topic_mapping.json"
output_path.write_text(
    json.dumps(output, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

print("Chunks checked:", len(chunks))
print("Unambiguous proposals:", len(proposals))
print("Unmatched chunks:", len(unmatched))
print("Ambiguous chunks:", len(ambiguous))
print("Saved proposals to:", output_path.name)

if unmatched:
    print("\nUnmatched chunk IDs:")
    print(", ".join(unmatched))

if ambiguous:
    print("\nAmbiguous mappings:")
    for item in ambiguous:
        print(item["chunk_id"], "->", item["candidate_topic_ids"])

print("\nNo database rows were modified.")
