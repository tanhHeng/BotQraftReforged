"""Reuse MCDR 2.16.2's pack implementation with a private filename binding.

The upstream function has no metadata-path parameter. A separate globals mapping
changes that one dependency for this callable only: the native module, constants,
and every other caller remain untouched. Ignore matching (relative to the input
directory), Metadata, resources, requirements, archive naming and shebang handling
all remain native.
"""
from typing import Callable
from pathlib import Path
from types import FunctionType

import pathspec
from mcdreforged.cli import cmd_pack as native_pack
from mcdreforged.cli.cmd_pack import PackArgs, read_ignore_file
from mcdreforged.plugin.meta.metadata import Metadata, RequirementsFileSpec
from mcdreforged.plugin.meta.schema import PluginMetadataJsonModel

from botqraft.constants import plugin_constant


def _bind_native_packer() -> Callable[..., None]:
    original = native_pack.make_packed_plugin
    bindings = dict(original.__globals__, plugin_constant=plugin_constant)
    bound = FunctionType(original.__code__, bindings, original.__name__, original.__defaults__, original.__closure__)
    bound.__kwdefaults__ = original.__kwdefaults__.copy() if original.__kwdefaults__ else None
    return bound


def _ignore_spec(args: PackArgs, input_dir: Path) -> pathspec.PathSpec:
    # Same precedence as the native packer: explicit patterns win over the ignore file.
    if len(args.ignore_patterns) > 0:
        return pathspec.GitIgnoreSpec.from_lines(args.ignore_patterns)
    if args.ignore_file:
        spec = read_ignore_file(input_dir / args.ignore_file, lambda _: None)
        if spec is not None:
            return spec
    return pathspec.GitIgnoreSpec.from_lines([])


def make_packed_plugin(args: PackArgs, *, quiet: bool = False) -> None:
    """Package a validated BotQraft plugin using native MCDR archive conventions.
    
    :param args: Native packaging options for input, output, archive naming and ignores.
    :param quiet: Whether to suppress native packaging progress output.
    :return: No return value.
    """
    # Native packing only prints and returns on bad input; raise so the CLI exits non-zero.
    input_dir = Path(args.input)
    if not input_dir.is_dir():
        raise NotADirectoryError(args.input)
    metadata_path = input_dir / plugin_constant.PLUGIN_META_FILE
    if not metadata_path.is_file():
        raise FileNotFoundError(str(metadata_path))
    metadata = Metadata.create(PluginMetadataJsonModel.model_validate_json(metadata_path.read_bytes(), strict=True))
    requirements = metadata.requirements_file
    if requirements.mode is RequirementsFileSpec.Mode.REQUIRED:
        if not (input_dir / requirements.path).is_file():
            raise FileNotFoundError(str(input_dir / requirements.path))
        if _ignore_spec(args, input_dir).match_file(requirements.path):
            raise ValueError('Required requirements file {!r} is excluded by pack ignore rules'.format(requirements.path))
    # Native mkdir is non-recursive; a deployment output may have missing parents.
    Path(args.output).mkdir(parents=True, exist_ok=True)
    _bind_native_packer()(args, quiet=quiet)
