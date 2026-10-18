# Career Assistant

**AI career assistant: resume analysis, job search and interview preparation.**

A web app with a Django REST API and a React frontend that helps job seekers get ready for the job market: it analyzes a resume with AI, finds vacancies through the HeadHunter API, writes cover letters, runs mock interviews with feedback and tests skills.

> **Status:** working prototype. The backend (Django REST API) is in `career_assistant/backend`, the React frontend is in `career_assistant/frontend`.

---

## Features

- **Resume analysis** — upload a PDF or DOCX; the AI scores it on 6 criteria and lists strengths, what to improve, what to add, formatting issues and key skills
- **Cover letters** — generated in 4 styles: formal, friendly, brief, creative
- **Job search** — vacancies from HeadHunter, saved vacancies and applications tracking
- **Mock interviews** — 8–10 AI-generated questions in 4 formats (HR, technical, stress, behavioral), then feedback and scores for the answers
- **Skill tests** — 9 categories, single-choice, multiple-choice and open questions, difficulty 1–5, time limits, pass score, AI-generated tests
- **Certificates** — users can add diplomas, certificates and courses with files
- **Accounts** — registration, profile, JWT authentication, admin views

## Tech stack

| Part | Tools |
|---|---|
| Frontend | React 18, React Router, Material UI, Axios |
| Backend | Python, Django 4.2, Django REST Framework |
| Auth | JWT (djangorestframework-simplejwt) |
| Database | PostgreSQL |
| AI | Google Gemini 2.5 Flash (google-generativeai) |
| Resume parsing | PyPDF2, python-docx |
| Jobs data | HeadHunter API |

## API overview

| Prefix | What it does |
|---|---|
| `/api/auth/` | registration, login, profile |
| `/api/resumes/` | upload, parsing, AI analysis, cover letters |
| `/api/vacancies/` | job search (HeadHunter), saved vacancies |
| `/api/applications/` | job applications |
| `/api/interviews/` | mock interviews and AI feedback |
| `/api/testing/` | skill tests, sessions, results, certificates |

## Getting started

```bash
git clone https://github.com/erkezhanab/career-assistant.git
cd career-assistant/career_assistant/backend

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (never commit it):

```
SECRET_KEY=your-django-secret-key
DEBUG=True
POSTGRES_DB=career_assistant
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
GEMINI_API_KEY=your-gemini-api-key
```

Then:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The API runs at http://localhost:8000. Uploads are limited to 10 MB (PDF, DOC, DOCX).

## Roadmap

- [ ] Background jobs with Celery and Redis
- [ ] Automated tests
- [ ] Docker setup

## Author

**Yerkezhan Abil** · erkezhanabil@gmail.com · [LinkedIn](https://www.linkedin.com/in/erkezhanabil)
