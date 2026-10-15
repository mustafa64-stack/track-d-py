import os
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai
from google.genai import types
from config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    GEMINI_API_KEY,
    GEMINI_FLASH_MODEL,
    GEMINI_EMBEDDING_MODEL,
    EMBEDDING_DIM,
    DEFAULT_MATCH_COUNT,
    DEFAULT_SIMILARITY_THRESHOLD,
    REFUSAL_SIMILARITY_THRESHOLD
)

load_dotenv()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(timeout=30.0)
)


def seconds_to_str(seconds: float) -> str:
    """Format seconds into MM:SS for readable video timestamps."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def build_citation(chunk: dict) -> dict:
    """
    Build user-friendly citation metadata so Streamlit can render
    clickable chips opening the exact page, slide, or video timestamp.
    """
    modality = chunk.get("modality", "text")
    chunk_id = chunk.get("id", "")
    page = chunk.get("page")
    slide = chunk.get("slide")
    start_sec = chunk.get("start_sec")
    end_sec = chunk.get("end_sec")
    image_ref = chunk.get("image_ref")

    if modality == "pdf":
        label = f"PDF Page {page}" if page else "Textbook Page"
        location = f"Page {page}" if page else ""
        link_or_file = f"assets/pages/page_{page}.png" if page else ""
    elif modality == "slide":
        label = f"Slide {slide}" if slide else "Slide Deck"
        location = f"Slide {slide}" if slide else ""
        link_or_file = image_ref or (f"assets/slides/slide_{slide}.png" if slide else "")
    elif modality == "youtube":
        start_fmt = seconds_to_str(start_sec or 0)
        end_fmt = seconds_to_str(end_sec or 0)
        label = f"Video [{start_fmt} - {end_fmt}]"
        location = f"{start_fmt}"
        link_or_file = image_ref or f"https://youtube.com?t={int(start_sec or 0)}s"
    elif modality == "image":
        label = f"Diagram (Page {page})" if page else "Figure / Diagram"
        location = f"Page {page}" if page else ""
        link_or_file = image_ref or ""
    else:
        label = f"Source ({modality})"
        location = ""
        link_or_file = ""

    return {
        "chunk_id": chunk_id,
        "modality": modality,
        "label": label,
        "location": location,
        "link_or_file": link_or_file,
        "snippet": chunk.get("text", "")[:150].replace("\n", " ") + "...",
        "similarity": float(chunk.get("similarity", 0.0))
    }

def enrich_chunks_with_metadata(match_records: List[dict]) -> List[dict]:
    """
    Makes sure slide, start_sec, and image_ref are always populated,
    even if an earlier match_chunks SQL definition returned fewer columns.
    """
    if not match_records:
        return []

    sample = match_records[0]
    if "slide" in sample and "start_sec" in sample and "image_ref" in sample:
        return match_records

    chunk_ids = [m["id"] for m in match_records]
    sim_scores = {m["id"]: m.get("similarity", 0.0) for m in match_records}

    try:
        res = supabase.table("chunks").select(
            "id, source_id, modality, text, page, slide, start_sec, end_sec, topic_id, image_ref"
        ).in_("id", chunk_ids).execute()
        
        data = res.data or []
        by_id = {row["id"]: row for row in data}

        enriched = []
        for cid in chunk_ids:
            if cid in by_id:
                item = by_id[cid]
                item["similarity"] = sim_scores.get(cid, 0.0)
                enriched.append(item)
        return enriched
    except Exception:
        return match_records

def retrieve_chunks(
    query: str,
    match_count: int = DEFAULT_MATCH_COUNT,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    filter_topic_id: Optional[str] = None
) -> List[dict]:
    """Embed question and search Supabase vector store."""
    resp = client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=query,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM)
    )
    query_vector = resp.embeddings[0].values

    params = {
        "query_embedding": query_vector,
        "match_threshold": threshold,
        "match_count": match_count
    }
    if filter_topic_id:
        params["filter_topic_id"] = filter_topic_id

    try:
        rpc_res = supabase.rpc("match_chunks", params).execute()
        raw_matches = rpc_res.data or []
    except Exception:
        params.pop("filter_topic_id", None)
        rpc_res = supabase.rpc("match_chunks", params).execute()
        raw_matches = rpc_res.data or []

    return enrich_chunks_with_metadata(raw_matches)

def ask_tutor(
    user_question: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    filter_topic_id: Optional[str] = None,
    top_k: int = DEFAULT_MATCH_COUNT
) -> Tuple[str, List[dict], List[dict]]:
    """
    Main grounded chat pipeline.
    Finds chunks, validates confidence, and asks Gemini to cite sources.
    Refuses if the topic is not found in the course materials.
    """
    matches = retrieve_chunks(
        query=user_question,
        match_count=top_k,
        threshold=DEFAULT_SIMILARITY_THRESHOLD,
        filter_topic_id=filter_topic_id
    )

    if not matches:
        return "I cannot answer this. This concept is not covered in your uploaded course materials.", [], []

    best_score = max(m.get("similarity", 0.0) for m in matches)
    if best_score < REFUSAL_SIMILARITY_THRESHOLD:
        msg = "I cannot answer this. This concept is not covered in your uploaded course materials."
        return msg, [], matches

    context_chunks = []
    citations = []

    for idx, chunk in enumerate(matches):
        cite_num = idx + 1
        meta = build_citation(chunk)
        meta["citation_index"] = cite_num
        citations.append(meta)

        tag = f"[Source #{cite_num} | {meta['label']} | ID: {chunk.get('id')}]"
        context_chunks.append(f"{tag}\n{chunk.get('text', '').strip()}")

    full_context = "\n\n--------------------\n\n".join(context_chunks)

    # Conversation history snippet if available
    history_snippet = ""
    if chat_history:
        lines = []
        for turn in chat_history[-4:]:
            speaker = "Student" if turn.get("role") == "user" else "Tutor"
            lines.append(f"{speaker}: {turn.get('text', '')}")
        history_snippet = "Recent Conversation:\n" + "\n".join(lines) + "\n\n"

    system_rules = """
