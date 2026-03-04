"""Tests for EventHandler core behaviour."""

import pytest

from eventbus.core.handler import EventHandler


class TestEventHandlerInit:
    def test_name_is_stored(self) -> None:
        handler = EventHandler("my-handler")
        assert handler.name == "my-handler"

    def test_active_by_default(self) -> None:
        handler = EventHandler("h")
        assert handler._active is True

    def test_deactivate_sets_flag(self) -> None:
        handler = EventHandler("h")
        handler.deactivate()
        assert handler._active is False

    def test_handle_noop_when_inactive(self) -> None:
        handler = EventHandler("h")
        handler.deactivate()
        # Should not raise even with an empty event
        handler.handle({})
