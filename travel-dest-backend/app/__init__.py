"""Application package entrypoint."""


def create_app():
    """Import the FastAPI factory lazily so utility imports stay lightweight."""
    from app.main import create_app as app_factory

    return app_factory()


__all__ = ["create_app"]
