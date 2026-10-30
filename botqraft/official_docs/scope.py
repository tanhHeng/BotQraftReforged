"""Crawl boundary, canonical document URLs and a stable URL-to-file mapping."""
from __future__ import annotations

from pathlib import PurePosixPath
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

from typing_extensions import Self

DEFAULT_BASE_URL = 'https://bot.q.qq.com/wiki/develop/api-v2/'
_WINDOWS_RESERVED = {'CON', 'PRN', 'AUX', 'NUL', *('COM{}'.format(i) for i in range(1, 10)), *('LPT{}'.format(i) for i in range(1, 10))}


class DocumentScope:
    def __init__(self: Self, base_url: str = DEFAULT_BASE_URL) -> None:
        """Bound crawling to HTML documents below one directory of one origin.

        :param base_url: Directory URL; a trailing ``index.html`` is ignored.
        :raises ValueError: The URL is not an absolute HTTP(S) URL.
        """
        parts = urlsplit(base_url)
        if parts.scheme not in {'http', 'https'} or not parts.netloc:
            raise ValueError('base_url must be an HTTP(S) URL: {}'.format(base_url))
        path = parts.path
        if path.endswith('index.html'):
            path = path[:-10]
        if not path.endswith('/'):
            path += '/'
        self.base_url = urlunsplit((parts.scheme, parts.netloc, path, '', ''))
        self.origin = (parts.scheme.lower(), parts.netloc.lower())
        self.root_path = unquote(path)

    def canonical(self: Self, href: str, page_url: str | None = None) -> str | None:
        """Resolve a link to its canonical in-scope document URL.

        :param href: Link target, possibly relative.
        :param page_url: Page the link appears on; defaults to the base URL.
        :return: URL without query or fragment, or None for assets, other sites and traversal.
        """
        parts = urlsplit(urljoin(page_url or self.base_url, href))
        if (parts.scheme.lower(), parts.netloc.lower()) != self.origin:
            return None
        path = unquote(parts.path)
        if not path.startswith(self.root_path):
            return None
        if any(part in {'.', '..'} for part in path.split('/')):
            return None
        if path.endswith('index.html'):
            path = path[:-10]
        if not (path.endswith('/') or path.endswith('.html')):
            return None
        return urlunsplit((*self.origin, quote(path, safe='/-._~'), '', ''))

    def output_path(self: Self, url: str) -> PurePosixPath:
        """Map a document URL to a relative Markdown path that is valid on Windows too.

        :param url: In-scope document URL.
        :return: Relative path; the site's ``autogen/`` directory becomes ``api-reference/``.
        :raises ValueError: The URL is outside the scope.
        """
        canonical = self.canonical(url)
        if canonical is None:
            raise ValueError('Document URL is out of scope: {}'.format(url))
        relative = unquote(urlsplit(canonical).path)[len(self.root_path):]
        relative = relative + 'index.md' if relative.endswith('/') or not relative else relative[:-5] + '.md'
        parts = PurePosixPath(relative).parts
        if parts[0] == 'autogen':
            parts = ('api-reference', *parts[1:])
        safe_parts = []
        for part in parts:
            # Percent-encode only characters Windows rejects, so Chinese names stay readable.
            encoded = ''.join('%{:02X}'.format(ord(char)) if char in '<>:"\\|?*%' or ord(char) < 32 else char for char in part)
            if encoded.split('.', 1)[0].upper() in _WINDOWS_RESERVED:
                encoded = '%{:02X}'.format(ord(encoded[0])) + encoded[1:]
            safe_parts.append(encoded)
        return PurePosixPath(*safe_parts)
