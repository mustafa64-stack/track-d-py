"""
study_data.py
Helper module for session state, learning materials,
tutor responses, and progress analytics.
"""

from datetime import datetime
import streamlit as st


# --------------------------------------------------
# 1. AVAILABLE TOPICS
# --------------------------------------------------

AVAILABLE_TOPICS = [
    "Physics of Light and Optics",
    "Electromagnetic Waves",
    "Reflection and Refraction",
    "Total Internal Reflection",
    "Polarization and Brewster's Angle",
    "Wave Optics & Huygens Principle",
    "Fourier Optics & Diffraction",
    "Laser Physics & Coherence",
    "Data Structures",
    "Operating Systems",
    "Computer Networks",
    "Programming Concepts",
]


# --------------------------------------------------
# 2. QUESTION BANK
# --------------------------------------------------

QUESTION_BANK = {
    "Data Structures": [
        {
            "question": "Which data structure follows LIFO?",
            "options": ["Queue", "Stack", "Array", "Linked List"],
            "answer": "Stack"
        },
        {
            "question": "Which data structure follows FIFO?",
            "options": ["Stack", "Tree", "Queue", "Graph"],
            "answer": "Queue"
        },
        {
            "question": "Which data structure stores elements using indexes?",
            "options": ["Array", "Stack", "Queue", "Tree"],
            "answer": "Array"
        }
    ],
    "Operating Systems": [
        {
            "question": "Which of these is an operating system?",
            "options": ["Python", "Windows", "HTML", "MySQL"],
            "answer": "Windows"
        },
        {
            "question": "What is a process?",
            "options": [
                "A program in execution",
                "A storage device",
                "A programming language",
                "A network cable"
            ],
            "answer": "A program in execution"
        },
        {
            "question": "Which is a smaller unit of execution within a process?",
            "options": ["File", "Thread", "Folder", "Database"],
            "answer": "Thread"
        }
    ],
    "Computer Networks": [
        {
            "question": "What does IP help with?",
            "options": [
                "Routing packets",
                "Editing images",
                "Writing documents",
                "Compiling Python"
            ],
            "answer": "Routing packets"
        },
        {
            "question": "Which protocol provides reliable data delivery?",
            "options": ["HTTP only", "TCP", "HTML", "CSS"],
            "answer": "TCP"
        },
        {
            "question": "What does LAN stand for?",
            "options": [
                "Local Area Network",
                "Large Access Node",
                "Linked Application Name",
                "Long Area Number"
            ],
            "answer": "Local Area Network"
        }
    ],
    "Programming Concepts": [
        {
            "question": "Which Python keyword defines a function?",
            "options": ["func", "define", "def", "function"],
            "answer": "def"
        },
        {
            "question": "Which data type stores True or False?",
            "options": ["int", "str", "bool", "list"],
            "answer": "bool"
        },
        {
            "question": "Which symbol starts a comment in Python?",
            "options": ["//", "#", "/*", "<!--"],
            "answer": "#"
        }
    ]
}


# --------------------------------------------------
# 3. INITIALIZE SESSION STATE
# --------------------------------------------------

def apply_custom_theme():
    """Injects adaptive CSS that guarantees flawless font contrast in both dark and light modes."""
    st.markdown("""
    <style>
    /* Global modern typography */
    html, body, [class*="st-"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Helvetica, Arial, sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }
    
    /* Ensure titles adapt dynamically to current theme text color */
    .main-title, .dashboard-title {
        color: var(--text-color) !important;
        font-weight: 800 !important;
    }
    .subtitle {
        color: var(--text-color) !important;
        opacity: 0.8 !important;
    }
    
    /* Adaptive glassmorphic feature cards */
    .feature-card {
        background: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid rgba(148, 163, 184, 0.22) !important;
        border-radius: 14px;
        padding: 22px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    }
    .feature-card h4 {
        color: var(--text-color) !important;
        margin-top: 0;
    }
    .feature-card p {
        color: var(--text-color) !important;
        opacity: 0.85 !important;
        font-size: 0.95rem;
    }
    
    /* Callout & tip boxes */
    .tip-callout {
        background: var(--secondary-background-color) !important;
        border-left: 4px solid #6366f1 !important;
        color: var(--text-color) !important;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 1.5rem 0;
    }
    .weak-alert-box {
        background: rgba(239, 68, 68, 0.12) !important;
        border: 1px solid rgba(239, 68, 68, 0.35) !important;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 1rem;
        color: var(--text-color) !important;
    }
    .tag-pill {
        background: rgba(239, 68, 68, 0.15) !important;
        color: #ef4444 !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
    }
    
    /* Code blocks contrast in dark mode */
    pre, code {
        color: var(--text-color) !important;
    }
    </style>
    """, unsafe_allow_html=True)


