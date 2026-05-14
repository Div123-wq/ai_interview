# 🤖 AI Interview Coach & Career Mentor

> An intelligent, AI-powered platform to prepare candidates for job interviews, provide real-time feedback, and guide their career growth journey.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
  - [AI Interview Coach](#-ai-interview-coach)
  - [Career Mentor](#-career-mentor)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Usage](#-usage)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

**AI Interview Coach & Career Mentor** is a smart, conversational platform designed to help job seekers:
- Practice and prepare for technical and behavioral interviews using AI-driven mock sessions.
- Receive instant, personalized feedback on their answers, communication, and confidence.
- Get tailored career guidance, skill gap analysis, and roadmap recommendations.

Whether you're a fresh graduate or an experienced professional, this system acts as your **24/7 personal interview trainer and career advisor**.

---

## 🚀 Features

### 🎤 AI Interview Coach

| Feature | Description |
|---|---|
| **Mock Interview Sessions** | Conduct realistic mock interviews for any role (SDE, Data Analyst, PM, etc.) with AI-generated questions |
| **Domain-Specific Questions** | Automatically fetches role-specific technical and HR questions based on your target job |
| **Real-Time Answer Evaluation** | Analyzes your responses for relevance, depth, clarity, and correctness |
| **Voice-Based Interviews** | Supports speech-to-text input for a realistic interview feel |
| **Text-to-Speech Feedback** | AI reads out questions and feedback using natural TTS voice |
| **Behavioral Question Practice** | STAR method guidance for situational and behavioral questions |
| **Follow-Up Questions** | Dynamically generates follow-up questions based on your previous answer |
| **Difficulty Levels** | Choose interview difficulty: Beginner, Intermediate, or Advanced |
| **Interview History** | Saves past sessions so you can review and track improvement |
| **Performance Scoring** | Assigns a score to each answer with detailed justification |
| **Confidence Analysis** | Evaluates tone, hesitation markers, and communication confidence |
| **Time Management Alerts** | Notifies if your answer is too short or too long for the question |

---

### 🧭 Career Mentor

| Feature | Description |
|---|---|
| **Career Path Recommendations** | Suggests ideal career paths based on skills, interests, and experience |
| **Skill Gap Analysis** | Identifies missing skills needed for your target job role |
| **Personalized Learning Roadmap** | Generates a step-by-step learning plan with curated resources |
| **Resume Review & Suggestions** | Analyzes resume content and suggests improvements for ATS optimization |
| **Job Role Matching** | Matches your profile to the most suitable job roles in the market |
| **Industry Insights** | Provides trends, salary benchmarks, and in-demand skills by domain |
| **Goal Setting & Progress Tracking** | Helps set SMART career goals and monitors milestones |
| **Mentorship Chat** | AI-powered career advisor chatbot for ongoing career questions |
| **LinkedIn Profile Tips** | Provides recommendations to improve LinkedIn visibility and reach |
| **Certification Recommendations** | Suggests certifications relevant to your career goals |
| **Job Search Strategy** | Guides on where and how to apply, networking tips, and cold outreach |
| **Interview Preparation Plan** | Creates a customized week-by-week interview prep schedule |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, FastAPI / Flask |
| **AI / NLP** | Google Gemini API / OpenAI GPT |
| **Speech** | SpeechRecognition, gTTS / pyttsx3 |
| **Frontend** | HTML, CSS, JavaScript / React |
| **Database** | SQLite / Firebase / MongoDB |
| **Authentication** | JWT / OAuth2 |
| **Deployment** | Docker, Render / Railway / Vercel |

---

## 📁 Project Structure

```
ai_interview/
│
├── app.py                    # Main application entry point
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
│
├── routes/                   # API route handlers
│   ├── interview.py          # Interview session routes
│   └── mentor.py             # Career mentor routes
│
├── services/                 # Core business logic
│   ├── ai_engine.py          # AI model integration
│   ├── voice_service.py      # STT & TTS services
│   ├── resume_parser.py      # Resume analysis logic
│   └── career_advisor.py     # Career guidance logic
│
├── models/                   # Database models
│   ├── user.py
│   ├── session.py
│   └── feedback.py
│
├── static/                   # Frontend static assets
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/                # HTML templates
│   ├── index.html
│   ├── interview.html
│   └── mentor.html
│
└── tests/                    # Unit & integration tests
    ├── test_interview.py
    └── test_mentor.py
```

---

## ⚡ Getting Started

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- An API key for Gemini / OpenAI

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/ai_interview.git
cd ai_interview

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
cp .env.example .env
# Edit .env and add your API keys

# 5. Run the application
python app.py
# Or with FastAPI:
uvicorn app:app --reload
```

### Environment Variables

```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_jwt_secret
DATABASE_URL=sqlite:///interview.db
```

---

## 📖 Usage

1. **Register / Login** — Create your profile with your skills, experience, and target role.
2. **Start Mock Interview** — Select role, difficulty, and interview type (Technical / HR / Mixed).
3. **Answer Questions** — Respond via text or voice input.
4. **Get Feedback** — Receive detailed AI feedback after each answer.
5. **View Report** — Get a session summary with scores, strengths, and areas of improvement.
6. **Chat with Career Mentor** — Ask career questions, get roadmaps, and review your resume.
7. **Track Progress** — Monitor your performance over multiple sessions.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add: your feature description'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👩‍💻 Author

**Divya** — [GitHub](https://github.com/your-username) | [LinkedIn](https://linkedin.com/in/your-profile)

---

> ⭐ If you found this project helpful, please give it a star on GitHub!