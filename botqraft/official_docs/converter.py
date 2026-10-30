"""Extract VuePress article content and render Markdown that keeps code, tables, anchors and images."""
from __future__ import annotations

import html
import posixpath
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING
from urllib.parse import quote, urljoin, urlsplit

from bs4 import BeautifulSoup, Tag
from markdownify import MarkdownConverter

if TYPE_CHECKING:
    from botqraft.official_docs.fetch import AssetStore
    from botqraft.official_docs.scope import DocumentScope


@dataclass
class Page:
    url: str
    title: str
    content: Tag
    updated: str | None


def extract_page(markup: str, url: str) -> Page:
    """Extract the article body, title and update time from a VuePress page.

    :param markup: Page HTML.
    :param url: Canonical page URL.
    :return: Parsed page with navigation and decorations removed.
    :raises ValueError: The page has no article body, no title or an empty body (usually an error page).
    """
    soup = BeautifulSoup(markup, 'html.parser')
    content = soup.select_one('main.page .theme-default-content, main.page .content__default')
    if content is None:
        raise ValueError('Page has no VuePress article body; it may be an error page: {}'.format(url))
    heading = content.find('h1')
    if heading:
        title = heading.get_text(' ', strip=True).lstrip('# ')
    elif soup.title:
        title = soup.title.get_text(strip=True).split('|', 1)[0].strip()
    else:
        raise ValueError('Page has no title: {}'.format(url))
    if not content.get_text(strip=True) and not content.find('img'):
        raise ValueError('Page body is empty: {}'.format(url))
    updated = soup.select_one('.last-updated .time')
    for unwanted in content.select('.header-anchor, .icon.outbound, .sr-only, .line-numbers-wrapper, script, style'):
        unwanted.decompose()
    return Page(url, title, content, updated.get_text(strip=True) if updated else None)


def _relative_link(target: PurePosixPath, source: PurePosixPath) -> str:
    return quote(posixpath.relpath(str(target), str(source.parent)), safe='/-._~')


class _ArticleConverter(MarkdownConverter):
    def convert_hN(self, n, el, text, parent_tags):
        heading = super().convert_hN(n, el, text, parent_tags)
        # Keep the site's heading IDs so fragments copied from the site still resolve.
        if el.get('id'):
            return '\n\n<a id="' + html.escape(el['id'], quote=True) + '"></a>' + heading
        return heading

    def convert_a(self, el, text, parent_tags):
        if not el.get('href') and (el.get('id') or el.get('name')):
            return '<a id="' + html.escape(el.get('id') or el['name'], quote=True) + '"></a>' + text
        return super().convert_a(el, text, parent_tags)

    def convert_pre(self, el, text, parent_tags):
        code = el.get_text().strip('\n')
        language = ''
        for node in (el.find('code'), el, el.parent):
            if node:
                for css_class in node.get('class', []):
                    if css_class.startswith('language-'):
                        language = css_class[len('language-'):]
                        break
            if language:
                break
        fence = '`' * max(3, max((len(run) + 1 for run in re.findall(r'`+', code)), default=0))
        return '\n\n{}{}\n{}\n{}\n\n'.format(fence, language, code, fence)

    def convert_br(self, el, text, parent_tags):
        if {'td', 'th'} & parent_tags:
            return '<br>' + text
        return super().convert_br(el, text, parent_tags)

    def convert_td(self, el, text, parent_tags):
        return super().convert_td(el, text.replace('|', r'\|'), parent_tags)

    def convert_th(self, el, text, parent_tags):
        return self.convert_td(el, text, parent_tags)

    def convert_table(self, el, text, parent_tags):
        # Pipe tables cannot express merged cells; keep those tables as HTML.
        if el.select('[rowspan], [colspan]'):
            return '\n\n' + str(el) + '\n\n'
        return super().convert_table(el, text, parent_tags)

    def convert_details(self, el, text, parent_tags):
        return '\n\n<details' + (' open' if el.has_attr('open') else '') + '>\n\n' + text.strip() + '\n\n</details>\n\n'

    def convert_summary(self, el, text, parent_tags):
        return '<summary>' + html.escape(el.get_text()) + '</summary>\n\n'


def render_page(page: Page, scope: DocumentScope, available_urls: set[str], assets: AssetStore, errors: list[dict[str, str]]) -> str:
    """Render a page as Markdown with local links and images.

    Links to exported documents become relative ``.md`` links; other links keep their absolute URL.
    Image failures keep the remote URL and are appended to ``errors``.

    :param page: Extracted page.
    :param scope: Crawl boundary used for output paths.
    :param available_urls: Canonical URLs of every successfully fetched document.
    :param assets: Image store for the output directory.
    :param errors: Error records to append image failures to.
    :return: Markdown starting with a source line.
    """
    output_path = scope.output_path(page.url)
    content = BeautifulSoup(str(page.content), 'html.parser')
    for anchor in content.select('a[href]'):
        href = str(anchor['href'])
        if href.startswith('#'):
            continue
        absolute = urljoin(page.url, href)
        target = scope.canonical(absolute)
        if target in available_urls:
            fragment = urlsplit(absolute).fragment
            anchor['href'] = _relative_link(scope.output_path(target), output_path) + ('#' + quote(fragment, safe='%-._~') if fragment else '')
        else:
            anchor['href'] = absolute
    for image in content.select('img'):
        source = image.get('src') or image.get('data-src')
        if not source:
            errors.append({'page': page.url, 'error': 'Image has no src or data-src'})
            continue
        absolute = urljoin(page.url, str(source))
        try:
            image['src'] = _relative_link(assets.save(absolute), output_path)
        except (ValueError, OSError) as error:
            errors.append({'page': page.url, 'url': absolute[:300], 'error': str(error)})
            image['src'] = absolute
        # Retained HTML tables would otherwise keep pointing at remote images.
        image.attrs.pop('srcset', None)
    converter = _ArticleConverter(
        heading_style='ATX', bullets='-', wrap=False,
        keep_inline_images_in=['td', 'th', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
    )
    body = converter.convert_soup(content).strip()
    metadata = '> Source: <{}>\n'.format(page.url)
    if page.updated:
        metadata += '> Last updated: {}\n'.format(page.updated)
    if not page.content.find('h1'):
        body = '# ' + page.title + '\n\n' + body
    return metadata + '\n' + body + '\n'
