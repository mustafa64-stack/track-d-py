
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parent / ".env")

db = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

result = (
    db.table("chunks")
    .select("id, page, text")
    .order("id")
    .limit(200)
    .execute()
)

rows = result.data
pages = sorted({
    row["page"] for row in rows
    if row.get("page") is not None
})

print(f"Chunks retrieved: {len(rows)}")
print(f"Distinct page numbers: {len(pages)}")
print(f"Page range: {min(pages)} to {max(pages)}" if pages else "No page numbers")

print("\nSample of available material:")
for row in rows[:8]:
    text = (row.get("text") or "").replace("\n", " ")
    print(f"\nPage {row.get('page')} | {row['id']}")
    print(text[:180])
