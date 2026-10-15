import json
import math
import os

from dotenv import load_dotenv

from question_generator import generate_questions
from question_verifier import verify_question
from question_deduplicator import (
    deduplicate_questions,
    generate_question_hash,
)

load_dotenv()

EMBED_MODEL = "gemini-embedding-001"   # change if this model is unavailable for you
SIMILARITY_THRESHOLD = 0.85
NUMERIC_REL_TOL = 1e-2


# ---------- helpers ----------

def _to_float(value):
    text = str(value).strip().replace(",", "")
    try:
        return float(text)
    except ValueError:
        # accept values like "9.8 m/s^2" by reading the leading number
        number = ""
        for ch in text:
            if ch in "+-.0123456789eE":
                number += ch
            else:
                break
        return float(number)


def _answers_match(expected: str, actual: str, question_type: str) -> bool:
    """Python-based answer check: tolerance for numerical, normalised text otherwise."""
    if str(question_type).lower() in ("numerical", "numeric"):
        try:
            return math.isclose(
                _to_float(expected), _to_float(actual),
                rel_tol=NUMERIC_REL_TOL, abs_tol=1e-6,
            )
        except ValueError:
            pass  # not parseable: fall back to text comparison
    return str(expected).strip().lower() == str(actual).strip().lower()


def _question_text(question: dict) -> str:
    options = question.get("options") or ""
    return f"{question.get('stem', '')} {options}"


def _cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def _embed_texts(texts):
    from google import genai

    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("No Gemini API key found in environment.")
    client = genai.Client(api_key=key)
    response = client.models.embed_content(model=EMBED_MODEL, contents=texts)
    return [list(e.values) for e in response.embeddings]


def _load_store(path):
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("hashes", [])), list(data.get("embeddings", []))
    return set(), []


def _save_store(path, hashes, embeddings):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"hashes": sorted(hashes), "embeddings": embeddings}, f)


# ---------- pipeline ----------

def run_assessment_pipeline(
    context: str,
    topic: str,
    topic_id: str,
    source_ref: str,
    question_type: str = "MCQ",
    difficulty: str = "easy",
    count: int = 3,
    existing_hashes: set[str] | None = None,
    existing_embeddings: list[list[float]] | None = None,
    store_path: str | None = None,
    max_attempts: int = 3,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
    embed_fn=None,
) -> dict:
    """
    Generate, verify and deduplicate assessment questions.

    - Regenerates only the missing questions, up to max_attempts rounds.
    - Rejects exact duplicates (hash) and near-duplicates (embedding cosine).
    - If store_path is given, hashes and embeddings persist between runs, so
      questions never repeat across assessments.
    """

    if not context.strip():
        raise ValueError("Study material cannot be empty.")

    known_hashes = set(existing_hashes or set())
    known_embeddings = list(existing_embeddings or [])
    stored_hashes, stored_embeddings = _load_store(store_path)
    known_hashes |= stored_hashes
    known_embeddings.extend(stored_embeddings)

    embed = embed_fn or _embed_texts
    embeddings_ok = True

    accepted: list[dict] = []
    rejected: list[dict] = []
    generated_total = 0
    verified_total = 0
    attempts = 0

    while len(accepted) < count and attempts < max_attempts:
        attempts += 1
        needed = count - len(accepted)
        print(f"\nAttempt {attempts}/{max_attempts}: generating {needed} question(s)...")

        candidates = generate_questions(
            context=context,
            topic=topic,
            topic_id=topic_id,
            question_type=question_type,
            difficulty=difficulty,
            count=needed,
        )
        generated_total += len(candidates)

        # ---- verification ----
        verified = []
        for index, question in enumerate(candidates, start=1):
            print(f"Verifying question {index}/{len(candidates)}...")
            question.setdefault("topic_id", topic_id)
            question.setdefault("source_ref", source_ref)

            try:
                result = verify_question(
                    question=question,
                    context=context,
                    source_ref=source_ref,
                )
                question["verification_result"] = result

                passed = (
                    result["correct"] is True
                    and result["source_supported"] is True
                    and _answers_match(
                        result["expected_answer"], question["answer"], question_type
                    )
                )

                if passed:
                    question["verified"] = True
                    verified.append(question)
                else:
                    question["verified"] = False
                    question["rejection_reason"] = (
                        "Failed answer correctness or source-support checks."
                    )
                    rejected.append(question)

            except (ValueError, KeyError, TypeError) as exc:
                question["verified"] = False
                question["rejection_reason"] = str(exc)
                rejected.append(question)

        verified_total += len(verified)

        # ---- exact-duplicate removal (hash) ----
        unique, duplicates = deduplicate_questions(
            verified, existing_hashes=known_hashes
        )
        for question in duplicates:
            question["verified"] = False
            question["rejection_reason"] = "Duplicate question detected."
            rejected.append(question)

        for question in unique:
            question["hash"] = generate_question_hash(question)

        # ---- near-duplicate removal (embeddings) ----
        vectors = []
        if unique and embeddings_ok:
            try:
                vectors = embed([_question_text(q) for q in unique])
            except Exception as exc:  # network, key, model name...
                embeddings_ok = False
                print(f"Embedding check skipped ({exc}). Using hash-only dedup.")

        for i, question in enumerate(unique):
            if embeddings_ok and vectors:
                vector = vectors[i]
                similarity = max(
                    (_cosine(vector, old) for old in known_embeddings), default=0.0
                )
                if similarity >= similarity_threshold:
                    question["verified"] = False
                    question["rejection_reason"] = (
                        f"Too similar to an earlier question (cosine {similarity:.2f})."
                    )
                    rejected.append(question)
                    continue
                question["embedding"] = vector
                known_embeddings.append(vector)

            known_hashes.add(question["hash"])
            accepted.append(question)

        print(f"Accepted so far: {len(accepted)}/{count}")

    if store_path and accepted:
        _save_store(store_path, known_hashes, known_embeddings)

    print(f"\nAccepted unique questions: {len(accepted)}")
    print(f"Total rejected questions: {len(rejected)}")

    return {
        "questions": accepted,
        "rejected": rejected,
        "stats": {
            "generated": generated_total,
            "verified_before_deduplication": verified_total,
            "accepted": len(accepted),
            "rejected": len(rejected),
            "attempts": attempts,
            "embedding_dedup": embeddings_ok,
        },
    }