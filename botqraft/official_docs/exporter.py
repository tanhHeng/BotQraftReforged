"""Crawl the official QQ bot documentation and write a Markdown snapshot with a manifest."""
from __future__ import annotations

import json
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from bs4 import BeautifulSoup
from typing_extensions import Self

from botqraft.official_docs.converter import Page, extract_page, render_page
from botqraft.official_docs.discovery import app_scripts, bundle_routes, page_links
from botqraft.official_docs.fetch import AssetStore, FetchError, HttpClient
from botqraft.official_docs.scope import DEFAULT_BASE_URL, DocumentScope

logger = logging.getLogger(__name__)


@dataclass
class ExportResult:
    discovered: int
    exported: int
    output_dir: Path
    errors: list[dict[str, str]] = field(default_factory=list)

    @property
    def complete(self: Self) -> bool:
        """Whether every discovered document was exported without any error."""
        return self.exported == self.discovered and not self.errors


def export_docs(base_url: str = DEFAULT_BASE_URL, output_dir: str | Path = 'qq_docs', *, timeout: float = 30, delay: float = 0.1) -> ExportResult:
    """Export every in-scope VuePress route and recursively linked document as Markdown.

    Files of the same name are overwritten; other files in the output directory are kept.
    Failures never stop the crawl and are never retried: they are recorded in the result and in
    ``manifest.json``, and the pages that succeeded are still written.

    :param base_url: Documentation directory to crawl.
    :param output_dir: Output directory, created when missing.
    :param timeout: Per-request timeout in seconds.
    :param delay: Minimum seconds between requests.
    :return: Discovery and export counts plus error records.
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
    known = {scope.base_url}
    queue = deque([scope.base_url])
    processed: set[str] = set()
    fetched_bundles: set[str] = set()
    route_count = 0
    while queue:
        url = queue.popleft()
        processed.add(url)
        logger.info('Fetching [%d/%d] %s', len(processed), len(known), url)
        try:
            markup, final_url = client.text(url)
            # Missing pages redirect to the home page; never store that as the requested document.
            if scope.canonical(final_url) != url:
                raise ValueError('Document redirected to another page: {}'.format(final_url))
            page = extract_page(markup, url)
            soup = BeautifulSoup(markup, 'html.parser')
            found = page_links(soup, url, scope)
            if url == scope.base_url:
                bundles = app_scripts(soup, url)
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
                        errors.append({'url': bundle_url, 'error': 'Route discovery failed: {}'.format(error)})
            pages[url] = page
            for discovered in sorted(found - known):
                known.add(discovered)
                queue.append(discovered)
        except (FetchError, ValueError) as error:
            errors.append({'url': url, 'error': str(error)})
            logger.error('Failed to fetch %s: %s', url, error)

    assets = AssetStore(destination, client)
    available = set(pages)
    records: list[dict[str, str]] = []
    for url, page in sorted(pages.items()):
        relative = scope.output_path(url)
        path = destination.joinpath(*relative.parts)
        markdown = render_page(page, scope, available, assets, errors)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding='utf-8', newline='\n')
        records.append({'url': url, 'title': page.title, 'path': relative.as_posix()})
        logger.info('Saved %s', relative)

    result = ExportResult(len(known), len(records), destination, errors)
    manifest = {
        'base_url': scope.base_url,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'route_count': route_count,
        'discovered': result.discovered,
        'exported': result.exported,
        'complete': result.complete,
        'pages': records,
        'errors': errors,
    }
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    catalog = ['# QQ bot official documentation', '', 'Source: <{}>'.format(scope.base_url), '',
               'Discovered {} documents, exported {}, {} errors.'.format(result.discovered, result.exported, len(errors)), '']
    for record in records:
        title = record['title'].replace('\\', '\\\\').replace('[', r'\[').replace(']', r'\]')
        catalog.append('- [{}]({})'.format(title, quote(record['path'], safe='/-._~')))
    catalog.extend(['', 'See [manifest.json](manifest.json) for the page list and errors.', ''])
    (destination / 'README.md').write_text('\n'.join(catalog), encoding='utf-8', newline='\n')
    return result
