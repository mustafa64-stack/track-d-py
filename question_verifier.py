
import json
import os
import time
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

PROMPT_PATH = (
    Path(__file__).parent / "question_verification_prompt.txt"
)


def verify_question(
    question: dict,
    context: str,
    source_ref: str,
) -> dict:
    """Verify a generated question against supplied study material."""

    if not context.strip():
        raise ValueError("Study material cannot be empty.")

    required_fields = {
        "type",
        "stem",
        "answer",
        "explanation",
        "topic_id",
        "difficulty",
    }

    missing = required_fields - question.keys()

    if missing:
        raise ValueError(
            f"Question is missing fields: {missing}"
        )

    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

    # Replace only placeholders, preserving JSON braces in the prompt
    prompt = (
        prompt_template
        .replace("{question}", json.dumps(question, ensure_ascii=False))
        .replace("{proposed_answer}", str(question["answer"]))
        .replace("{context}", context)
        .replace("{source_ref}", source_ref)
    )

    prompt += """

ADDITIONAL REQUIREMENTS:
- Return one JSON object, not a JSON array.
- correct must be a boolean.
- source_supported must be a boolean.
- If the material is insufficient, set source_supported to false
  and correct to false.
- Do not treat a claim as verified merely because it appears in
  the proposed explanation.
- expected_answer must contain your independently derived answer.
"""

    response = None

    # Retry temporary API failures
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
        result = json.loads(response.text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(
            "Verifier did not return valid JSON."
        ) from exc

    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object.")

    required_result_fields = {
        "correct",
        "expected_answer",
        "proposed_answer",
        "explanation",
        "source_supported",
    }

    missing_result_fields = required_result_fields - result.keys()

    if missing_result_fields:
        raise ValueError(
            f"Verifier response is missing fields: "
            f"{missing_result_fields}"
        )

    if not isinstance(result["correct"], bool):
        raise ValueError("'correct' must be true or false.")

    if not isinstance(result["source_supported"], bool):
        raise ValueError("'source_supported' must be true or false.")

    if not isinstance(result["expected_answer"], str):
        raise ValueError("'expected_answer' must be a string.")

    if not isinstance(result["proposed_answer"], str):
        raise ValueError("'proposed_answer' must be a string.")

    if not isinstance(result["explanation"], str):
        raise ValueError("'explanation' must be a string.")

    # A question cannot pass if its answer is unsupported
    if not result["source_supported"]:
        result["correct"] = False

    return result
