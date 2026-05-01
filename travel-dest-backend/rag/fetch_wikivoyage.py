"""Fetch destination summaries from Wikivoyage and save them as raw JSON documents."""

from datetime import datetime, timezone
from pathlib import Path

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.rag import RawDestinationDocument
from rag.destinations import DESTINATIONS


logger = get_logger(__name__)


def destination_file_path(destination_name: str) -> Path:
    """Build a predictable JSON file name for one destination."""
    settings = get_settings()
    safe_name = destination_name.lower().replace(" ", "_")
    return settings.raw_data_path / f"{safe_name}.json"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def fetch_destination_extract(wikivoyage_title: str) -> str:
    """Call the Wikivoyage API and return the plain-text extract for one title."""
    settings = get_settings()
    response = requests.get(
        settings.WIKIVOYAGE_API_URL,
        params={
            "action": "query",
            "prop": "extracts",
            "explaintext": True,
            "titles": wikivoyage_title,
            "format": "json",
        },
        headers={
            "User-Agent": settings.WIKIVOYAGE_USER_AGENT,
            "Accept": "application/json",
        },
        timeout=settings.WIKIVOYAGE_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    pages = data.get("query", {}).get("pages", {})

    for page in pages.values():
        extract = page.get("extract", "")
        if extract.strip():
            return extract

    raise ValueError(f"No extract returned for {wikivoyage_title}")


def save_raw_document(document: RawDestinationDocument) -> None:
    """Write one validated raw destination document to disk."""
    settings = get_settings()
    settings.raw_data_path.mkdir(parents=True, exist_ok=True)
    file_path = destination_file_path(document.destination)
    file_path.write_text(document.model_dump_json(indent=2), encoding="utf-8")
    logger.info(
        "Saved raw destination document",
        extra={
            "event": "wikivoyage_fetch",
            "destination": document.destination,
            "file_path": str(file_path),
            "status": "saved",
        },
    )


def fetch_all_destinations() -> None:
    """Fetch all configured destinations and skip failures without stopping the pipeline."""
    for item in DESTINATIONS:
        destination_name = item["destination"]
        try:
            raw_text = fetch_destination_extract(item["wikivoyage_title"])
            document = RawDestinationDocument(
                destination=destination_name,
                source="wikivoyage",
                title=destination_name,
                wikivoyage_title=item["wikivoyage_title"],
                url=item["url"],
                raw_text=raw_text,
                fetched_at=datetime.now(timezone.utc),
            )
            save_raw_document(document)
        except Exception as exc:
            logger.error(
                "Failed to fetch destination from Wikivoyage",
                extra={
                    "event": "wikivoyage_fetch",
                    "destination": destination_name,
                    "status": "failed",
                    "error": str(exc),
                },
            )


def main() -> None:
    """Run the raw ingestion step from the command line."""
    fetch_all_destinations()


if __name__ == "__main__":
    main()
