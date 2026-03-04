"""Auth plugin — EventHandler subclass that enforces token validation."""

from eventbus.core.handler import EventHandler


class AuthHandler(EventHandler):
    """Validates auth tokens on every event before forwarding."""

    def __init__(self, name: str, secret: str) -> None:
        super().__init__(name)
        self._secret = secret

    def _process(self, payload: dict) -> None:
        token = payload.get("token", "")
        if token != self._secret:
            raise PermissionError(
                f"EventHandler({self.name}): invalid token"
            )
