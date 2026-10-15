import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env")

supabase = create_client(url, key)

try:
    response = (
        supabase.table("chunks")
        .select("id, text, page")
        .limit(3)
        .execute()
    )

    print("Connection successful!")
    print(f"Rows retrieved: {len(response.data)}")

    for row in response.data:
        print(
            f"ID: {row.get('id')}, "
            f"Page: {row.get('page')}, "
            f"Text: {str(row.get('text', ''))[:100]}"
        )

except Exception as error:
    print("Connection or table access failed.")
    print(type(error).__name__, str(error))