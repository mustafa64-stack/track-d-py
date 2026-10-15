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
    "Physics of Light and Optics": [
        {
            "question": "According to electromagnetic wave theory, what is the speed of light c in a vacuum related to?",
            "options": [
                "Permittivity eps_0 and permeability mu_0 (c = 1/sqrt(mu_0 * eps_0))",
                "Gravitational constant and Planck's constant",
                "Only the frequency of light",
                "The refractive index of air"
            ],
            "answer": "Permittivity eps_0 and permeability mu_0 (c = 1/sqrt(mu_0 * eps_0))",
            "explanation": "Maxwell derived the wave equation in vacuum showing the propagation speed is c = 1 / sqrt(mu_0 * eps_0)."
        },
        {
            "question": "What mathematical theorem relates the divergence of an electric field over a volume to its flux through the boundary surface?",
            "options": [
                "Divergence Theorem (Gauss's Theorem)",
                "Stokes' Theorem",
                "Fermat's Principle",
                "Brewster's Law"
            ],
            "answer": "Divergence Theorem (Gauss's Theorem)",
            "explanation": "Gauss's Divergence Theorem transforms the volume integral of the divergence of a vector field into a surface integral of its flux."
        },
        {
            "question": "In an electromagnetic wave in vacuum, what is the spatial orientation between electric field E, magnetic field B, and wavevector k?",
            "options": [
                "E, B, and k are mutually perpendicular (orthogonal)",
                "E and B are parallel to each other and to k",
                "E and B oscillate in the same plane along k",
                "B is zero in a vacuum"
            ],
            "answer": "E, B, and k are mutually perpendicular (orthogonal)",
            "explanation": "Electromagnetic waves are transverse: E and B oscillate perpendicularly to each other and to the direction of propagation k."
        }
    ],
    "Electromagnetic Waves": [
        {
            "question": "Which set of fundamental equations forms the theoretical foundation of classical electrodynamics and wave optics?",
            "options": ["Maxwell's Equations", "Schrodinger Equations", "Navier-Stokes Equations", "Euler-Lagrange Equations"],
            "answer": "Maxwell's Equations",
            "explanation": "Maxwell's four partial differential equations unify electricity, magnetism, and optics."
        },
        {
            "question": "The Poynting vector S in electromagnetic theory represents:",
            "options": [
                "The directional energy flux density (power per unit area) of the wave",
                "The electrostatic force on a stationary charge",
                "The wavelength divided by frequency",
                "The phase difference in a birefringent crystal"
            ],
            "answer": "The directional energy flux density (power per unit area) of the wave",
            "explanation": "The Poynting vector S = (1/mu_0) (E x B) measures the rate of electromagnetic energy transport per unit area."
        }
    ],
    "Reflection and Refraction": [
        {
            "question": "What does Snell's Law quantitatively relate at an interface between two transparent dielectric media?",
            "options": [
                "Refractive indices and the sines of incident and refracted angles (n1 sin theta1 = n2 sin theta2)",
                "The energy dissipation to wave amplitude",
                "The Doppler frequency shift of light",
                "The rate of photon absorption"
            ],
            "answer": "Refractive indices and the sines of incident and refracted angles (n1 sin theta1 = n2 sin theta2)",
            "explanation": "Snell's Law states n1 * sin(theta1) = n2 * sin(theta2), derived from phase matching at the boundary."
        },
        {
            "question": "According to Fermat's Principle of Least Time, light traverses an optical path that:",
            "options": [
                "Takes stationary (extremum) time relative to nearby paths",
                "Always follows a straight line regardless of medium",
                "Maximizes geometric path length",
                "Is unpredictable in dielectric media"
            ],
            "answer": "Takes stationary (extremum) time relative to nearby paths",
            "explanation": "Fermat's principle asserts that the actual path taken by light between two points is an extremum of optical path length."
        },
        {
            "question": "When light enters a medium with a higher refractive index (denser medium), what happens to its wave properties?",
            "options": [
                "Speed and wavelength decrease, while frequency remains constant",
                "Speed increases while wavelength stays constant",
                "Frequency decreases and wavelength increases",
                "All wave properties remain unchanged"
            ],
            "answer": "Speed and wavelength decrease, while frequency remains constant",
            "explanation": "Since v = c/n and lambda = lambda_0/n, velocity and wavelength decrease while frequency f is determined solely by the source."
        }
    ],
    "Total Internal Reflection": [
        {
            "question": "Under what physical condition does Total Internal Reflection (TIR) occur?",
            "options": [
                "Light travels from denser (n1) to rarer (n2) medium with angle > critical angle",
                "Light travels from vacuum into diamond at any angle",
                "Light travels from air into water at normal incidence",
                "Only when light is completely circularly polarized"
            ],
            "answer": "Light travels from denser (n1) to rarer (n2) medium with angle > critical angle",
            "explanation": "When light travels from n1 > n2 and theta_i > theta_c = arcsin(n2/n1), 100% of the energy is reflected back into the denser medium."
        },
        {
            "question": "How is the critical angle theta_c calculated for an interface between media n1 and n2 (n1 > n2)?",
            "options": [
                "theta_c = arcsin(n2 / n1)",
                "theta_c = arctan(n1 / n2)",
                "theta_c = arccos(n2 * n1)",
                "theta_c = arcsin(n1 / n2)"
            ],
            "answer": "theta_c = arcsin(n2 / n1)",
            "explanation": "Setting theta_2 = 90 degrees in Snell's Law gives sin(theta_c) = n2 / n1."
        },
        {
            "question": "Which widespread technology directly relies on total internal reflection for ultra-high speed communication?",
            "options": [
                "Fiber optic cables",
                "Cathode ray tubes",
                "Copper coaxial cables",
                "Microwave horns"
            ],
            "answer": "Fiber optic cables",
            "explanation": "Optical fiber waveguides trap light pulses in their higher-index glass cores via continuous total internal reflection."
        }
    ],
    "Polarization and Brewster's Angle": [
        {
            "question": "What is Brewster's Angle (polarizing angle)?",
            "options": [
                "The angle of incidence where reflected light is completely linearly polarized",
                "The angle where total internal reflection begins",
                "The angle where diffraction fringes disappear",
                "The angle where refractive index equals zero"
            ],
            "answer": "The angle of incidence where reflected light is completely linearly polarized",
            "explanation": "At Brewster's angle, p-polarized reflection drops to zero, leaving only s-polarized (linearly polarized) light."
        },
        {
            "question": "At Brewster's angle theta_B, what is the geometric relationship between the reflected and refracted rays?",
            "options": [
                "They are mutually perpendicular (orthogonal at 90 degrees)",
                "They are parallel and travel in opposite directions",
                "They form an angle of 180 degrees",
                "They overlap along the surface normal"
            ],
            "answer": "They are mutually perpendicular (orthogonal at 90 degrees)",
            "explanation": "Because theta_r + theta_t = 90 degrees, oscillating dipoles in the second medium cannot radiate along their oscillation axis."
        },
        {
            "question": "Which formula determines Brewster's angle theta_B for light incident from medium n1 onto medium n2?",
            "options": [
                "tan(theta_B) = n2 / n1",
                "sin(theta_B) = n1 / n2",
                "cos(theta_B) = n2 / n1",
                "tan(theta_B) = n1 * n2"
            ],
            "answer": "tan(theta_B) = n2 / n1",
            "explanation": "Brewster's condition theta_B + theta_t = 90 deg gives sin(theta_B) = n2/n1 * cos(theta_B) => tan(theta_B) = n2 / n1."
        }
    ],
    "Wave Optics & Huygens Principle": [
        {
            "question": "What does Huygens' Principle state about wave propagation?",
            "options": [
                "Every point on a wavefront acts as a source of secondary wavelets",
                "Light only propagates in straight Euclidean rays",
                "Electrons cannot emit photons during acceleration",
                "Interference only occurs for longitudinal waves"
            ],
            "answer": "Every point on a wavefront acts as a source of secondary wavelets",
            "explanation": "The envelope of secondary spherical wavelets reconstructs the advancing wavefront, explaining refraction and diffraction."
        },
        {
            "question": "In Young's double-slit experiment, what produces the alternating bright and dark fringes on the screen?",
            "options": [
                "Constructive and destructive interference of coherent light",
                "Photoelectric emission from the barrier slits",
                "Total internal reflection inside the slits",
                "Thermal dissipation of photons"
            ],
            "answer": "Constructive and destructive interference of coherent light",
            "explanation": "Path length difference delta = d * sin(theta) causes phase differences leading to constructive and destructive interference fringes."
        }
    ],
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
    /* Global modern typography - applied without breaking Streamlit Material Symbols icon ligatures */
    html, body, p, label, input, textarea, button, select {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Helvetica, Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
    }
    
    /* Explicitly preserve icon ligatures for Streamlit and Material Symbols */
    [data-testid="stIconMaterial"], 
    .material-symbols-rounded, 
    .material-symbols-outlined, 
    [class*="material-symbols"],
    [data-testid*="Icon"],
    [data-testid="stExpanderToggleIcon"],
    i.material-icons {
        font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
        font-style: normal;
        letter-spacing: normal;
        text-transform: none;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        -webkit-font-feature-settings: 'liga';
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

    /* Form containers: dark mode sleek styling */
    [data-testid="stForm"] {
        border: 1px solid rgba(148, 163, 184, 0.18) !important;
        border-radius: 16px !important;
        background: rgba(26, 31, 44, 0.6) !important;
        padding: 24px !important;
    }

    /* Radio button text */
    div[data-testid="stRadio"] label {
        color: var(--text-color) !important;
        font-size: 0.98rem;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--secondary-background-color) !important;
        border-radius: 8px !important;
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