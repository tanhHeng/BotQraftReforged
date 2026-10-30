"""Fetch the official QQ bot documentation as local Markdown, for offline reading and AI agents."""
import importlib.util
import logging
import sys
from pathlib import Path

_DOCS_EXTRA = (('bs4', 'beautifulsoup4'), ('markdownify', 'markdownify'))


def _interactive() -> bool:
    if not sys.stdin.isatty():
        return False
    if sys.platform != 'win32':
        return True
    # Windows reports the NUL device (`< /dev/null`, `< NUL`) as a TTY; only a real console has a console mode.
    import ctypes
    import msvcrt
    mode = ctypes.c_uint32()
    return bool(ctypes.windll.kernel32.GetConsoleMode(msvcrt.get_osfhandle(sys.stdin.fileno()), ctypes.byref(mode)))


def _offer_ignore(output: Path) -> None:
    from botqraft.official_docs.history import add_ignore_entry, ignore_entry, unignored_parent_repository

    root = unignored_parent_repository(output)
    if root is None or not (root / '.gitignore').is_file():
        return
    entry = ignore_entry(root, output)
    gitignore = root / '.gitignore'
    shown = '.gitignore' if gitignore.resolve() == (Path.cwd() / '.gitignore').resolve() else str(gitignore)
    if not _interactive():
        print('Hint: {} is not ignored by Git; consider adding {} to {}'.format(output, entry, shown), file=sys.stderr)
        return
    try:
        answer = input('Add {} to {}? (Y/n) '.format(entry, shown)).strip().lower()
    except EOFError:
        answer = 'n'
    if answer in ('', 'y', 'yes'):
        add_ignore_entry(root, output)
        print('Added {} to {}'.format(entry, shown))


def fetch_official_docs(output: str, *, base_url: str, timeout: float, delay: float, quiet: bool = False, git: bool = False) -> None:
    """Export the official documentation and fail when the export is incomplete.

    After fetching, when the output directory sits in a Git work tree whose root ``.gitignore`` exists but does
    not ignore it, an interactive terminal is asked whether to add it; other terminals only get a hint.

    :param output: Output directory.
    :param base_url: Documentation directory to crawl.
    :param timeout: Per-request timeout in seconds.
    :param delay: Minimum seconds between requests.
    :param quiet: Whether to suppress per-page progress; errors are still printed.
    :param git: Whether to commit page and image changes to a Git repository in the output directory.
    :raises ModuleNotFoundError: The optional ``docs`` dependencies are not installed.
    :raises RuntimeError: Git cannot be used for the output directory, a Git command failed, the directory is
        still not ignored after the prompt (``git`` commits are then skipped), or some documents or images
        failed; with ``git``, an incomplete export is still committed first.
    """
    missing = [package for module, package in _DOCS_EXTRA if importlib.util.find_spec(module) is None]
    if missing:
        raise ModuleNotFoundError('Missing optional dependencies: {}. Install the docs extra, for example: python -m pip install ".[docs]" in the BotQraft source directory'.format(', '.join(missing)))
    from botqraft.official_docs.exporter import export_docs
    from botqraft.official_docs.history import check_history_target, commit_history, unignored_parent_repository

    if git:
        check_history_target(Path(output), can_ignore_later=_interactive())

    logger = logging.getLogger('botqraft.official_docs')
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING if quiet else logging.INFO)
    logger.propagate = False
    try:
        result = export_docs(base_url, output, timeout=timeout, delay=delay)
    finally:
        logger.removeHandler(handler)
    print('Discovered {} documents, exported {}, removed {} files, {} errors, {} redirected links skipped; output: {}'.format(
        result.discovered, result.exported, len(result.removed), len(result.errors), len(result.redirected), result.output_dir.resolve()))
    _offer_ignore(result.output_dir)
    if git:
        if unignored_parent_repository(result.output_dir) is not None:
            raise RuntimeError('{} is still not ignored by the enclosing Git work tree; skipped the --git commit'.format(output))
        commit = commit_history(result.output_dir, result, base_url)
        print('Committed {}'.format(commit) if commit else 'No page or image changed; nothing committed')
    if not result.complete:
        raise RuntimeError('Export incomplete; see {} for the errors'.format(result.output_dir / 'manifest.json'))
