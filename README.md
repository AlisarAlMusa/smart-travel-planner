# Smart Travel Planner

## Project Overview

This project is a Smart Travel Planner built during AI Engineering Week 4. It combines:

- a retrieval system backed by Postgres + pgvector
- a trained ML pipeline for travel-style prediction
- a FastAPI backend
- a LangGraph agent that combines RAG, ML, and live weather into one final answer

The design goal is simple: the agent should not guess everything with an LLM. Instead, it should retrieve destination evidence, use the trained ML model for travel-style prediction, fetch live conditions, and then synthesize those signals into one helpful recommendation.

## Features

- RAG retrieval over embedded Wikivoyage destination chunks
- ML-based travel-style prediction using the trained sklearn pipeline
- Live weather checks with retries and caching
- LangGraph orchestration
- JWT auth with signup and login
- Postgres persistence for users, agent runs, and tool calls
- Structured JSON logging
- Dockerized pgvector database

## Architecture Diagram

```text
┌──────────────────────┐
│ Frontend / Client    │
│ user travel request  │
└──────────┬───────────┘
           │ HTTP
           ▼
┌────────────────────────────────────────────┐
│ FastAPI Backend                            │
│ POST /agent/run                            │
│ JWT auth + persistence                     │
└──────────┬─────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────┐
│ LangGraph Agent                            │
│ 1. classify_travel_style                   │
│ 2. retrieve_destinations                   │
│ 3. get_live_conditions                     │
│ 4. final synthesis                         │
└───────┬─────────────────┬──────────────────┘
        │                 │
        │                 │
        ▼                 ▼
┌──────────────────┐   ┌─────────────────────┐
│ RAG Service      │   │ Weather Service     │
│ pgvector search  │   │ Open-Meteo          │
└───────┬──────────┘   └─────────────────────┘
        │
        ▼
┌────────────────────────────────────────────┐
│ Postgres + pgvector                        │
│ destination_chunks                         │
│ users                                      │
│ agent_runs                                 │
│ tool_calls                                 │
└────────────────────────────────────────────┘
        ▲
        │
┌───────┴────────────────────────────────────┐
│ ML Service                                  │
│ LLM extracts features only                  │
│ sklearn pipeline predicts travel style      │
└────────────────────────────────────────────┘
```

This diagram is also mirrored in `ARCHITECTURE.md` with the design tradeoffs behind the flow.

## Tech Stack

- FastAPI
- LangGraph
- Azure OpenAI
- PostgreSQL
- pgvector
- SQLAlchemy
- scikit-learn
- Open-Meteo
- React
- TypeScript
- Vite
- pytest
- uv

## Agent Explanation

The agent has exactly 3 tools:

1. `retrieve_destinations`
2. `classify_travel_style`
3. `get_live_conditions`

Flow:

1. The user sends a travel preference query.
2. The cheap Azure deployment extracts structured ML features from the user request only.
3. The trained ML pipeline predicts the trip style the user wants.
4. The cheap Azure deployment rewrites the retrieval query using the user request plus the predicted style.
5. The retrieval tool searches pgvector for similar destinations.
6. The live conditions tool fetches weather for the retrieved destinations.
7. The strong Azure deployment synthesizes all signals into one final answer.

Important guardrail:

- the LLM never predicts travel style directly
- the ML pipeline remains the only style predictor

## Deliverables Documentation

### Dataset Labeling Rules

The supervised dataset is stored in `data/dests_1200.csv`. Each row represents a destination/place variant with structured travel features and a `travel_style` label.

Input feature groups:

- Budget and climate: `avg cost (usd/day)`, `avg_temp_year`
- Activity scores from 0 to 10: hiking, beach, nightlife, culture, food, adventure, nature, safety
- Categorical context: `accommodation_type`, `terrain_type`

Label set:

