from __future__ import annotations
from typing import TYPE_CHECKING
from typing_extensions import Self

if TYPE_CHECKING:
    from botqraft.plugin.plugin_manager import PluginManager
from typing import Any
from mcdreforged.plugin.meta.schema import PluginMetadataJsonModel
from mcdreforged.plugin.type.builtin_plugin import BuiltinPlugin as NativeBuiltinPlugin
from mcdreforged.plugin.builtin.python_plugin import PythonPlugin as NativePythonPlugin, METADATA
from botqraft.constants.core_constant import VERSION
from botqraft.plugin.meta.metadata import Metadata
from .plugin import Plugin


class BuiltinPlugin(Plugin, NativeBuiltinPlugin):
    def __init__(self: Self, plugin_manager: PluginManager, metadata: dict[str, Any] | PluginMetadataJsonModel) -> None:
        """Initialize a built-in plugin from native metadata fields.
        
        :param plugin_manager: Manager owning the record.
        :param metadata: Metadata fields with open JSON-compatible values, or a native metadata model.
        :return: No value is returned.
        """
        Plugin.__init__(self, plugin_manager)
        self._set_metadata(Metadata.create(metadata, plugin=self))


class CorePlugin(BuiltinPlugin):
    def __init__(self: Self, plugin_manager: PluginManager) -> None:
        """Initialize the BotQraft administration plugin.
        
        :param plugin_manager: Manager owning the record.
        :return: No value is returned.
        """
        super().__init__(plugin_manager, {'id': 'botqraft', 'version': VERSION, 'name': 'BotQraft', 'dependencies': {'python': '*'}})

    def load(self: Self) -> None:
        """Register the BotQraft administration commands.
        
        :return: No value is returned.
        """
        from botqraft.plugin.builtin.botqraft import register
        self.runtime.builtin_command_root = register(self.server_interface)


class PythonPlugin(BuiltinPlugin, NativePythonPlugin):
    def __init__(self: Self, plugin_manager: PluginManager) -> None:
        """Initialize the native Python runtime plugin record.
        
        :param plugin_manager: Manager owning the record.
        :return: No value is returned.
        """
        BuiltinPlugin.__init__(self, plugin_manager, METADATA)

    def load(self: Self) -> None:
        """Log the available Python runtime plugin.
        
        :return: No value is returned.
        """
        self.runtime.logger.info('Python runtime: %s', self.get_meta_name())
