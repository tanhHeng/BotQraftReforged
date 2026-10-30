"""Sequential, rate-limited HTTP fetching and content-addressed image storage."""
from __future__ import annotations

import base64
import hashlib
import http.client
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote_to_bytes, urlsplit

from typing_extensions import Self

from botqraft.constants import core_constant


class FetchError(OSError):
    """An HTTP request failed, timed out or returned an error status."""


@dataclass(frozen=True)
class Response:
    url: str
    content_type: str
    body: bytes


class HttpClient:
    def __init__(self: Self, timeout: float, delay: float) -> None:
        self.timeout = timeout
        self.delay = delay
        self.user_agent = 'BotQraft/{} (official docs fetcher)'.format(core_constant.VERSION)
        self._last_request = 0.0

    def get(self: Self, url: str) -> Response:
        """Fetch a URL after waiting out the request delay; redirects are followed.

        :param url: Absolute HTTP(S) URL.
        :return: Final URL after redirects, lowercased media type and body.
        :raises FetchError: Network failure, timeout or HTTP error status.
        """
        wait = self.delay - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={'User-Agent': self.user_agent})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return Response(response.geturl(), response.headers.get_content_type(), response.read())
        except (OSError, http.client.HTTPException) as error:
            raise FetchError('{}: {}'.format(url, error)) from error
        finally:
            self._last_request = time.monotonic()

    def text(self: Self, url: str) -> tuple[str, str]:
        """Fetch a UTF-8 page.

        :param url: Absolute HTTP(S) URL.
        :return: Decoded text and the final URL after redirects.
        :raises FetchError: Network failure, timeout or HTTP error status.
        """
        response = self.get(url)
        return response.body.decode('utf-8', errors='replace'), response.url


class AssetStore:
    EXTENSIONS = {
        'image/png': '.png', 'image/jpeg': '.jpg', 'image/gif': '.gif',
        'image/svg+xml': '.svg', 'image/webp': '.webp', 'image/avif': '.avif',
        'image/bmp': '.bmp', 'image/x-icon': '.ico',
    }

    def __init__(self: Self, output_dir: Path, client: HttpClient) -> None:
        self.output_dir = output_dir
        self.client = client
        self.cache: dict[str, PurePosixPath] = {}

    def save(self: Self, url: str) -> PurePosixPath:
        """Store an image under ``_assets/`` named by its SHA-256, downloading each URL once.

        :param url: HTTP(S) or ``data:`` image URL.
        :return: Path relative to the output directory.
        :raises ValueError: Unsupported URL scheme or non-image content.
        :raises OSError: Download or file write failure.
        """
        if url in self.cache:
            return self.cache[url]
        if url.startswith('data:'):
            metadata, payload = url[5:].split(',', 1)
            content_type = metadata.split(';', 1)[0].lower()
            raw = unquote_to_bytes(payload)
            data = base64.b64decode(raw, validate=True) if ';base64' in metadata else raw
        else:
            if urlsplit(url).scheme not in {'http', 'https'}:
                raise ValueError('Unsupported image URL: {}'.format(url))
            response = self.client.get(url)
            content_type, data = response.content_type, response.body
        extension = self.EXTENSIONS.get(content_type)
        if extension is None:
            raise ValueError('Response is not a supported image: {!r} ({})'.format(content_type, url))
        relative = PurePosixPath('_assets', hashlib.sha256(data).hexdigest() + extension)
        destination = self.output_dir.joinpath(*relative.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        self.cache[url] = relative
        return relative
