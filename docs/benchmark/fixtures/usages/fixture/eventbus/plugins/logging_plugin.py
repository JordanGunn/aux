"""Logging plugin — extends EventHandler to emit structured logs."""

import logging

from eventbus.core.handler import EventHandler

logger = logging.getLogger(__name__)


class LoggingHandler(EventHandler):
    """An EventHandler subclass that logs every event it processes."""

    def __init__(self, name: str, level: int = logging.INFO) -> None:
        super().__init__(name)
        self._level = level

    def _process(self, payload: dict) -> None:
        logger.log(self._level, "EventHandler(%s) received: %s", self.name, payload)
