"""Backend entrypoint for running the FastAPI application locally."""

from app import create_app


# Expose the ASGI app so uvicorn can import `main:app`.
app = create_app()
