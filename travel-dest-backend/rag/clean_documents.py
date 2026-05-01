"""Clean raw Wikivoyage text and save processed destination documents."""

import re
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.rag import ProcessedDestinationDocument, RawDestinationDocument


logger = get_logger(__name__)


def clean_text(raw_text: str) -> str:
    """Normalize whitespace and remove short noisy lines while keeping travel content."""
    normalized_text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    normalized_text = re.sub(r"[ \t]+", " ", normalized_text)

    cleaned_lines: list[str] = []
    for line in normalized_text.split("\n"):
        stripped_line = line.strip()
        if not stripped_line:
            cleaned_lines.append("")
            continue

        if len(stripped_line.split()) <= 1 and len(stripped_line) < 4:
            continue

        cleaned_lines.append(stripped_line)

    cleaned_text = "\n".join(cleaned_lines)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    return cleaned_text.strip()


def output_file_path(destination_name: str) -> Path:
    """Build the processed JSON file path for one destination."""
    settings = get_settings()
    safe_name = destination_name.lower().replace(" ", "_")
    return settings.processed_data_path / f"{safe_name}.json"


def process_file(file_path: Path) -> None:
    """Read one raw document, clean it, and save the processed version."""
    settings = get_settings()
    raw_document = RawDestinationDocument.model_validate_json(file_path.read_text(encoding="utf-8"))
    clean_content = clean_text(raw_document.raw_text)

    if not clean_content:
        logger.warning(
            "Skipping document with empty cleaned text",
            extra={
                "event": "document_clean",
                "destination": raw_document.destination,
                "file_path": str(file_path),
                "status": "skipped",
            },
        )
        return

    processed_document = ProcessedDestinationDocument(
        destination=raw_document.destination,
        source=raw_document.source,
        title=raw_document.title,
        wikivoyage_title=raw_document.wikivoyage_title,
        url=raw_document.url,
        clean_text=clean_content,
        processed_at=datetime.now(timezone.utc),
    )

    settings.processed_data_path.mkdir(parents=True, exist_ok=True)
    destination_file = output_file_path(processed_document.destination)
    destination_file.write_text(processed_document.model_dump_json(indent=2), encoding="utf-8")
    logger.info(
        "Saved processed destination document",
        extra={
            "event": "document_clean",
            "destination": processed_document.destination,
            "file_path": str(destination_file),
            "status": "saved",
        },
    )


def clean_all_documents() -> None:
    """Process every raw JSON file and skip bad files gracefully."""
    settings = get_settings()
    for file_path in sorted(settings.raw_data_path.glob("*.json")):
        try:
            process_file(file_path)
        except Exception as exc:
            logger.error(
                "Failed to clean destination document",
                extra={
                    "event": "document_clean",
                    "file_path": str(file_path),
                    "status": "failed",
                    "error": str(exc),
                },
            )


def main() -> None:
    """Run the cleaning step from the command line."""
    clean_all_documents()


if __name__ == "__main__":
    main()
