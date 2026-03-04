"""Tests for EventDispatcher integration with EventHandler."""

from eventbus.core.dispatcher import EventDispatcher
from eventbus.core.handler import EventHandler


def test_dispatch_calls_handler() -> None:
    received: list[dict] = []

    class CollectorHandler(EventHandler):
        def _process(self, payload: dict) -> None:
            received.append(payload)

    dispatcher = EventDispatcher()
    handler = CollectorHandler("collector")
    dispatcher.register(handler)
    dispatcher.dispatch({"payload": {"key": "value"}})

    assert len(received) == 1
    assert received[0] == {"key": "value"}


def test_unregister_removes_handler() -> None:
    handler = EventHandler("h")
    dispatcher = EventDispatcher()
    dispatcher.register(handler)
    dispatcher.unregister(handler)

    # EventHandler should not receive events after unregister
    assert handler not in dispatcher._handlers
