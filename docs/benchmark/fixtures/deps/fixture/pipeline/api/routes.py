"""Route definitions — depends only on server (highest instability)."""

from pipeline.api.server import Server


def register_routes(server: Server) -> dict:
    """Return a mapping of path → handler callable."""
    return {
        "/process": server.handle,
    }
