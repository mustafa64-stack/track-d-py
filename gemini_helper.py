import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# Use the reliable Flash model
MODEL_NAME = os.getenv("GEMINI_FLASH_MODEL", "gemini-flash-latest")


# --------------------------------------------------
# 1. GEMINI CLIENT
# --------------------------------------------------

def get_gemini_client():
    """Create a Gemini client when an API key is available."""

    api_key = os.getenv("GEMINI_API_KEY") or API_KEY

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY nahi mili. Project ki .env file check karo."
        )

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=30000)
    )


# --------------------------------------------------
# 2. GENERATE GEMINI RESPONSE
# --------------------------------------------------

def generate_with_retry(
    client,
    prompt,
    json_response=False,
    max_attempts=1
):
    """Generate a response and provide a readable error if it fails."""

    last_error = None

    for _ in range(max(1, int(max_attempts))):
        try:
            config = None

            if json_response:
                config = types.GenerateContentConfig(
                    response_mime_type="application/json"
                )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=config
            )

            response_text = response.text

            if not response_text or not response_text.strip():
                raise ValueError("Gemini ne empty response diya.")

            return response_text.strip()

        except Exception as error:
            last_error = error
            print("GEMINI ERROR:", repr(error))

    raise RuntimeError(
        "Gemini response generate nahi ho saka. "
        "API key, model availability, internet aur API quota check karo. "
        f"Actual error: {type(last_error).__name__}: {last_error}"
    ) from last_error


# --------------------------------------------------
# 3. AI TUTOR
# --------------------------------------------------

def generate_tutor_answer(question, study_material):
    """
    Answer a student's question using retrieved study material only.
    """

    if not isinstance(question, str) or not question.strip():
        return "Please enter a question."

    if (
        not isinstance(study_material, str)
        or not study_material.strip()
    ):
        return (
            "No study material is available. "
            "Please upload and process your notes first."
        )

    prompt = f"""
You are an AI Study Tutor.

Your task is to help a student understand their uploaded notes.

STUDENT QUESTION:
{question.strip()}

RETRIEVED STUDY MATERIAL:
{study_material[:10000]}

STRICT INSTRUCTIONS:
1. Answer using only the supplied study material.
2. Do not invent facts or add unsupported information.
3. Do not use outside knowledge to fill missing information.
4. If the material does not contain enough information to answer,
   say exactly:
   "This information was not found in your uploaded study material."
5. Keep the answer clear and concise.
6. Use simple English that a college student can understand.
7. Explain technical concepts in short steps when appropriate.
8. Do not invent document names, page numbers, or citations.
9. If the material provides a definition, preserve its meaning.
10. Do not claim that a statement is verified if the material
    does not support it.

Return only the answer for the student.
"""

    try:
        client = get_gemini_client()

        return generate_with_retry(
            client=client,
            prompt=prompt
        )

    except Exception as error:
        print("TUTOR ERROR:", repr(error))

        return (
            "The AI tutor is temporarily unavailable. "
            "Please check the Gemini API configuration, model "
            "availability and usage quota, then try again."
        )


# --------------------------------------------------
# 4. VALIDATE ONE QUIZ QUESTION
# --------------------------------------------------

def validate_quiz_question(item):
    """Validate the structure and answer of a generated MCQ."""

    if not isinstance(item, dict):
        return None

    question = item.get("question")
    options = item.get("options")
    answer = item.get("answer")
    explanation = item.get("explanation", "")

    if not isinstance(question, str) or not question.strip():
        return None

    if not isinstance(options, list) or len(options) != 4:
        return None

    if not all(
        isinstance(option, str) and option.strip()
        for option in options
    ):
        return None

    # Reject duplicate options.
    normalized_options = [option.strip().casefold() for option in options]

    if len(set(normalized_options)) != 4:
        return None

    if not isinstance(answer, str):
        return None

    answer = answer.strip()

    # Answer must match exactly one option, ignoring case and outer spaces.
    matching_options = [
        option
        for option in options
        if option.strip().casefold() == answer.casefold()
    ]

    if len(matching_options) != 1:
        return None

    answer = matching_options[0]

    if not isinstance(explanation, str):
        explanation = ""

    return {
        "question": question.strip(),
        "options": [option.strip() for option in options],
        "answer": answer.strip(),
        "explanation": explanation.strip()
    }


