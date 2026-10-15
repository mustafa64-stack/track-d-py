# 🌟 PrismAI — Multimodal AI Study Companion & Adaptive Assessment Engine
> **Multimodal AI Hackathon 2026 — Track D: Personalized Tutoring & Adaptive Learning**
> Built with Gemini 2.5, Supabase pgvector, and Bayesian Knowledge Tracing (BKT).

---

## 💡 Overview & Problem Statement
Students frequently study from fragmented materials — textbook chapters, slide decks, diagrams, and video lectures — while traditional AI chatbots hallucinate ungrounded responses and fail to model student comprehension.

**PrismAI** solves this by unifying multimodal course content into a **source-grounded knowledge graph**, powering:
1. **Multimodal Grounded AI Tutor:** Citations linking directly to exact textbook page images, slide cards, and timestamped YouTube video segments with an honest refusal guardrail for out-of-domain queries.
2. **Adaptive Cognitive Assessments:** Real-time question generation with two-step cross-validation, anti-trivia filtering, and Bayesian Knowledge Tracing (BKT) student cognitive mastery modeling.
3. **Transparent Learning Analytics:** Empirical learning curves, mastery tracking, and targeted weak-concept remediation.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Ingestion ["1. Multimodal Knowledge Ingestion"]
        PDF["📄 Textbook PDF (opticsbook.pdf)"] --> Extractor["Multimodal Extractor (PyMuPDF & python-pptx)"]
        PPT["🖼️ Lecture Slides (pptx)"] --> Extractor
        YT["🎥 YouTube Lecture (yt_fD1544bM_c4)"] --> YT_Ingest["Transcript Slicer & Timestamp Indexer"]
        Extractor --> Chunks["76 Multimodal Chunks"]
        YT_Ingest --> Chunks
        Chunks --> Embedder["Gemini Embedding (gemini-embedding-001)"]
        Embedder --> VectorStore[("Supabase pgvector (1000-dim HNSW)")]
    end

    subgraph Chat ["2. Source-Grounded AI Tutor"]
        UserQ["Student Query"] --> RAGSearch["Hybrid Vector Search (Top-k Chunks)"]
        VectorStore --> RAGSearch
        RAGSearch --> RefusalGate{"Threshold Check (>0.60 Similarity?)"}
        RefusalGate -- No --> Refusal["🛡️ Honest Refusal: Flagged as Out-of-Domain"]
        RefusalGate -- Yes --> GeminiTutor["Gemini 2.5 Tutor Synthesis"]
        GeminiTutor --> CitedAnswer["Cited Response + Clickable Receipt Chips"]
        CitedAnswer --> MediaViewer["Source Viewer (Page Image / Slide Card / Timestamped Video Player)"]
    end

    subgraph Assessment ["3. Adaptive Assessment & Cognitive BKT"]
        Scope["Select Topic / Scope"] --> FilterChunks["Substantive Chunk Retriever (Anti-TOC Filter)"]
        VectorStore --> FilterChunks
        FilterChunks --> QGen["Question Generator (MCQ / Numerical / Short)"]
        QGen --> QVer["Two-Step LLM Verifier"]
        QVer --> Quiz["Interactive Practice Quiz"]
        Quiz --> StudentAns["Student Answers Assessment"]
        StudentAns --> BKT["Bayesian Knowledge Tracing (BKT Engine)"]
        BKT --> Mastery["Latent Topic Mastery Update (p_L)"]
        Mastery --> Dash["📊 Analytics Dashboard & Weak Area Alerts"]
    end
```

---

## 🚀 Key Features & Rubric Alignment

### 1. Multimodal Knowledge Base & Grounding (20%)
- **Zero Manual Preprocessing:** Ingests PDF textbooks, PPTX slides, images/diagrams, and YouTube video lectures.
- **Deep-Link Video Seeking:** YouTube chunks are sliced into 35-second chapters. In-app source receipts embed `st.video` seeking directly to the relevant timestamp (`start_time=sec`).
- **Honest Refusal Guardrail:** Evaluates semantic similarity thresholds; off-material queries (e.g. *"How do I bake chocolate chip cookies?"*) are cleanly declined without hallucinations.

### 2. Adaptive Assessment & Verification (15%)
- **Two-Step Question Verification:** Generates and cross-validates questions using source excerpts.
- **Strict Anti-TOC Filtering:** Guaranteed zero trivia on table of contents, book layouts, or section titles — testing only true scientific concepts (Snell's law, refractive index, total internal reflection, Brewster's angle, Huygens' principle).
- **Novelty & Deduplication:** Cosine similarity hashing prevents question repetition across assessment attempts.

### 3. Personalization & BKT Learner Model (20%)
- **Bayesian Knowledge Tracing (BKT):** Tracks latent student mastery per topic with standard parameters ($p(L_0) = 0.30$, $p(T) = 0.15$, $p(S) = 0.10$, $p(G) = 0.25$).
- **Dynamic Difficulty Adaptation:** Recommends Easy ($p < 0.60$), Medium ($0.60 \le p < 0.85$), or Hard ($p \ge 0.85$) challenges based on active student proficiency.
- **Intake & Diagnostic Flow:** Smooth diagnostic baseline for new students with no previous history.

### 4. User Experience & Aesthetics (15%)
- **Glassmorphic Dark Theme:** Built with cohesive contrast-safe CSS (`var(--text-color)`, `var(--secondary-background-color)`), responsive cards, and vibrant WCAG-accessible indicators.
- **Interactive Multi-Page Portal:**
  - `app.py`: Overview portal, active streak, and learning snapshot.
  - `pages/1_Upload.py`: Document upload & YouTube lecture ingestion with embedded player preview.
  - `pages/2_Chat.py`: AI Tutor with citation chips and multimedia source receipt viewer.
  - `pages/3_Quiz.py`: Adaptive practice assessments with instant BKT feedback.
  - `pages/4_Dashboard.py`: Cognitive learning curve graphs and weak-concept revision alerts.
  - `pages/5_Knowledge_Base.py`: 38-topic concept hierarchy and interactive chunk explorer.

### 5. System Evaluation & Benchmarking (15%)
- **Simulated Learning Curves:** Verified student simulations across Weak (0.25), Average (0.50), and Strong (0.75) profiles showing empirical mastery gains over 5 sessions (`simulation_chart.png`).
- **Comprehensive Test Set:** Automated verification across 15 curated benchmark queries with known citations and refusal assertions.

---

## ⚡ Quickstart & Installation

```bash
# 1. Clone repository
git clone https://github.com/mustafa64-stack/track-d-py.git
cd track-d-py

# 2. Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment variables (.env)
cp .env.example .env
# Fill in your GEMINI_API_KEY, SUPABASE_URL, and SUPABASE_KEY

# 4. Launch Application
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 👥 Authors & Team
- **Mustafa & Shagun** — Track D: Personalized Tutoring & Adaptive Learning
