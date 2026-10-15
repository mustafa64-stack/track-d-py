
import json
from pathlib import Path

path = Path(__file__).resolve().parent / "topic_tree.json"

with path.open("r", encoding="utf-8") as file:
    tree = json.load(file)

topics = tree.get("topics", [])
topic_ids = [topic.get("topic_id") for topic in topics]
valid_ids = set(topic_ids)

print("JSON file: valid")
print("Chunks processed:", tree.get("chunks_processed"))
print("Number of topics:", len(topics))
print("Duplicate topic IDs:", len(topic_ids) - len(valid_ids))

missing_names = [
    topic.get("topic_id")
    for topic in topics
    if not topic.get("name")
]
print("Topics missing names:", missing_names)

bad_prerequisites = []
for topic in topics:
    for prerequisite in topic.get("prerequisites", []):
        if prerequisite not in valid_ids:
            bad_prerequisites.append(
                (topic.get("topic_id"), prerequisite)
            )

print("Invalid prerequisite references:", bad_prerequisites)

bad_source_refs = []
for topic in topics:
    for ref in topic.get("source_refs", []):
        if not isinstance(ref, dict):
            bad_source_refs.append(
                (topic.get("topic_id"), ref)
            )
        elif "chunk_id" not in ref or "page" not in ref:
            bad_source_refs.append(
                (topic.get("topic_id"), ref)
            )

print("Malformed topic-level source references:", bad_source_refs)

print("\nValidation finished.")
