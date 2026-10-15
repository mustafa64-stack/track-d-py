
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
INPUT_FILE = BASE / "topic_tree.json"
OUTPUT_FILE = BASE / "topic_tree.json"

with INPUT_FILE.open("r", encoding="utf-8") as file:
    tree = json.load(file)

converted = 0
unmatched = []

for topic in tree.get("topics", []):
    for concept in topic.get("key_concepts", []):
        refs = concept.get("source_refs", [])

        if not isinstance(refs, list):
            unmatched.append((topic.get("topic_id"), refs))
            continue

        new_refs = []

        for ref in refs:
            if isinstance(ref, dict):
                new_refs.append(ref)
                continue

            if not isinstance(ref, str):
                unmatched.append((topic.get("topic_id"), ref))
                continue

            match = re.search(
                r"(.+?),\s*page\s*(\d+)",
                ref,
                flags=re.IGNORECASE,
            )

            if match:
                new_refs.append({
                    "chunk_id": match.group(1).strip(),
                    "page": int(match.group(2)),
                })
                converted += 1
            else:
                unmatched.append((topic.get("topic_id"), ref))
                new_refs.append(ref)

        concept["source_refs"] = new_refs

backup = BASE / "topic_tree.before_reference_fix.json"
backup.write_text(
    json.dumps(tree, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

OUTPUT_FILE.write_text(
    json.dumps(tree, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

print("Reference conversion finished.")
print("References converted:", converted)
print("References needing manual review:", len(unmatched))

for topic_id, ref in unmatched[:10]:
    print(f"Review {topic_id}: {ref}")

print("Backup saved to:", backup.name)
print("Updated:", OUTPUT_FILE.name)
