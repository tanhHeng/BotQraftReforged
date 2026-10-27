"""Media message content. Construction validates and snapshots sources; MessageSender uploads them."""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
from threading import Lock
from typing import IO, ClassVar
from typing_extensions import Self

MAX_MEDIA_SIZE = 200 * 1024 * 1024
_MD5_10M_SIZE = 10002432
_DIGEST_BLOCK = 1024 * 1024

MediaSource = str | os.PathLike | bytes | bytearray | memoryview | IO[bytes]


class QMediaBase:
    """One QQ media message: image, video, voice or file. Not combinable with text or keyboards."""
    file_type: ClassVar[int]

    def __init__(self: Self, source: MediaSource, *, name: str | None = None) -> None:
        """Validate a media source and take the snapshot required for a later upload.

        :param source: An http(s) URL string, a local path, bytes-like data, or a readable seekable binary stream.
            Local files must be passed as os.PathLike; other strings are rejected. Streams are read from their
            current position and must stay open and unmodified until the send Future completes.
        :param name: File name sent to QQ. Required for bytes and streams; defaults to the path name for files.
        :raises TypeError: The class is abstract or the source type is unsupported.
        :raises ValueError: The URL, path, stream, name or size is invalid.
        """
        if type(self) is QMediaBase:
            raise TypeError('QMediaBase is abstract; use QImage, QVideo, QVoice or QFile')
        if name is not None:
            _check_name(name)
        self._url: str | None = None
        self._path: Path | None = None
        self._data: bytes | None = None
        self._stream: IO[bytes] | None = None
        self._start = 0
        if isinstance(source, str):
            if not source.startswith(('http://', 'https://')):
                raise ValueError('str media sources must be http(s) URLs; use pathlib.Path for local files')
            self._url = source
        elif isinstance(source, os.PathLike):
            path = Path(source)
            if not path.is_file():
                raise ValueError('media path is not an existing regular file')
            if not os.access(path, os.R_OK):
                raise ValueError('media path is not readable')
            _check_size(path.stat().st_size)
            self._path = path
            name = path.name if name is None else name
        elif isinstance(source, (bytes, bytearray, memoryview)):
            self._data = bytes(source)
            _check_size(len(self._data))
        elif isinstance(source, io.TextIOBase):
            raise TypeError('media streams must be binary')
        elif all(callable(getattr(source, method, None)) for method in ('read', 'seek', 'tell', 'seekable', 'readable')):
            if not source.readable() or not source.seekable():
                raise ValueError('media streams must be readable and seekable')
            self._start = source.tell()
            end = source.seek(0, io.SEEK_END)
            source.seek(self._start)
            _check_size(end - self._start)
            self._stream = source
        else:
            raise TypeError('media source must be an http(s) URL, os.PathLike, bytes-like data or a binary stream')
        if name is None and self._url is None:
            raise ValueError('name is required for bytes and stream media sources')
        self.name = name

    @property
    def url(self: Self) -> str | None:
        """The http(s) URL source, or None for local and in-memory sources."""
        return self._url

    def _open(self: Self) -> _MediaReader:
        """Open a reader over the uploaded byte range; call close when the upload ends."""
        if self._path is not None:
            return _MediaReader(open(self._path, 'rb'), 0, owned=True)
        if self._data is not None:
            return _MediaReader(io.BytesIO(self._data), 0, owned=True)
        if self._stream is not None:
            return _MediaReader(self._stream, self._start, owned=False)
        raise ValueError('URL media sources are uploaded by URL')

    def __repr__(self: Self) -> str:
        source = self._url if self._url is not None else self._path if self._path is not None else 'bytes' if self._data is not None else 'stream'
        return f'{type(self).__name__}({source!r}, name={self.name!r})'


class QImage(QMediaBase):
    """Image media (file_type=1); supported formats and size downgrades are decided by QQ."""
    file_type = 1


class QVideo(QMediaBase):
    """Video media (file_type=2)."""
    file_type = 2


class QVoice(QMediaBase):
    """Voice media (file_type=3); QQ expects silk audio and BotQraft does not transcode."""
    file_type = 3


class QFile(QMediaBase):
    """File media (file_type=4), shown as a downloadable file card."""
    file_type = 4


class _MediaReader:
    """Thread-safe positional reads; close waits for an in-flight read."""

    def __init__(self: Self, file: IO[bytes], start: int, *, owned: bool) -> None:
        self._file = file
        self._start = start
        self._owned = owned
        self._lock = Lock()
        self._closed = False

    def read(self: Self, offset: int, length: int) -> bytes:
        """Read up to length bytes at offset, looping over short reads; fewer bytes only at end of data."""
        chunks = []
        with self._lock:
            if self._closed:
                raise ValueError('media reader is closed')
            self._file.seek(self._start + offset)
            while length > 0:
                data = self._file.read(length)
                if not isinstance(data, bytes):
                    raise TypeError('media stream must return bytes')
                if not data:
                    break
                chunks.append(data)
                length -= len(data)
        return b''.join(chunks)

    def read_part(self: Self, offset: int, length: int) -> tuple[bytes, str]:
        """Read exactly one planned chunk and its MD5, off the network loop."""
        data = self.read(offset, length)
        if len(data) != length:
            raise ValueError('media source changed during upload')
        return data, hashlib.md5(data).hexdigest()

    def digest(self: Self) -> dict[str, str | int]:
        """Read the whole range once and return size, md5, sha1 and md5_10m."""
        md5, sha1, md5_10m = hashlib.md5(), hashlib.sha1(), hashlib.md5()
        size = 0
        while True:
            block = self.read(size, _DIGEST_BLOCK)
            if not block:
                break
            md5.update(block)
            sha1.update(block)
            if size < _MD5_10M_SIZE:
                md5_10m.update(block[:_MD5_10M_SIZE - size])
            size += len(block)
            if size > MAX_MEDIA_SIZE:
                break
        _check_size(size)
        return {'size': size, 'md5': md5.hexdigest(), 'sha1': sha1.hexdigest(), 'md5_10m': md5_10m.hexdigest()}

    def close(self: Self) -> None:
        with self._lock:
            if not self._closed:
                self._closed = True
                if self._owned:
                    self._file.close()


def _check_size(size: int) -> None:
    if size <= 0:
        raise ValueError('media must not be empty')
    if size > MAX_MEDIA_SIZE:
        raise ValueError('media exceeds the 200 MiB QQ upload limit')


def _check_name(name: str) -> None:
    if not isinstance(name, str) or not name.strip():
        raise ValueError('media name must be a non-empty string')
    if any(char in name for char in '/\\') or any(ord(char) < 32 for char in name):
        raise ValueError('media name must not contain path separators or control characters')
