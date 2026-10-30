"""Crawl the official QQ bot documentation and write a Markdown snapshot with a manifest."""
from __future__ import annotations

import json
import logging
import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

from bs4 import BeautifulSoup
from typing_extensions import Self

from botqraft.official_docs.converter import Page, extract_page, render_page
from botqraft.official_docs.discovery import app_scripts, bundle_routes, page_links
from botqraft.official_docs.fetch import AssetStore, FetchError, HttpClient
from botqraft.official_docs.scope import DEFAULT_BASE_URL, DocumentScope

logger = logging.getLogger(__name__)
_SOURCE_LINE = re.compile(r'> Source: <(.+)>')
_ASSET_NAME = re.compile(r'[0-9a-f]{64}\.[a-z]+')


@dataclass
class ExportResult:
    discovered: int
    exported: int
    output_dir: Path
    errors: list[dict[str, str]] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    redirected: dict[str, str] = field(default_factory=dict)

    @property
    def complete(self: Self) -> bool:
        """Whether every discovered document was exported without any error; redirected links do not count."""
        return self.exported == self.discovered and not self.errors


def _exported_markdown(destination: Path) -> list[Path]:
    return sorted(path for path in destination.rglob('*.md') if '.git' not in path.relative_to(destination).parts)


def _source_url(path: Path) -> str | None:
    with path.open(encoding='utf-8', errors='replace') as stream:
        match = _SOURCE_LINE.fullmatch(stream.readline().rstrip('\r\n'))
    return match.group(1) if match else None


def _previous_assets(destination: Path) -> dict[str, str]:
    try:
        assets = json.loads((destination / 'manifest.json').read_text(encoding='utf-8')).get('assets', {})
    except (OSError, ValueError, AttributeError):
        return {}
    return {url: path for url, path in assets.items() if isinstance(url, str) and isinstance(path, str)} if isinstance(assets, dict) else {}


def _prune_withdrawn(destination: Path, scope: DocumentScope, known: set[str]) -> list[str]:
    """Delete exported pages the site no longer lists, then images no page references.

    Only files this exporter wrote are touched: pages are recognized by their source line, images by their hash name.
    Pages that were discovered but failed this time are kept, so a network error never looks like a withdrawal.
    """
    removed: list[Path] = []
    for path in _exported_markdown(destination):
        url = _source_url(path)
        if url is None or scope.canonical(url) != url or url in known:
            continue
        path.unlink()
        removed.append(path)
    assets = destination / '_assets'
    if assets.is_dir():
        referenced = set()
        for path in _exported_markdown(destination):
            referenced.update(re.findall(r'_assets/([0-9a-f]{64}\.[a-z]+)', path.read_text(encoding='utf-8', errors='replace')))
        for asset in sorted(assets.iterdir()):
            if asset.is_file() and _ASSET_NAME.fullmatch(asset.name) and asset.name not in referenced:
                asset.unlink()
                removed.append(asset)
    for directory in sorted({parent for path in removed for parent in path.parents if destination in parent.parents}, key=lambda path: len(path.parts), reverse=True):
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    return [path.relative_to(destination).as_posix() for path in removed]


