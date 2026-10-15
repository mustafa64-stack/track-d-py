"""
Sync topic_tree.json into Supabase topics and prerequisites tables,
and update chunks with their assigned topic_ids.
"""
import json
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

load_dotenv()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE = Path(__file__).resolve().parent

def sync_topics_to_supabase():
    tree_path = BASE / "topic_tree.json"
    if not tree_path.exists():
        print("topic_tree.json not found!")
        return

    with open(tree_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    topics = data.get("topics", [])
    print(f"Loaded {len(topics)} topics from topic_tree.json.")

    # 1. Upsert all topics
    topic_rows = []
    prereq_rows = []

    for t in topics:
        tid = t.get("topic_id")
        name = t.get("name", tid)
        if not tid:
            continue
        topic_rows.append({
            "id": tid,
            "name": name,
            "parent_id": None
        })

    print(f"Upserting {len(topic_rows)} topics to Supabase...")
    for row in topic_rows:
        supabase.table("topics").upsert(row).execute()
    print("Topics successfully synced.")

    # 2. Upsert prerequisites edges
    for t in topics:
        tid = t.get("topic_id")
        for prereq in t.get("prerequisites", []):
            if prereq and prereq != tid:
                prereq_rows.append({
                    "topic_id": tid,
                    "prereq_id": prereq
                })

    print(f"Upserting {len(prereq_rows)} prerequisites edges to Supabase...")
    for edge in prereq_rows:
        try:
            supabase.table("prerequisites").upsert(edge).execute()
        except Exception as e:
            print(f"Edge {edge['topic_id']} -> {edge['prereq_id']} error: {e}")
    print("Prerequisites successfully synced.")

    # 3. Update chunks with mapped topic_ids from source_refs
    mapped_count = 0
    for t in topics:
        tid = t.get("topic_id")
        for ref in t.get("source_refs", []):
            if isinstance(ref, dict) and "chunk_id" in ref:
                cid = ref["chunk_id"]
                try:
                    supabase.table("chunks").update({"topic_id": tid}).eq("id", cid).execute()
                    mapped_count += 1
                except Exception as e:
                    pass
    print(f"Updated {mapped_count} chunk topic references in Supabase.")

if __name__ == "__main__":
    sync_topics_to_supabase()
