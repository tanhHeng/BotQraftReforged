"""Fetch the official QQ bot documentation as local Markdown, for offline reading and AI agents."""
import importlib.util
import logging
import sys
from pathlib import Path

_DOCS_EXTRA = (('bs4', 'beautifulsoup4'), ('markdownify', 'markdownify'))


def fetch_official_docs(output: str, *, base_url: str, timeout: float, delay: float, quiet: bool = False, git: bool = False) -> None:
    """Export the official documentation and fail when the export is incomplete.

    :param output: Output directory.
    :param base_url: Documentation directory to crawl.
    :param timeout: Per-request timeout in seconds.
    :param delay: Minimum seconds between requests.
    :param quiet: Whether to suppress per-page progress; errors are still printed.
    :param git: Whether to commit page and image changes to a Git repository in the output directory.
    :raises ModuleNotFoundError: The optional ``docs`` dependencies are not installed.
    :raises RuntimeError: Git cannot be used for the output directory (checked before fetching), a Git command
        failed, or some documents or images failed; with ``git``, an incomplete export is still committed first.
    """
    missing = [package for module, package in _DOCS_EXTRA if importlib.util.find_spec(module) is None]
    if missing:
        raise ModuleNotFoundError('Missing optional dependencies: {}. Install the docs extra, for example: python -m pip install ".[docs]" in the BotQraft source directory'.format(', '.join(missing)))
    from botqraft.official_docs.exporter import export_docs
    from botqraft.official_docs.history import check_history_target, commit_history

    if git:
        check_history_target(Path(output))

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
    print('Discovered {} documents, exported {}, removed {} files, {} errors; output: {}'.format(
        result.discovered, result.exported, len(result.removed), len(result.errors), result.output_dir.resolve()))
    if git:
        commit = commit_history(result.output_dir, result, base_url)
        print('Committed {}'.format(commit) if commit else 'No page or image changed; nothing committed')
    if not result.complete:
        raise RuntimeError('Export incomplete; see {} for the errors'.format(result.output_dir / 'manifest.json'))
