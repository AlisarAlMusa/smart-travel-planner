# Architecture

## System Flow

1. The user signs up or logs in and receives a JWT.
2. The client sends a travel request to `POST /agent/run`.
3. FastAPI authenticates the user and creates an `agent_runs` row.
4. LangGraph starts the agent workflow.
5. `classify_travel_style` extracts ML features from the user request and calls the trained sklearn pipeline.
6. `retrieve_destinations` rewrites the retrieval query with the predicted trip style and searches pgvector.
7. `get_live_conditions` fetches current weather per destination.
8. The strong Azure deployment synthesizes the final answer.
9. The backend persists tool calls, token usage, final answer, and estimated cost.

## Agent Design

The agent uses a simple, deterministic LangGraph workflow instead of an overly generic planner. This was chosen because:

- the product flow is known in advance
- the project is time-limited
- the tool order is fixed by the business requirement

Graph order:

1. classify
2. retrieve
3. live conditions
4. synthesize

This gives LangGraph observability and clean state transitions without introducing unnecessary autonomy.

## Tool Design

Exactly 3 tools are exposed:

1. `retrieve_destinations`
2. `classify_travel_style`
3. `get_live_conditions`

Every tool:

- validates input with Pydantic
- returns structured success or structured error
- never crashes the whole request on validation failure

An explicit allowlist is enforced in `app/agent/tool_registry.py`.

## RAG Design Decisions

### Why chunking

- destination pages are too large to embed as single blocks
- chunking improves semantic retrieval quality
- 150-token overlap preserves context between chunks

### Why pgvector

- same Postgres database as the app
- no extra vector database needed for this stage
- stores metadata, text, and embeddings together

## ML Pipeline Explanation

The ML artifact is loaded once at startup from `artifacts/model.joblib`.

The classifier does not let the LLM predict travel style directly.

Instead:

1. the cheap model extracts structured numeric/categorical features from the user request
2. the sklearn pipeline predicts the trip style the user is asking for

This preserves the role of the trained model and makes the behavior more explainable.

## Model Routing

Cheap deployment:

- query rewriting
- feature extraction
- JSON-style mechanical work

Strong deployment:

- final user-facing synthesis

This keeps cost down without weakening the final answer too much.

## DB Schema Explanation

Main tables:

- `destination_chunks`
- `users`
- `agent_runs`
- `tool_calls`

`agent_runs` stores:

- query
- final answer
- token usage
- estimated cost
- user ownership

`tool_calls` stores:

- tool name
- JSON input
- JSON output
- status
- latency
- error message

## Error Handling Strategy

- invalid tool args return structured tool errors
- external API failures are retried
- retry exhaustion becomes graceful tool failure
- one failed tool should not crash the whole request when partial output is still possible

## Retry Strategy

Retries use exponential backoff for:

- Azure OpenAI calls
- Open-Meteo weather calls
- Wikivoyage ingestion calls

The goal is to handle temporary network or provider instability without hiding persistent failures.

## Caching Decisions

- `lru_cache` is used for settings and shared OpenAI clients
- weather responses use a small in-memory TTL cache

Caching is intentionally simple to keep the code readable.

## Tradeoffs

1. The LangGraph flow is deterministic instead of a free-form tool-calling agent.
This is less flexible, but easier to debug and better aligned with the required flow.

2. The app uses synchronous SQLAlchemy sessions.
This is simpler and is acceptable because the main async pressure comes from external APIs.

3. Weather is implemented before FX and flights.
This prioritizes the most useful live condition signal under time constraints.

4. App tables are created by SQLAlchemy on startup, while `destination_chunks` still comes from the pgvector init SQL.
This keeps the agent tables simple without adding a migration system yet.
