"""Event dispatcher — routes events to registered EventHandler instances."""

from eventbus.core.handler import EventHandler


class EventDispatcher:
    """Dispatches events to all registered handlers."""

    def __init__(self) -> None:
        self._handlers: list[EventHandler] = []

    def register(self, handler: EventHandler) -> None:
        """Add an EventHandler to the dispatch list."""
        self._handlers.append(handler)

    def dispatch(self, event: dict) -> None:
        """Send event to every registered EventHandler."""
        for handler in self._handlers:
            handler.handle(event)

    def unregister(self, handler: EventHandler) -> None:
        """Remove an EventHandler from the dispatch list."""
        self._handlers = [h for h in self._handlers if h is not handler]
