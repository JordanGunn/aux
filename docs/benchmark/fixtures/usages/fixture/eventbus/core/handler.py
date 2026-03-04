"""Core event handler module — defines EventHandler."""


class EventHandler:
    """Base class for all event handlers in the eventbus system."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._active = True

    def handle(self, event: dict) -> None:
        """Process an incoming event."""
        if not self._active:
            return
        payload = event.get("payload", {})
        self._process(payload)

    def _process(self, payload: dict) -> None:
        """Internal processing hook — override in subclasses."""
        pass

    def deactivate(self) -> None:
        """Disable this handler."""
        self._active = False
