"""Pipeline configuration — stable leaf module, no internal imports."""


class Config:
    """Immutable runtime configuration container."""

    def __init__(self, data: dict) -> None:
        self._data = dict(data)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    @classmethod
    def from_env(cls) -> "Config":
        import os
        return cls(dict(os.environ))
