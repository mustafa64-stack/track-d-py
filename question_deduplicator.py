
import hashlib
import re
import unicodedata


def normalize_text(text: str) -> str:
    """Normalize text so simple formatting differences don't matter."""
    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def generate_question_hash(question: dict) -> str:
    """Generate a stable hash for a question's content."""

    stem = question.get("stem", "")
    question_type = question.get("type", "")

    if not isinstance(stem, str) or not stem.strip():
        raise ValueError("Question stem cannot be empty.")

    if not isinstance(question_type, str) or not question_type.strip():
        raise ValueError("Question type cannot be empty.")

    # IDs, explanations and formatting are excluded deliberately.
    # Identical question stems of the same type get the same hash.
    content = (
        normalize_text(question_type)
        + "|"
        + normalize_text(stem)
    )

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def deduplicate_questions(
    questions: list[dict],
    existing_hashes: set[str] | None = None,
) -> tuple[list[dict], list[dict]]:
    """
    Return (unique_questions, duplicates).

    Existing hashes can represent questions already stored elsewhere.
    The first occurrence is kept; later duplicates are rejected.
    """

    seen = set(existing_hashes or set())
    unique_questions = []
    duplicates = []

    for question in questions:
        question_hash = generate_question_hash(question)
        question["hash"] = question_hash

        if question_hash in seen:
            duplicates.append(question)
            continue

        seen.add(question_hash)
        unique_questions.append(question)

    return unique_questions, duplicates
