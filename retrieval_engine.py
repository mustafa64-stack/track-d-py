import os
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai
from google.genai import types

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def ask_tutor(user_question):
    """
    Member A's core retrieval pipeline.
    Embeds the question, searches Supabase, and forces a cited response.
    """
    resp = client.models.embed_content(
        model="gemini-embedding-001", 
        contents=user_question,
        config=types.EmbedContentConfig(output_dimensionality=1000)
    )
    vector = resp.embeddings[0].values

    matches = supabase.rpc("match_chunks", {
        "query_embedding": vector, 
        "match_threshold": 0.5,
        "match_count": 3
    }).execute().data

    if not matches:
        return "I cannot answer this. This concept is not covered in your uploaded course materials.", []

 
    context = "\n\n".join([f"Page {m['page']}: {m['text']}" for m in matches])
    prompt = f"""
    You are an AI study companion. Answer the question using ONLY the context provided below. 
    You must cite the source inline like [Page X] immediately after the relevant sentence.
    If the context does not contain the answer, say "I don't know."
    
    Context:
    {context}
    
    Question: {user_question}
    """
    answer = client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt).text

    return answer, matches