# --------------------------------------------------
# 5. GENERATE QUIZ FROM UPLOADED MATERIAL
# --------------------------------------------------

def generate_quiz_questions(
    topic,
    study_material=None,
    num_questions=5,
    difficulty="Medium",
    text=None,
    **kwargs
):
    """
    Generate multiple-choice questions from uploaded study material.

    Returns a list of validated questions.
    Raises RuntimeError if AI generation fails.
    """

    if study_material is None:
        study_material = text

    if (
        not isinstance(study_material, str)
        or not study_material.strip()
    ):
        raise ValueError(
            "Study material empty hai. Pehle PDF upload aur process karo."
        )

    try:
        num_questions = int(num_questions)
    except (TypeError, ValueError):
        num_questions = 5

    num_questions = max(1, min(num_questions, 10))

    allowed_difficulties = {"Easy", "Medium", "Hard"}

    if difficulty not in allowed_difficulties:
        difficulty = "Medium"

    prompt = f"""
You are an educational assessment generator.

Generate exactly {num_questions} multiple-choice questions based
strictly on the supplied study material.

TOPIC:
{topic}

DIFFICULTY:
{difficulty}

STUDY MATERIAL:
{study_material[:12000]}

REQUIREMENTS:
1. Use only information present in the study material.
2. Generate exactly {num_questions} questions.
3. Every question must have exactly four options.
4. There must be exactly one correct option per question.
5. The answer field must match one option exactly.
6. Avoid repeated or nearly identical questions.
7. Do not create questions whose answers are absent from the material.
8. Keep the wording clear and suitable for college students.
9. Include a short explanation supported by the material.
10. Do not invent facts, definitions, numbers or examples.
11. Return valid JSON only. Do not use Markdown fences.

Return JSON in exactly this structure:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
      ],
      "answer": "Exact text of the correct option",
      "explanation": "Short explanation supported by the material"
    }}
  ]
}}
"""

    try:
        client = get_gemini_client()

        response_text = generate_with_retry(
            client=client,
            prompt=prompt,
            json_response=True
        )

        data = json.loads(response_text)

        if not isinstance(data, dict):
            raise ValueError("AI response JSON object nahi hai.")

        generated_questions = data.get("questions")

        if not isinstance(generated_questions, list):
            raise ValueError(
                "AI response mein questions ki list nahi mili."
            )

        valid_questions = []

        for item in generated_questions:
            validated = validate_quiz_question(item)

            if validated is not None:
                valid_questions.append(validated)

        # Avoid silently pretending a partial quiz is complete.
        if len(valid_questions) < num_questions:
            raise ValueError(
                f"Requested {num_questions} questions, "
                f"but only {len(valid_questions)} valid questions "
                "were generated. Please generate the quiz again."
            )

        return valid_questions[:num_questions]

    except Exception as error:
        print("GEMINI QUIZ ERROR:", repr(error))

        raise RuntimeError(
            "AI quiz generation failed. "
            "Check the Gemini model name, API key, usage quota "
            "and uploaded study material. "
            f"Details: {type(error).__name__}: {error}"
        ) from error


# --------------------------------------------------
# 6. CHECK WHETHER GEMINI IS CONFIGURED
# --------------------------------------------------

def check_gemini_configuration():
    """Return a simple status message without making an API request."""

    api_key = os.getenv("GEMINI_API_KEY") or API_KEY

    if not api_key:
        return {
            "configured": False,
            "message": "GEMINI_API_KEY .env file mein nahi mili."
        }

    return {
        "configured": True,
        "message": (
            "API key environment mein mili. "
            "Actual model availability aur quota abhi verify nahi hue."
        )
    }