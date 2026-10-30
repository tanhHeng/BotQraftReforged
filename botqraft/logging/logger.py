"""Native logging and rotation with an independent name, QQ redaction and color formatting."""
from __future__ import annotations
from os import PathLike
from typing import TYPE_CHECKING, Any, Mapping
from typing_extensions import Self

if TYPE_CHECKING:
    from botqraft.runtime import Runtime
import json
import logging
import os
import re
from threading import RLock
from colorlog import ColoredFormatter
from mcdreforged.logging.file_handler import ZippingDayRotatingFileHandler
from mcdreforged.logging.logger import MCDReforgedLogger
from mcdreforged.logging.formatter import PluginIdAwareFormatter, NoColorFormatter
from mcdreforged.logging.stream_handler import SyncStdoutStreamHandler


class Logger(MCDReforgedLogger):
    DEFAULT_NAME = 'BotQraft'
    FILE_FORMATTER = PluginIdAwareFormatter(
        NoColorFormatter,
        '[%(name)s] [%(asctime)s.%(msecs)03d] [%(threadName)s/%(levelname)s] [%(filename)s:%(lineno)d(%(funcName)s)] [%(plugin_id)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    CONSOLE_FORMATTER = PluginIdAwareFormatter(
        ColoredFormatter,
        '[%(name)s] [%(asctime)s] [%(threadName)s/%(log_color)s%(levelname)s%(reset)s] [%(plugin_id)s]: %(message)s',
        datefmt='%H:%M:%S', log_colors=MCDReforgedLogger.LOG_COLORS,
    )
    PLAIN_CONSOLE_FORMATTER = PluginIdAwareFormatter(
        NoColorFormatter,
        '[%(name)s] [%(asctime)s] [%(threadName)s/%(levelname)s] [%(plugin_id)s]: %(message)s',
        datefmt='%H:%M:%S',
    )

    def __init__(self: Self, plugin_id: str | None = None) -> None:
        """Create a standalone logger that owns its console and file handlers.
        
        The native initializer is skipped on purpose: it registers every instance in
        MCDR's process-wide shared file handler, which BotQraft never configures.
        
        :param plugin_id: Plugin identifier attached to every record, or None for the runtime logger.
        :return: No return value.
        """
        logging.Logger.__init__(self, self.DEFAULT_NAME)
        self.setLevel(logging.INFO)
        self.file_handler: ZippingDayRotatingFileHandler | None = None
        self._plugin_id = plugin_id
        self.console_handler = SyncStdoutStreamHandler()
        self.console_handler.setFormatter(self.CONSOLE_FORMATTER)
        self.addHandler(self.console_handler)

    def _log(self: Self, level: int, msg: object, args: Any, *remaining_args: Any, **kwargs: Any) -> None:
        """Attach the plugin identifier and keep the caller's stack location.
        
        :param level: Numeric logging level.
        :param msg: Message or format string.
        :param args: Format arguments.
        :return: No return value.
        """
        if self._plugin_id is not None:
            extra = kwargs.get('extra') or {}
            extra[PluginIdAwareFormatter.PLUGIN_ID_KEY] = self._plugin_id
            kwargs['extra'] = extra
        # One extra frame for this override; logging.Logger._log defaults to 1.
        kwargs['stacklevel'] = kwargs.get('stacklevel', 1) + 1
        super()._log(level, msg, args, *remaining_args, **kwargs)

    def set_file(self: Self, file_path: str) -> None:
        """Write records to a daily rotating, zipped log file, replacing any previous file.
        
        :param file_path: Path of the active log file.
        :return: No return value.
        """
        if self.file_handler is not None:
            self.unset_file()
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        self.file_handler = ZippingDayRotatingFileHandler(file_path, self.ROTATE_DAY_COUNT)
        self.file_handler.setFormatter(self.FILE_FORMATTER)
        self.addHandler(self.file_handler)

    def unset_file(self: Self) -> None:
        """Detach and close the log file handler if one is set.
        
        :return: No return value.
        """
        if self.file_handler is not None:
            self.removeHandler(self.file_handler)
            self.file_handler.close()
            self.file_handler = None

    def setLevel(self: Self, level: int | str) -> None:
        """Set the log level and clear the directly constructed logger cache.
        
        :param level: Numeric logging level or standard level name.
        :return: No return value.
        """
        super().setLevel(level)
        # Directly constructed native loggers are absent from logging.manager's cache sweep.
        self._cache.clear()

    def set_console_color(self: Self, enabled: bool) -> None:
        """Select colored or plain standalone console formatting.
        
        :param enabled: Whether console colors should be enabled.
        :return: No return value.
        """
        self.console_handler.setFormatter(self.CONSOLE_FORMATTER if enabled else self.PLAIN_CONSOLE_FORMATTER)

    def set_debug_options(self: Self, debug_options: Mapping[str, bool]) -> None:
        """Apply native debug options while excluding the QQ raw-response switch.
        
        :param debug_options: Debug-option names and enabled states.
        :return: No return value.
        """
        super().set_debug_options({key: value for key, value in debug_options.items() if key != 'raw_response'})