| Label | Main labeling signals |
| --- | --- |
| `Adventure` | high hiking/adventure/nature scores, often mountain or nature terrain |
| `Budget` | lower daily cost, simpler accommodation, good value signals |
| `Culture` | high culture/food scores, urban or heritage-heavy places |
| `Family` | high safety, balanced activities, lower nightlife emphasis |
| `Luxury` | higher daily cost, resort/apartment style, comfort-oriented signals |
| `Relaxation` | beach/nature/food signals, slower pace, coastal or resort context |

The target label is intentionally predicted by the sklearn model, not by the LLM. At runtime, the LLM only extracts the structured feature payload from the user's request, then `MLService.predict_style()` runs the trained pipeline.

### Chunking And Retrieval Rationale

RAG source content comes from cleaned Wikivoyage destination documents. The chunking strategy is deliberately simple and inspectable:

- target chunk size: about `1000` words/tokens by approximation
- overlap: `150` words/tokens
- maximum chunks per destination: `3`
- split on word boundaries

Why this design:

- Full destination pages are too large to embed as single records.
- Overlap preserves useful context around boundaries.
- A small max chunk count keeps the demo database compact and retrieval fast.
- pgvector keeps text, metadata, and embeddings in the same Postgres database as the app.

At query time, the agent rewrites the user's request into a concise semantic search query, embeds it, and retrieves the top matching destination chunks with cosine similarity.

### Model Comparison Table

The ML training notebook writes model results to `artifacts/results.csv`. The final artifact is stored at `artifacts/model.joblib`.

| Model | Notes | Test accuracy | Test F1 | Test precision | Test recall |
| --- | --- | ---: | ---: | ---: | ---: |
| Logistic Regression | baseline | 0.9889 | 0.9889 | 0.9890 | 0.9889 |
| Random Forest | baseline | 0.9861 | 0.9861 | 0.9865 | 0.9861 |
| Gradient Boosting | baseline | 0.9889 | 0.9889 | 0.9892 | 0.9889 |
| Tuned Logistic Regression | tuned/final selected family | 0.9917 | 0.9917 | 0.9917 | 0.9917 |

Operational LLM comparison:

| Model role | Attempted deployment | Result | Decision |
| --- | --- | --- | --- |
| Small/cheap JSON model | `DeepSeek-R1` | Unreliable for strict JSON feature extraction, even after a stronger prompt | Not used for now |
| Strong/general model | `DeepSeek-V3.2` | Returned the required JSON more reliably and worked for synthesis | Used for both cheap and strong routes temporarily |

Important lesson: the weak model was the unreliable JSON step, not the graph or tool code. The backend now logs invalid JSON and classification failures so this is visible in the terminal.

### Per-Query Cost Breakdown

The backend tracks token usage per agent run and persists it in `agent_runs.total_tokens` plus `agent_runs.estimated_cost`.

Cost formula:

```text
input_cost = prompt_tokens / 1000 * MODEL_INPUT_COST_PER_1K
output_cost = completion_tokens / 1000 * MODEL_OUTPUT_COST_PER_1K
request_cost = input_cost + output_cost
```

Per `/agent/run`, expected LLM calls:

| Step | Purpose | Deployment route | Cost source |
| --- | --- | --- | --- |
| 1 | Extract ML features for classifier | cheap route | `CHEAP_MODEL_*_COST_PER_1K` |
| 2 | Rewrite retrieval query | cheap route | `CHEAP_MODEL_*_COST_PER_1K` |
| 3 | Final recommendation synthesis | strong route | `STRONG_MODEL_*_COST_PER_1K` |

Weather and sklearn inference do not add token cost. Embedding cost for ingestion/query embedding depends on Azure pricing and can be documented separately if enabled in the deployed pricing settings.

Example breakdown template to fill from one real run:

| Component | Prompt tokens | Completion tokens | Estimated cost |
| --- | ---: | ---: | ---: |
| Feature extraction | from logs/tool call | from logs/tool call | calculated |
| Retrieval rewrite | from logs/tool call | from logs/tool call | calculated |
| Final synthesis | from logs/tool call | from logs/tool call | calculated |
| Total | `agent_runs.total_tokens` | included above | `agent_runs.estimated_cost` |

### LangSmith Trace Screenshot

