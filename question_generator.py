
import json
import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors


load_dotenv()

from google.genai import types

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY was not found. Check your .env file."
    )

client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(timeout=60000)
)
MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-flash-lite-latest")
PROMPT_PATH = Path(__file__).parent / "question_generation_prompt.txt"


def generate_questions(
    context: str,
    topic: str,
    topic_id: str,
    question_type: str = "MCQ",
    difficulty: str = "easy",
    count: int = 3,
) -> list[dict]:

    if not context.strip():
        raise ValueError("Study material cannot be empty.")

    if not 1 <= count <= 10:
        raise ValueError("Count must be between 1 and 10.")

    if question_type not in {"MCQ", "short", "numerical"}:
        raise ValueError("Invalid question type.")

    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("Invalid difficulty.")

    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

    prompt = (
        prompt_template
        .replace("{topic}", topic)
        .replace("{question_type}", question_type)
        .replace("{difficulty}", difficulty)
        .replace("{count}", str(count))
        .replace("{context}", context)
    )

    prompt += """

ADDITIONAL REQUIREMENTS:
- Return only a JSON array.
- Include all required question fields.
- Use the supplied topic ID for topic_id.
- Do not invent source references.
- Set verified to false.
- Set hash to an empty string.
- Set embedding to null.
- Do not invent information absent from the material.
"""

    response = None

    # Retry temporary server or rate-limit errors
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                },
            )
            break

        except (errors.ServerError, errors.ClientError) as exc:
            status = getattr(exc, "code", None)

            # Retry only temporary errors
            if status not in {429, 500, 502, 503, 504}:
                raise

            if attempt == 2:
                raise

            wait_seconds = 2 ** (attempt + 1)
            print(
                f"Temporary Gemini error. "
                f"Retrying in {wait_seconds} seconds..."
            )
            time.sleep(wait_seconds)

    if response is None or not response.text:
        raise ValueError("Gemini returned an empty response.")

    try:
        questions = json.loads(response.text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(
            "Gemini did not return valid JSON."
        ) from exc

    if not isinstance(questions, list):
        raise ValueError("Expected a JSON array.")

    required_fields = {
        "id",
        "type",
        "stem",
        "options",
        "answer",
        "explanation",
        "topic_id",
        "source_ref",
        "difficulty",
    }

    for question in questions:
        if not isinstance(question, dict):
            raise ValueError("Each question must be an object.")

        missing = required_fields - question.keys()

        if missing:
            raise ValueError(
                f"Question is missing fields: {missing}"
            )

        if question["type"] != question_type:
            raise ValueError("Incorrect question type.")

        if question["difficulty"] != difficulty:
            raise ValueError("Incorrect difficulty.")

        for field in ("stem", "answer", "explanation", "source_ref"):
            if not isinstance(question[field], str) or not question[field].strip():
                raise ValueError(f"Invalid or empty field: {field}")

        if question_type == "MCQ":
            options = question["options"]

            if (
                not isinstance(options, list)
                or len(options) != 4
                or not all(isinstance(option, str) for option in options)
                or len(set(options)) != 4
            ):
                raise ValueError(
                    "MCQs need exactly four unique string options."
                )

            if question["answer"] not in options:
                raise ValueError(
                    "The correct answer must match one of the options."
                )

        question["id"] = str(uuid.uuid4())
        question["topic_id"] = topic_id
        question["verified"] = False
        question["hash"] = ""
        question["embedding"] = None

    return questions
