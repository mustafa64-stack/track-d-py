
import os
from pathlib import Path
from collections import Counter

from dotenv import load_dotenv
from supabase import create_client

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise SystemExit("Missing Supabase credentials in .env")

db = create_client(url, key)

response = (
    db.table("chunks")
    .select("id, topic_id")
    .not_.is_("text", "null")
    .execute()
)

rows = response.data or []
counts = Counter(
    "NULL" if row.get("topic_id") is None else "ASSIGNED"
    for row in rows
)

print("Chunks checked:", len(rows))
print("Chunks with topic IDs:", counts["ASSIGNED"])
print("Chunks with NULL topic IDs:", counts["NULL"])

print("\nSample mappings:")
for row in rows[:10]:
    print(f"{row['id']} -> {row.get('topic_id')}")

if counts["ASSIGNED"] == 0:
    print("\nStatus: No topic IDs are assigned yet.")
elif counts["NULL"] > 0:
    print("\nStatus: Mapping is partially complete.")
else:
    print("\nStatus: All retrieved chunks have topic IDs.")