LangSmith tracing is supported, but the screenshot needs to be captured from your own LangSmith project after running the app.

To create the screenshot:

1. Add these values to `travel-dest-backend/.env`:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=travel-planner-agent
```

2. Restart FastAPI.
3. Run one request through the frontend or Swagger: `POST /agent/run`.
4. Open LangSmith, go to the `travel-planner-agent` project, and open the latest trace.
5. Take a screenshot showing the LangGraph/tool sequence.
6. Save it as something like `docs/langsmith-trace.png`.
7. Add it here:

```md
![LangSmith trace](docs/langsmith-trace.png)
```

### Optional Extensions Completed

- React + TypeScript frontend with login, signup, protected routes, chat UI, and history page
- Tool trace panel showing tool status, input, output, and latency
- JWT authentication and user-specific history
- Persistent `agent_runs` and `tool_calls`
- Live weather tool with Open-Meteo integration
- Structured JSON logging with secret redaction
- Config validation for required `.env` values
- Graceful graph behavior when classification fails
- CORS support for local Vite frontend development

## How To Run

### 1. Install dependencies

```bash
uv venv
source .venv/bin/activate
uv sync
```

### 2. Start Docker Postgres + pgvector

```bash
docker compose up -d
```

### 3. Configure backend environment

Create `travel-dest-backend/.env` from `travel-dest-backend/.env.example`.

Required backend variables:

- `DATABASE_URL`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_CHEAP_DEPLOYMENT`
- `AZURE_OPENAI_STRONG_DEPLOYMENT`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- `JWT_SECRET_KEY`

Create `travel-dest-frontend/.env` from `travel-dest-frontend/.env.example`.

Required frontend variable:

- `VITE_API_BASE_URL=http://localhost:8000`

### 4. Run the ingestion pipeline if needed

```bash
cd travel-dest-backend
python -m rag.fetch_wikivoyage
python -m rag.clean_documents
python -m rag.chunk_documents
python -m rag.embed_and_store
```

### 5. Run the backend

```bash
cd travel-dest-backend
uv run uvicorn main:app --reload
```

### 6. Run the frontend

```bash
cd travel-dest-frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, usually:

```text
http://localhost:5173
```

## Repository Notes

This repo uses one root `.gitignore` for the whole project. Local secrets, virtual environments, `node_modules`, frontend build output, Python caches, logs, and editor noise are ignored. Safe example files such as `.env.example` remain tracked.

## Example Request/Response

### Signup

```http
POST /auth/signup
Content-Type: application/json

{
  "email": "demo@example.com",
  "password": "examplepass123"
}
```

### Agent run

```http
POST /agent/run
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "I want a warm destination with beaches, good food, and a relaxed pace."
}
```

### Example response shape

```json
{
  "agent_run_id": "uuid",
  "final_answer": "Portugal looks strongest overall because...",
  "total_tokens": 1234,
  "estimated_cost": 0.0123,
  "retrieval": {
    "status": "success",
    "rewritten_query": "warm beach food relaxed destination",
    "destinations": []
  },
  "trip_style_prediction": {
    "status": "success",
    "prediction": {
      "user_query": "I want a warm destination with beaches, good food, and a relaxed pace.",
      "predicted_style": "Relaxation",
      "confidence": 0.81,
      "extracted_features": {}
    }
  },
  "live_conditions": {
    "status": "success",
    "conditions": []
  },
  "tool_calls": []
}
```

## Cost + Model Routing

The backend uses two Azure OpenAI deployments:

- cheap deployment:
  - query rewriting
  - feature extraction
  - tool argument cleanup style tasks
- strong deployment:
  - final synthesis

This keeps mechanical work on the cheaper model and reserves the stronger model for the user-facing answer.

Token usage is tracked and stored per run, and estimated cost is computed from configurable per-1K token prices in settings.

## More Documentation

- System design: [ARCHITECTURE.md](/Users/alisaralmusa/Desktop/AIE%20Bootcamp/Week%204%20-%20project/ARCHITECTURE.md)