class SecretFilter(logging.Filter):
    def __init__(self: Self) -> None:
        """Create a thread-safe registry of credentials to redact.
        
        :return: No return value.
        """
        super().__init__()
        self.secrets = set()
        self._lock = RLock()

    def add(self: Self, value: str | None) -> None:
        """Register a nonempty credential for redaction.
        
        :param value: Credential to redact; empty values are ignored.
        :return: No return value.
        """
        if value:
            with self._lock:
                self.secrets.add(str(value))

    def _sanitize(self: Self, text: str) -> str:
        with self._lock:
            secrets = sorted(self.secrets, key=len, reverse=True)
        for secret in secrets:
            text = text.replace(secret, '<redacted>')
        text = re.sub(r'(?i)((?:access_token|auth_token|clientSecret|secret|authorization)[\"\']?\s*[=:]\s*[\"\']?)[^\s,;\"\'\]}]+', r'\1<redacted>', text)
        text = re.sub(r'(?i)(QQBot\s+|Bearer\s+)[^\s,;\"\']+', r'\1<redacted>', text)
        # Presigned media URLs authorize uploads/downloads through their query string.
        text = re.sub(r'(?i)((?:presigned_url|raw_url)[\"\']?\s*[=:]\s*[\"\']?)[^\s,;\"\'\]}]+', r'\1<redacted>', text)
        return text

    def sanitize_response(self: Self, body: str | bytes) -> str:
        """Redact sensitive JSON fields and credentials, escaping unsafe output characters.
        
        :param body: Raw protocol response text or UTF-8 bytes.
        :return: Result of the operation.
        """
        if isinstance(body, bytes):
            body = body.decode('utf8', errors='replace')
        try:
            data = json.loads(body)
        except (ValueError, TypeError):
            data = body

        def redact(value: Any) -> Any:
            if isinstance(value, dict):
                return {key: '<redacted>' if key.lower() in {
                    'access_token', 'auth_token', 'token', 'clientsecret', 'client_secret',
                    'secret', 'authorization', 'session_id', 'presigned_url', 'raw_url',
                } else redact(item) for key, item in value.items()}
            if isinstance(value, list):
                return [redact(item) for item in value]
            if isinstance(value, str):
                if value.startswith(('ws://', 'wss://')):
                    return '<redacted>'
                return self._sanitize(value)
            return value

        rendered = json.dumps(redact(data), ensure_ascii=False, separators=(',', ':'))
        return rendered.translate({code: repr(chr(code))[1:-1] for code in (*range(127, 160), 0x2028, 0x2029)})

    def filter(self: Self, record: logging.LogRecord) -> bool:
        """Redact a log record message and exception text before emission.
        
        :param record: Log record to sanitize in place.
        :return: True to allow the sanitized record to be emitted.
        """
        record.msg, record.args = self._sanitize(record.getMessage()), ()
        if record.exc_info:
            record.exc_text = self._sanitize(logging.Formatter().formatException(record.exc_info))
        return True


def log_raw_response(runtime: Runtime, origin: str, body: str | bytes, *, operation: str | None = None, http_code: int | None = None) -> None:
    """Log a sanitized transport response only when raw-response debugging is enabled.
    
    :param runtime: Runtime providing configuration and the redacting logger.
    :param origin: Transport label used in the diagnostic.
    :param body: Raw protocol response text or UTF-8 bytes.
    :param operation: Optional human-readable HTTP operation label.
    :param http_code: HTTP response status, or None for non-HTTP transport.
    :return: No return value.
    """
    if not runtime.get_config().debug.get('raw_response', False):
        return
    rendered = runtime.logger.secret_filter.sanitize_response(body)
    if http_code is None:
        runtime.logger.debug('Raw response [%s] %s', origin, rendered)
    else:
        runtime.logger.debug('Raw response [%s] [%s] [http_code:%s] %s', origin, operation, http_code, rendered)


def create_logger(name: str = 'BotQraft', *, log_directory: str | PathLike[str] | None = None, debug: bool = False) -> Logger:
    """Create a standalone logger with shared secret redaction and optional file output.
    
    :param name: Root logger name.
    :param log_directory: Optional directory for the rotating BotQraft log file.
    :param debug: Whether to enable the DEBUG logging level.
    :return: Result of the operation.
    """
    logger = Logger()
    logger.name = name
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.secret_filter = SecretFilter()
    logger.console_handler.addFilter(logger.secret_filter)
    if log_directory is not None:
        from pathlib import Path
        logger.set_file(str(Path(log_directory) / 'botqraft.log'))
        logger.file_handler.addFilter(logger.secret_filter)
    return logger


def plugin_logger(logger: Logger, plugin_id: str) -> Logger:
    """Create a plugin logger sharing the runtime handlers and secret filter.
    
    :param logger: Runtime logger whose handlers are reused.
    :param plugin_id: Plugin identifier used as the child logger name.
    :return: Result of the operation.
    """
    child = Logger(plugin_id)
    child.setLevel(logger.level)
    child.removeHandler(child.console_handler)
    child.console_handler = logger.console_handler
    for handler in logger.handlers:
        child.addHandler(handler)
    child.secret_filter = logger.secret_filter
    return child