def init_session_state():

    defaults = {
        "student_name": "Shagun",
        "uploaded_materials": [],
        "chat_history": [],
        "quiz_history": [],
        "quiz_answers": [],
        "quiz_score": 0,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

    apply_custom_theme()


# --------------------------------------------------
# 4. GENERATE A TUTOR RESPONSE
# --------------------------------------------------

def generate_tutor_response(
    question,
    topic="Programming Concepts"
):
    question = question.strip()

    if not question:
        return "Please enter a question so I can help you."

    q = question.lower()

    if any(word in q for word in [
        "data structure", "array", "stack", "queue"
    ]):
        return (
            "Let's understand this step by step!\n\n"
            "A data structure organizes and stores data "
            "so that it can be used efficiently.\n\n"
            "Examples include arrays, linked lists, stacks, "
            "queues, trees, and graphs."
        )

    if any(word in q for word in [
        "operating system", "process", "thread"
    ]):
        return (
            "An Operating System (OS) manages computer "
            "hardware and software resources.\n\n"
            "Examples include Windows, Linux, and macOS.\n\n"
            "A process is a program currently executing. "
            "A thread is a smaller execution unit within a process."
        )

    if any(word in q for word in [
        "computer network", "tcp", "ip address"
    ]):
        return (
            "A computer network connects devices so they can "
            "communicate and share resources.\n\n"
            "TCP helps provide reliable data delivery, while IP "
            "helps route packets to their destinations."
        )

    if any(word in q for word in [
        "python", "programming", "function"
    ]):
        return (
            "Programming means giving instructions to a computer.\n\n"
            "In Python, a function is a reusable block of code.\n\n"
            "Example:\n\n"
            "```python\n"
            "def greet():\n"
            "    print('Hello!')\n\n"
            "greet()\n"
            "```\n\n"
            "The `def` keyword defines a function."
        )

    return (
        f"Let's work through your question about {topic}.\n\n"
        f"You asked: {question}\n\n"
        "Try breaking the concept into smaller parts. "
        "Share an example if you would like a more detailed explanation."
    )


# --------------------------------------------------
# 5. CALCULATE DASHBOARD METRICS
# --------------------------------------------------

def calculate_dashboard_metrics():

    uploaded_materials = st.session_state.get(
        "uploaded_materials", []
    )

    quiz_history = st.session_state.get(
        "quiz_history", []
    )

    # Count materials, quizzes and scores
    total_documents = len(uploaded_materials)
    total_quizzes = len(quiz_history)

    percentages = []

    for quiz in quiz_history:
        percentage = quiz.get("percentage")

        if isinstance(percentage, (int, float)):
            percentages.append(percentage)
        else:
            score = quiz.get("score", 0)
            total = quiz.get("total", 0)

            if isinstance(score, (int, float)) and total:
                percentages.append(score / total * 100)

    average_mastery = (
        round(sum(percentages) / len(percentages))
        if percentages else 0
    )

    # Build topic mastery breakdown
    topic_scores = {}

    for quiz in quiz_history:
        topic = quiz.get("topic", "General")
        percentage = quiz.get("percentage")

        if not isinstance(percentage, (int, float)):
            score = quiz.get("score", 0)
            total = quiz.get("total", 0)

            if total and isinstance(score, (int, float)):
                percentage = score / total * 100
            else:
                continue

        topic_scores.setdefault(topic, []).append(percentage)

    mastery_breakdown = {
        topic: round(sum(scores) / len(scores))
        for topic, scores in topic_scores.items()
        if scores
    }

    # Calculate streak based on recorded quiz dates.
    # This is a basic approximation from quiz history.
    streak_days = 0
    quiz_dates = set()

    for quiz in quiz_history:
        date_value = quiz.get("date")

        if date_value:
            try:
                if isinstance(date_value, datetime):
                    quiz_date = date_value.date()
                else:
                    quiz_date = datetime.strptime(
                        str(date_value), "%Y-%m-%d"
                    ).date()

                quiz_dates.add(quiz_date)
            except (ValueError, TypeError):
                continue

    today = datetime.now().date()

    if today in quiz_dates:
        current_date = today

        while current_date in quiz_dates:
            streak_days += 1
            current_date = current_date.fromordinal(
                current_date.toordinal() - 1
            )
    elif today.fromordinal(today.toordinal() - 1) in quiz_dates:
        current_date = today.fromordinal(today.toordinal() - 1)

        while current_date in quiz_dates:
            streak_days += 1
            current_date = current_date.fromordinal(
                current_date.toordinal() - 1
            )

    return {
        # Keys used by the Dashboard
        "materials_count": total_documents,
        "quizzes_count": total_quizzes,
        "average_mastery": average_mastery,
        "streak_days": streak_days,
        "mastery_breakdown": mastery_breakdown,

        # Keep the existing metric names available too
        "total_documents": total_documents,
        "total_quizzes": total_quizzes,
        "total_questions": len(
            st.session_state.get("chat_history", [])
        ),
        "average_score": average_mastery,
    }


# --------------------------------------------------
# 6. FORMAT FILE SIZE
# --------------------------------------------------

def format_file_size(size_bytes):

    if size_bytes < 0:
        return "Unknown size"

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"

    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


# --------------------------------------------------
# 7. GET CURRENT DATE AND TIME
# --------------------------------------------------

def get_current_timestamp():
    return datetime.now().strftime("%d %b %Y, %I:%M %p")