"""Fetch the official QQ bot documentation as local Markdown, for offline reading and AI agents."""
import importlib.util
import logging
import sys

_DOCS_EXTRA = (('bs4', 'beautifulsoup4'), ('markdownify', 'markdownify'))


def fetch_official_docs(output: str, *, base_url: str, timeout: float, delay: float, quiet: bool = False) -> None:
    """Export the official documentation and fail when the export is incomplete.

    :param output: Output directory.
    :param base_url: Documentation directory to crawl.
    :param timeout: Per-request timeout in seconds.
    :param delay: Minimum seconds between requests.
    :param quiet: Whether to suppress per-page progress; errors are still printed.
    :raises ModuleNotFoundError: The optional ``docs`` dependencies are not installed.
    :raises RuntimeError: Some documents or images failed; the pages that succeeded are kept.
    """
    missing = [package for module, package in _DOCS_EXTRA if importlib.util.find_spec(module) is None]
    if missing:
        raise ModuleNotFoundError('Missing optional dependencies: {}. Install the docs extra, for example: python -m pip install ".[docs]" in the BotQraft source directory'.format(', '.join(missing)))
    from botqraft.official_docs.exporter import export_docs

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
    print('Discovered {} documents, exported {}, {} errors; output: {}'.format(
        result.discovered, result.exported, len(result.errors), result.output_dir.resolve()))
    if not result.complete:
        raise RuntimeError('Export incomplete; see {} for the errors'.format(result.output_dir / 'manifest.json'))
