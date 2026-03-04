"""HTML extraction path: fetch → extract → clean text or markdown."""

from __future__ import annotations

from typing import Literal


def extract_html(body: str, mode: Literal["text", "markdown"]) -> str:
    """Extract main content from an HTML document.

    Degradation chain:
    1. trafilatura (if installed) — best for articles/docs
    2. html2text (if installed)  — HTML→Markdown fallback
    3. stdlib html.parser         — emergency tag-stripping fallback

    Args:
        body: Raw HTML string.
        mode: "text" for clean plain text, "markdown" for Markdown-formatted output.

    Returns:
        Extracted text. Never empty if body is non-empty (stdlib fallback ensures this).
    """
    if mode == "markdown":
        return _extract_markdown(body)
    return _extract_text(body)


def _extract_text(body: str) -> str:
    """Extract clean plain text from HTML."""
    # 1. Try trafilatura
    try:
        import trafilatura

        result = trafilatura.extract(
            body,
            include_comments=False,
            include_tables=True,
            output_format="txt",
        )
        if result:
            return result
    except ImportError:
        pass

    # 2. Try html2text (returns markdown-ish, but better than nothing)
    try:
        import html2text

        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        result = h.handle(body)
        if result and result.strip():
            return result
    except ImportError:
        pass

    # 3. Stdlib fallback
    return _strip_tags(body)


def _extract_markdown(body: str) -> str:
    """Extract HTML content as Markdown."""
    # 1. Try trafilatura with markdown output
    try:
        import trafilatura

        result = trafilatura.extract(
            body,
            include_comments=False,
            include_tables=True,
            output_format="markdown",
        )
        if result:
            return result
    except ImportError:
        pass

    # 2. Try html2text
    try:
        import html2text

        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        result = h.handle(body)
        if result and result.strip():
            return result
    except ImportError:
        pass

    # 3. Stdlib fallback
    return _strip_tags(body)


def _strip_tags(body: str) -> str:
    """Remove HTML tags using stdlib html.parser as a last resort."""
    from html.parser import HTMLParser

    class _Stripper(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self._parts: list[str] = []
            self._skip = False

        def handle_starttag(self, tag: str, attrs) -> None:
            if tag in ("script", "style", "head"):
                self._skip = True

        def handle_endtag(self, tag: str) -> None:
            if tag in ("script", "style", "head"):
                self._skip = False
            elif tag in ("p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
                self._parts.append("\n")

        def handle_data(self, data: str) -> None:
            if not self._skip:
                self._parts.append(data)

        def get_text(self) -> str:
            return "".join(self._parts)

    stripper = _Stripper()
    stripper.feed(body)
    return stripper.get_text()
