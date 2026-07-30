# AI Healthcare Assistant v2.0

A production-grade AI healthcare assistant that combines Large Language Models, Retrieval-Augmented Generation (RAG), and Agentic AI to answer medical questions using trusted medical knowledge bases.

## Features

- **ChatGPT-style UI** - Clean, modern interface with conversation history
- **User Authentication** - JWT-based auth with register/login
- **Persistent Chat History** - All conversations saved to database
- **Dark/Light/System Theme** - User-selectable themes
- **RAG Pipeline** - Retrieves relevant medical information
- **Memory** - Maintains context across follow-up questions
- **Medication Search** - Search drug information from 1mg.com
- **Medical Knowledge Base** - Comprehensive medical documents
- **Source Attribution** - Shows which documents informed each response

## Tech Stack

### Backend
- **FastAPI** - Web framework
- **SQLAlchemy** - Database ORM (SQLite/PostgreSQL)
- **ChromaDB** - Vector database for embeddings
- **Mistral AI** - LLM and embeddings
- **JWT** - Authentication tokens
- **BeautifulSoup4** - Web scraping

### Frontend
- **React 18** with TypeScript
- **React Router** - Client-side routing
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **Vite** - Build tool

## Project Structure

```
AI Healthcare Assistant/
├── backend/
│   ├── app/
│   │   ├── api/routes.py          # API endpoints
│   │   ├── core/config.py         # Configuration
│   │   ├── database/              # SQLAlchemy models
│   │   ├── models/schemas.py      # Pydantic models
│   │   ├── services/
│   │   │   ├── auth_service.py    # JWT authentication
│   │   │   ├── chat_history_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── retrieval_service.py
│   │   │   ├── conversation_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── ingestion_service.py
│   │   │   └── scraper/           # Medical data scraper
│   │   ├── dependencies.py
│   │   └── main.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/            # UI components
│   │   ├── context/               # Auth & Theme context
│   │   ├── pages/                 # Login, Register, Chat
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── medical_knowledge/         # Medical documents
│   └── healthcare.db              # SQLite database
└── scripts/
    └── ingest_documents.py
```

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- Mistral AI API key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env to add your Mistral API key
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Start Application

```bash
./start.sh
```

Or manually:

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register user |
| POST | /api/v1/auth/login | Login user |
| GET | /api/v1/auth/me | Get current user |
| POST | /api/v1/chat | Send message |
| GET | /api/v1/conversations | List conversations |
| GET | /api/v1/conversations/:id | Get conversation |
| POST | /api/v1/conversations | New conversation |
| PUT | /api/v1/conversations/:id/title | Rename conversation |
| DELETE | /api/v1/conversations/:id | Delete conversation |
| POST | /api/v1/reset | Reset conversation |
| GET | /api/v1/health | Health check |
| POST | /api/v1/ingest | Ingest documents |
| GET | /api/v1/stats | Collection stats |
| POST | /api/v1/search-medical | Search medications |

## Sample Questions

- "What are the symptoms of diabetes?"
- "How can I manage high blood pressure?"
- "What medications are used for heart disease?"
- "Is fasting safe for people with diabetes?"
- "What should I eat for a sore throat?"

## Disclaimer

This AI assistant provides informational support only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider.

## License

MIT License
