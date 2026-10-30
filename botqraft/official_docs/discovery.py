"""Discover page links plus routes hidden inside collapsed VuePress navigation."""
from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlsplit

if TYPE_CHECKING:
    from bs4 import BeautifulSoup

    from botqraft.official_docs.scope import DocumentScope

_JS_STRING = r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\''


def page_links(soup: BeautifulSoup, page_url: str, scope: DocumentScope) -> set[str]:
    return {
        url
        for anchor in soup.select('a[href]')
        if (url := scope.canonical(str(anchor['href']), page_url)) is not None
    }


def app_scripts(soup: BeautifulSoup, page_url: str) -> list[str]:
    return sorted({
        urljoin(page_url, str(script['src']))
        for script in soup.select('script[src]')
        if re.fullmatch(r'app(?:\.[\w-]+)*\.js', urlsplit(str(script['src'])).path.rsplit('/', 1)[-1])
    })


def _js_string(value: str) -> str:
    if value.startswith('"'):
        return json.loads(value)
    return json.loads('"' + value[1:-1].replace('\\\'', "'").replace('"', '\\"') + '"')


def bundle_routes(script: str, scope: DocumentScope) -> set[str]:
    """Read in-scope document routes from a VuePress app bundle.

    The initial HTML only links pages of expanded sidebar groups, so the route table is the complete source.

    :param script: App bundle source.
    :param scope: Crawl boundary.
    :return: Canonical in-scope document URLs.
    :raises ValueError: The bundle has no deployment base or no in-scope route.
    """
    base_match = re.search(r'\bbase\s*:\s*(' + _JS_STRING + r')', script)
    if base_match is None:
        raise ValueError('VuePress app bundle has no base; routes cannot be resolved reliably')
    site_base = _js_string(base_match.group(1))
    origin = scope.base_url.split('/', 3)[:3]
    site_url = '/'.join(origin) + '/' + site_base.strip('/') + '/'
    routes = set()
    for match in re.finditer(r'\b(?:path|regularPath)\s*:\s*(' + _JS_STRING + r')', script):
        route = _js_string(match.group(1))
        if not route.startswith('/'):
            continue
        # Route paths omit the deployment base (for example /wiki/).
        url = scope.canonical(urljoin(site_url, route.lstrip('/')))
        if url is not None:
            routes.add(url)
    if not routes:
        raise ValueError('VuePress app bundle has no document route in scope')
    return routes
