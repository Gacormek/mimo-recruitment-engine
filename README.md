# 🧠 MiMo Recruitment Engine

**AI-Powered Recruitment Pipeline with 7 Coordinated Agents**

An intelligent hiring system powered by the MiMo LLM that automates the full recruitment lifecycle — from resume parsing to final hiring recommendations.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FASTAPI APPLICATION                          │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────────────┐  │
│  │ REST API │  │WebSocket │  │ Dashboard │  │   Agent Kernel    │  │
│  │ Routes   │  │  Events  │  │  (HTML)   │  │  (Lifecycle Mgr)  │  │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  └────────┬──────────┘  │
│       │              │              │                 │              │
│       └──────────────┴──────────────┴─────────────────┘              │
│                              │                                       │
│  ┌───────────────────────────┴───────────────────────────────────┐  │
│  │                     AGENT PIPELINE                            │  │
│  │                                                               │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐              │  │
│  │  │ ParseAgent │→ │ MatchAgent │→ │ ScoreAgent │              │  │
│  │  │ (Resume)   │  │ (Matching) │  │ (Scoring)  │              │  │
│  │  └────────────┘  └────────────┘  └────────────┘              │  │
│  │        │               │              │                       │  │
│  │  ┌────────────────┐ ┌─────────────┐ ┌──────────────────────┐ │  │
│  │  │QuestionAgent   │ │EvaluateAgent│ │ CompareAgent         │ │  │
│  │  │(Gen Questions) │ │(Score Ans)  │ │ (Rank Candidates)    │ │  │
│  │  └────────────────┘ └─────────────┘ └──────────────────────┘ │  │
│  │                          │                                    │  │
│  │                    ┌────────────┐                              │  │
│  │                    │ReportAgent │                              │  │
│  │                    │(Hiring Rpt)│                              │  │
│  │                    └────────────┘                              │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│  ┌───────────────────────────┴───────────────────────────────────┐  │
│  │              MiMo LLM (xmtp/mimo-v2.5-pro)                   │  │
│  │         Endpoint: http://your-mimo-server:20128/v1               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│  ┌───────────────────────────┴───────────────────────────────────┐  │
│  │          SQLite (WAL Mode) — Candidates, Jobs, Scores...     │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Purpose |
|-------|---------|
| **ParseAgent** | Extract skills, experience, education from resumes (PDF/text) |
| **MatchAgent** | Match candidate profiles to job requirements (skill overlap, experience fit) |
| **ScoreAgent** | Holistic candidate scoring with weighted criteria (technical, experience, education, cultural fit) |
| **QuestionAgent** | Generate role-specific interview questions (technical + behavioral) |
| **EvaluateAgent** | Analyze and score interview responses with detailed feedback |
| **CompareAgent** | Side-by-side candidate comparison and ranking |
| **ReportAgent** | Generate hiring recommendation reports with executive summaries |

## File Structure

```
mimo-recruitment-engine/
├── README.md
├── requirements.txt
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry, lifespan, agent registration
│   ├── kernel.py             # AgentKernel — lifecycle, scheduling, coordination
│   ├── database.py           # SQLite WAL mode, schema, query helpers
│   ├── config.py             # Configuration (paths, MiMo endpoint, server)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py     # Abstract base class for all agents
│   │   ├── parse_agent.py    # Resume/CV parsing agent
│   │   ├── match_agent.py    # Candidate-job matching agent
│   │   ├── score_agent.py    # Holistic scoring agent
│   │   ├── question_agent.py # Interview question generator
│   │   ├── evaluate_agent.py # Answer evaluation agent
│   │   ├── compare_agent.py  # Candidate comparison agent
│   │   └── report_agent.py   # Hiring report generator
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py         # REST API endpoints
│   │   └── websocket.py      # WebSocket real-time events
│   └── mimo/
│       ├── __init__.py
│       └── client.py         # MiMo LLM HTTP client
├── templates/
│   └── dashboard.html        # Dark-theme real-time dashboard
└── data/                     # SQLite database storage
```

## Dashboard

Professional dark-theme dashboard with 8 tabs:

- **Candidates** — View, add, manage candidate profiles
- **Jobs** — Create and manage job positions
- **Pipeline** — Execute the full AI recruitment pipeline
- **Scores** — View candidate scoring breakdowns
- **Questions** — Browse generated interview questions
- **Comparisons** — Side-by-side candidate rankings
- **Reports** — Hiring recommendation reports
- **System** — Agent status, execution history

## Quick Start

### Local

```bash
pip install -r requirements.txt
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker

```bash
docker compose up --build
```

Then open http://localhost:8000

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/candidates` | List all candidates |
| POST | `/api/candidates` | Create candidate (with resume parsing) |
| GET | `/api/jobs` | List all jobs |
| POST | `/api/jobs` | Create job position |
| POST | `/api/match` | Match candidate to job |
| POST | `/api/score` | Score candidate for a job |
| POST | `/api/questions/generate` | Generate interview questions |
| POST | `/api/evaluate` | Evaluate interview answer |
| POST | `/api/compare` | Compare multiple candidates |
| POST | `/api/reports/generate` | Generate hiring report |
| GET | `/api/status` | System status |

## MiMo LLM Integration

The engine uses the MiMo LLM (`xmtp/mimo-v2.5-pro`) for all AI operations:

- **Endpoint**: `http://your-mimo-server:20128/v1`
- **Model**: `xmtp/mimo-v2.5-pro`
- **API Key**: `sk-hermes-mimo`

All agents send structured prompts to MiMo and parse JSON responses for consistent, machine-readable outputs.

## License

MIT