You are a friendly, rigorous AI study tutor for university students.
Answer the student's question using ONLY the provided course excerpts.

Rules:
1. Ground every claim directly in the excerpts below.
2. Put inline citation numbers like [1] or [2] right after the sentence or fact.
3. If multiple sources agree, cite them both like [1, 2].
4. If the excerpts do not contain the answer, say:
   "I cannot answer this. This concept is not covered in your uploaded course materials."
5. If extra background is needed to make sense of the question, clearly prefix it with:
   "[Outside Knowledge]: <brief note>".
6. When referring to figures or ray tracings, mention the diagram details.
"""

    prompt = f"""{system_rules}

{history_snippet}Course Materials:
{full_context}

Question: {user_question}

Grounded Explanation:"""

    candidate_models = [GEMINI_FLASH_MODEL]
    for alt in ["gemini-flash-lite-latest", "gemini-flash-latest"]:
        if alt not in candidate_models:
            candidate_models.append(alt)

    answer = None
    last_err = None
    for m in candidate_models:
        try:
            response = client.models.generate_content(
                model=m,
                contents=prompt
            )
            if response.text and response.text.strip():
                answer = response.text.strip()
                break
        except Exception as err:
            last_err = err
            continue

    if not answer:
        answer = f"Error generating answer: {last_err}"
        return answer, [], matches

    # If tutor refused because the topic is not covered, clear citations
    if "cannot answer this" in answer.lower():
        citations = []

    return answer, citations, matches


def get_chunks_for_topic(topic_id: str, limit: int = 5) -> List[dict]:
    """Fetch source chunks for a specific topic so Member B can generate weak-topic questions."""
    res = supabase.table("chunks").select(
        "id, source_id, modality, text, page, slide, start_sec, end_sec, topic_id, image_ref"
    ).eq("topic_id", topic_id).limit(limit).execute()
    return res.data or []


def get_all_topics() -> List[dict]:
    """List all registered topics in the database."""
    res = supabase.table("topics").select("*").execute()
    return res.data or []
