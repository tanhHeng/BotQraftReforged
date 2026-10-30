"""Native copy/save/reset preference behavior with QQ-only identity keys."""
from __future__ import annotations
from typing import TYPE_CHECKING
from typing_extensions import Self

if TYPE_CHECKING:
    from botqraft.runtime import Runtime
    from botqraft.message.user import User
    from botqraft.command.command_source import QQCommandSource, ConsoleSource
import json
from pathlib import Path

from mcdreforged.preference.preference_manager import PreferenceManager as NativePreferenceManager, PreferenceItem, InvalidPreferenceSource
from mcdreforged.utils import file_utils

CONSOLE_ALIAS = '#@BotQraft_Console@#'
PREFERENCE_FILE_PATH = Path('config/botqraft/preferences.json')


class PreferenceManager(NativePreferenceManager):
    def __init__(self: Self, runtime: Runtime) -> None:
        """Initialize native preference behavior with QQ identity keys and standalone storage.
        
        :param runtime: Runtime supplying language configuration, translations and logger.
        :return: No return value.
        """
        self.runtime = runtime
        self.logger = runtime.logger
        self.preferences = {}
        self._PreferenceManager__store_file_path = PREFERENCE_FILE_PATH

    @classmethod
    def _PreferenceManager__get_name(cls: type[Self], obj: User | QQCommandSource | ConsoleSource, *, strict_type_check: bool = False) -> str | None:
        from botqraft.message.user import User
        from botqraft.command.command_source import QQCommandSource, ConsoleSource
        if isinstance(obj, ConsoleSource):
            return CONSOLE_ALIAS
        if isinstance(obj, QQCommandSource):
            obj = obj.user
        if isinstance(obj, User):
            try:
                return obj.require_identity()
            except ValueError:
                if strict_type_check:
                    raise InvalidPreferenceSource('Preference subject has no real QQ user identity') from None
                return None
        raise InvalidPreferenceSource('Preference subject must be User or a BotQraft command source')

    def get_default_preference(self: Self) -> PreferenceItem:
        """Create default preferences using the runtime language.
        
        :return: New default preference item.
        """
        return PreferenceItem(language=self.runtime.get_language())

    def get_console_preference(self: Self) -> PreferenceItem:
        """Return a copy of console preferences or a new default preference.
        
        :return: Independent console preference snapshot.
        """
        pref = self.preferences.get(CONSOLE_ALIAS)
        return self.get_default_preference() if pref is None else pref.copy()

    def set_console_preference(self: Self, pref: PreferenceItem) -> None:
        """Validate and persist a copy of console preferences.
        
        :param pref: Native PreferenceItem with an optional registered language.
        :return: No return value.
        """
        self._validate_preference(pref)
        self.preferences[CONSOLE_ALIAS] = pref.copy()
        self._PreferenceManager__save_preferences()

    def set_preference(self: Self, obj: User | QQCommandSource | ConsoleSource, pref: PreferenceItem) -> None:
        """Validate a QQ subject and persist its native preference item.
        
        :param obj: QQ user or standalone command source whose preferences are used.
        :param pref: Native PreferenceItem with an optional registered language.
        :return: No return value.
        """
        self._PreferenceManager__get_name(obj, strict_type_check=True)
        self._validate_preference(pref)
        super().set_preference(obj, pref)

    def _validate_preference(self: Self, pref: PreferenceItem) -> None:
        if not isinstance(pref, PreferenceItem):
            raise TypeError('Preference must be a native PreferenceItem')
        language = getattr(pref, 'language', None)
        # MCDR 2.16 stores language as a required str; a saved null makes the strict loader discard every preference.
        if not isinstance(language, str) or language not in self.runtime.translation_manager.available_languages:
            raise ValueError('Unknown preference language')

    def get_preferred_language(self: Self, obj: User | QQCommandSource | ConsoleSource) -> str:
        """Return the subject language preference with runtime-language fallback.
        
        :param obj: QQ user or standalone command source whose preferences are used.
        :return: Preferred registered language or the configured runtime language.
        """
        return self.get_preference(obj).language or self.runtime.get_language()

    def load_preferences(self: Self) -> None:
        """Load preferences using native malformed-file recovery behavior.
        
        :return: No return value.
        """
        self._drop_unset_languages()
        # The upstream path intentionally empties and rewrites malformed JSON.
        self.logger.warning('Preference loading follows native recovery: malformed files are emptied and saved; back up preferences to avoid data loss')
        super().load_preferences()

    def _drop_unset_languages(self: Self) -> None:
        # MCDR 2.14 accepted language: null (meaning "use the runtime language"). Removing such
        # entries keeps that meaning and stops the 2.16 strict loader from wiping the whole file.
        path: Path = self._PreferenceManager__store_file_path
        try:
            data = json.loads(path.read_text(encoding='utf8'))
        except (OSError, ValueError):
            return
        if not isinstance(data, dict):
            return
        kept = {name: item for name, item in data.items() if not (isinstance(item, dict) and 'language' in item and item['language'] is None)}
        if len(kept) == len(data):
            return
        with file_utils.safe_write(path, encoding='utf8') as file:
            json.dump(kept, file, indent=4, ensure_ascii=False)
        self.logger.info('Removed %d preference entries without a language; they follow the runtime language', len(data) - len(kept))
