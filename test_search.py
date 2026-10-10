import os
from dotenv import load_dotenv
from supabase import create_client,Client
from google import genai
from google.genai import types
load_dotenv()
supabase : Client =create_client(os.getenv("SUPABASE_URL"),os.getenv("SUPABASE_KEY"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
user_question = "What is the definition of light wave?"
print(f"Question: {user_question}")
response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=user_question,
    config=types.EmbedContentConfig(output_dimensionality=1000)
)
question_vector = response.embeddings[0].values
print("Searching database....")
result = supabase.rpc(
    "match_chunks",
    {
        "query_embedding": question_vector,
        "match_threshold": 0.5,
        "match_count": 3
    }
).execute()
for i , match in enumerate(result.data):
    print(f"\n---- Match {i+1} (Score: {match['similarity']:.2f}) ----")
    print(f"Page: {match['page']}")
    print(f"Text: {match['text'][:200]}.....")