def export_docs(base_url: str = DEFAULT_BASE_URL, output_dir: str | Path = 'qq_docs', *, timeout: float = 30, delay: float = 0.1) -> ExportResult:
    """Export every in-scope VuePress route and recursively linked document as Markdown.

    Files of the same name are overwritten. When route discovery succeeded, exported pages whose URL was not
    discovered again are deleted together with unreferenced images; other files in the output directory are kept.
    Output depends only on the site content, so re-running against an unchanged site rewrites identical files.
    Failures never stop the crawl and are never retried: they are recorded in the result and in
    ``manifest.json``, and the pages that succeeded are still written. Links that redirect to another page
    (usually dead links sent to the home page) are not documents: they are reported, not counted as errors.

    :param base_url: Documentation directory to crawl.
    :param output_dir: Output directory, created when missing.
    :param timeout: Per-request timeout in seconds.
    :param delay: Minimum seconds between requests.
    :return: Discovery and export counts, error records, removed paths and redirected links.
    :raises ValueError: Invalid base URL, non-positive timeout or negative delay.
    :raises OSError: An output file cannot be written.
    """
    if timeout <= 0 or delay < 0:
        raise ValueError('timeout must be positive and delay must not be negative')
    scope = DocumentScope(base_url)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    client = HttpClient(timeout, delay)
    errors: list[dict[str, str]] = []
    pages: dict[str, Page] = {}
    redirected: dict[str, str] = {}
    known = {scope.base_url}
    queue = deque([scope.base_url])
    processed: set[str] = set()
    fetched_bundles: set[str] = set()
    route_count = 0
    routes_complete = False
    while queue:
        url = queue.popleft()
        processed.add(url)
        logger.info('Fetching [%d/%d] %s', len(processed), len(known), url)
        try:
            markup, final_url = client.text(url)
            # Missing pages redirect to the home page; never store that as the requested document.
            if scope.canonical(final_url) != url:
                # Without the root page there are no routes to crawl, so this is a failure, not a dead link.
                if url == scope.base_url:
                    raise ValueError('Documentation root redirected to another page: {}'.format(final_url))
                redirected[url] = final_url
                logger.warning('Skipped %s: redirected to %s', url, final_url)
                continue
            page = extract_page(markup, url)
            soup = BeautifulSoup(markup, 'html.parser')
            found = page_links(soup, url, scope)
            if url == scope.base_url:
                bundles = app_scripts(soup, url)
                routes_complete = bool(bundles)
                if not bundles:
                    errors.append({'url': url, 'error': 'No VuePress app bundle found; collapsed navigation may be missing'})
                for bundle_url in bundles:
                    if bundle_url in fetched_bundles:
                        continue
                    fetched_bundles.add(bundle_url)
                    try:
                        script, _ = client.text(bundle_url)
                        routes = bundle_routes(script, scope)
                        route_count += len(routes)
                        found.update(routes)
                        logger.info('Route table lists %d documents', len(routes))
                    except (FetchError, ValueError) as error:
                        routes_complete = False
                        errors.append({'url': bundle_url, 'error': 'Route discovery failed: {}'.format(error)})
            pages[url] = page
            for discovered in sorted(found - known):
                known.add(discovered)
                queue.append(discovered)
        except (FetchError, ValueError) as error:
            errors.append({'url': url, 'error': str(error)})
            logger.error('Failed to fetch %s: %s', url, error)

    documents = known - set(redirected)
    # Transient failures must not rewrite unchanged content: keep links to pages that failed this time but
    # were exported before, and keep images that failed to download but were saved before.
    assets = AssetStore(destination, client, _previous_assets(destination))
    available = set(pages)
    for url in documents - available:
        previous = destination.joinpath(*scope.output_path(url).parts)
        if previous.is_file() and _source_url(previous) == url:
            available.add(url)
    records: list[dict[str, str]] = []
    for url, page in sorted(pages.items()):
        relative = scope.output_path(url)
        path = destination.joinpath(*relative.parts)
        markdown = render_page(page, scope, available, assets, errors)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding='utf-8', newline='\n')
        records.append({'url': url, 'title': page.title, 'path': relative.as_posix()})
        logger.info('Saved %s', relative)

    removed = _prune_withdrawn(destination, scope, documents) if routes_complete else []
    for path in removed:
        logger.info('Removed %s', path)
    result = ExportResult(len(documents), len(records), destination, errors, removed, redirected)
    manifest = {
        'base_url': scope.base_url,
        'route_count': route_count,
        'discovered': result.discovered,
        'exported': result.exported,
        'complete': result.complete,
        'pages': records,
        'assets': {url: path.as_posix() for url, path in sorted(assets.cache.items()) if not url.startswith('data:')},
        'redirects': dict(sorted(redirected.items())),
        'errors': errors,
    }
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    catalog = [
        '# QQ bot official documentation', '',
        '> Unofficial Markdown copy of the QQ bot documentation at <{}>, made by BotQraft for offline reference.'.format(scope.base_url),
        '> Copyright © Tencent. All rights reserved. All text and images belong to their copyright owners;',
        '> the original site is authoritative. Do not redistribute this copy or commit it to a public repository.', '',
        'Discovered {} documents, exported {}, {} errors, {} redirected links.'.format(
            result.discovered, result.exported, len(errors), len(redirected)), '',
    ]
    for record in records:
        title = record['title'].replace('\\', '\\\\').replace('[', r'\[').replace(']', r'\]')
        catalog.append('- [{}]({})'.format(title, quote(record['path'], safe='/-._~')))
    catalog.extend(['', 'See [manifest.json](manifest.json) for the page list, redirected links and errors.', ''])
    (destination / 'README.md').write_text('\n'.join(catalog), encoding='utf-8', newline='\n')
    return result
