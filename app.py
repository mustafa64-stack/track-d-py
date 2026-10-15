
import config
import streamlit as st
from html import escape
from study_data import init_session_state, calculate_dashboard_metrics

st.set_page_config(
    page_title="AI Study Companion",
    page_icon="📚",
    layout="wide"
)

# Initialize application session data
init_session_state()
stats = calculate_dashboard_metrics()

# Use safe defaults if a metric is missing
materials_count = stats.get(
    "materials_count",
    stats.get("total_documents", 0)
)
quizzes_count = stats.get(
    "quizzes_count",
    stats.get("total_quizzes", 0)
)
average_mastery = stats.get(
    "average_mastery",
    stats.get("average_score", 0)
)
streak_days = stats.get("streak_days", 0)

# Keep the displayed values safe
student_name = st.session_state.get("student_name", "Student").strip()
if not student_name:
    student_name = "Student"

# --- Custom styling ---
st.markdown("""
<style>
.main-title {
    text-align: center;
    font-size: 2.4rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
    color: #1e293b;
}
.subtitle {
    text-align: center;
    font-size: 1.15rem;
    color: #64748b;
    margin-bottom: 1.8rem;
}
.welcome-hero {
    padding: 28px;
    border-radius: 16px;
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: #ffffff;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.2);
}
.welcome-hero h2 {
    color: #ffffff;
    margin-bottom: 0.5rem;
}
.feature-card {
    padding: 22px;
    border-radius: 14px;
    min-height: 180px;
    margin-bottom: 1rem;
    border: 1px solid #e2e8f0;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.feature-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.06);
}
.card-upload {
    background: linear-gradient(135deg, #fdf2f8, #fff1f2);
    border-color: #fbcfe8;
}
.card-chat {
    background: linear-gradient(135deg, #eff6ff, #f0fdf4);
    border-color: #bfdbfe;
}
.card-quiz {
    background: linear-gradient(135deg, #fffbeb, #fef3c7);
    border-color: #fde68a;
}
.card-dash {
    background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
    border-color: #bbf7d0;
}
.tip-callout {
    padding: 16px 20px;
    border-radius: 12px;
    background: #f8fafc;
    border-left: 4px solid #6366f1;
    margin: 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)


# --- Sidebar: User Profile & Status ---
st.sidebar.title("📚 Study Portal")

student_input = st.sidebar.text_input(
    "Student Name",
    value=st.session_state.get("student_name", ""),
    placeholder="Enter your name..."
)

if student_input.strip():
    st.session_state["student_name"] = student_input.strip()

current_student = st.session_state.get("student_name", "Student")

st.sidebar.caption(f"Logged in as **{current_student}**")

st.sidebar.divider()
st.sidebar.markdown("### 📌 Quick Navigation")

st.sidebar.page_link("app.py", label="Home Overview", icon="🏠")
st.sidebar.page_link("pages/1_Upload.py", label="Study Material", icon="📤")
st.sidebar.page_link("pages/2_Chat.py", label="AI Tutor Chat", icon="💬")
st.sidebar.page_link("pages/3_Quiz.py", label="Practice Quiz", icon="📝")
st.sidebar.page_link("pages/4_Dashboard.py", label="Analytics Dashboard", icon="📊")
st.sidebar.page_link("pages/5_Knowledge_Base.py", label="Knowledge Base & Ontology", icon="📚")

st.sidebar.divider()
st.sidebar.metric("🔥 Study Streak", f"{streak_days} days")


# --- Main Page Header ---
st.markdown(
    '<div class="main-title">AI Study Companion</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Personalized notes comprehension, '
    'interactive tutoring, and progress tracking</div>',
    unsafe_allow_html=True
)


# --- Hero Greeting ---
safe_student = escape(current_student)

st.markdown(
    f"""
    <div class="welcome-hero">
        <h2>Welcome back, {safe_student}! 👋</h2>
        <p style="font-size: 1.05rem; opacity: 0.95;">
            You have <b>{materials_count} documents</b> in your library
            and an active <b>{streak_days}-day streak</b>.
        </p>
        <p style="font-size: 0.95rem; opacity: 0.85; margin-bottom: 0;">
            Upload Notes &nbsp;•&nbsp; Chat with Tutor &nbsp;•&nbsp;
            Test Concepts &nbsp;•&nbsp; Track Mastery
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# --- Primary Feature Cards ---
st.markdown("### 🚀 Study Modules")

col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown(
        f"""
        <div class="feature-card card-upload">
            <h4 style="margin-top:0;">📤 Upload &amp; Manage Notes</h4>
            <p style="color:#475569; font-size:0.95rem;">
                Keep your PDF lecture slides and lecture notes
                indexed and ready for reference.
            </p>
            <div style="margin-top:12px; font-weight:600;
                        color:#db2777; font-size:0.9rem;">
                📁 {materials_count} Files Available
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "Open Notes Library ➔",
        key="nav_upload",
        use_container_width=True
    ):
        st.switch_page("pages/1_Upload.py")

    st.markdown(
        f"""
        <div class="feature-card card-quiz">
            <h4 style="margin-top:0;">📝 Interactive Practice Quiz</h4>
            <p style="color:#475569; font-size:0.95rem;">
                Generate customized multiple-choice challenges
                across CS concepts and test retention.
            </p>
            <div style="margin-top:12px; font-weight:600;
                        color:#d97706; font-size:0.9rem;">
                🎯 {quizzes_count} Quizzes Completed
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "Start Practicing ➔",
        key="nav_quiz",
        use_container_width=True
    ):
        st.switch_page("pages/3_Quiz.py")


with col2:
    st.markdown(
        """
        <div class="feature-card card-chat">
            <h4 style="margin-top:0;">💬 Concept AI Tutor</h4>
            <p style="color:#475569; font-size:0.95rem;">
                Ask targeted questions, get simplified explanations,
                and walk through code step-by-step.
            </p>
            <div style="margin-top:12px; font-weight:600;
                        color:#2563eb; font-size:0.9rem;">
                🤖 Instant Interactive Explanations
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "Talk to AI Tutor ➔",
        key="nav_chat",
        use_container_width=True
    ):
        st.switch_page("pages/2_Chat.py")

    st.markdown(
        f"""
        <div class="feature-card card-dash">
            <h4 style="margin-top:0;">📊 Progress &amp; Mastery</h4>
            <p style="color:#475569; font-size:0.95rem;">
                Identify weak subtopics, review past scores,
                and track your proficiency over time.
            </p>
            <div style="margin-top:12px; font-weight:600;
                        color:#059669; font-size:0.9rem;">
                📈 {average_mastery}% Average Mastery
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "View Analytics ➔",
        key="nav_dash",
        use_container_width=True
    ):
        st.switch_page("pages/4_Dashboard.py")


st.divider()


# --- Quick Live Metrics ---
st.markdown("### 📈 Current Learning Snapshot")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        "Study Materials",
        materials_count,
        help="Active documents in your library"
    )

with m2:
    st.metric(
        "Quizzes Finished",
        quizzes_count,
        help="Total completed quiz sessions"
    )

with m3:
    st.metric(
        "Average Score",
        f"{average_mastery}%",
        help="Calculated from the available quiz metrics"
    )

with m4:
    st.metric(
        "Current Streak",
        f"{streak_days} Days"
    )


# --- Helpful Student Tip ---
st.markdown(
    """
    <div class="tip-callout">
        💡 <b>Active Recall Tip:</b>
        Instead of passively rereading lecture slides, test yourself
        using the <b>Practice Quiz</b> module after learning a new
        concept to help reinforce your understanding.
    </div>
    """,
    unsafe_allow_html=True
)
