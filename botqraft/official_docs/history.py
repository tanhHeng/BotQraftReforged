"""Git integration for an export directory: ignore rules of the enclosing repository and the export's own history."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from botqraft.official_docs.exporter import ExportResult

# Machine-made commits use a fixed identity, so they never depend on (or impersonate) the user's Git config.
_IDENTITY = {
    'GIT_AUTHOR_NAME': 'BotQraft docs fetcher', 'GIT_AUTHOR_EMAIL': 'docs-fetcher@botqraft.invalid',
    'GIT_COMMITTER_NAME': 'BotQraft docs fetcher', 'GIT_COMMITTER_EMAIL': 'docs-fetcher@botqraft.invalid',
}
_SUMMARY_FILES = {'README.md', 'manifest.json'}
_LISTED_CHANGES = 100


def _git(*args: str, cwd: Path, stdin: str | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        ['git', '-c', 'core.quotepath=false', *args], cwd=cwd, input=stdin, capture_output=True,
        text=True, encoding='utf-8', env={**os.environ, **_IDENTITY},
    )
    if check and process.returncode != 0:
        raise RuntimeError('git {} failed: {}'.format(args[0], (process.stderr or process.stdout).strip()))
    return process


def unignored_parent_repository(output: Path) -> Path | None:
    """Find the enclosing Git work tree that would track the output directory.

    :param output: Export output directory; it may not exist yet, and may already be its own repository.
    :return: Top level of the enclosing work tree when it does not ignore the directory; None when Git is
        missing, the directory is outside any work tree, or the work tree already ignores it.
    """
    if shutil.which('git') is None:
        return None
    target = output.resolve()
    # Start above the target: once --git has run, the target is a repository of its own.
    anchor = target.parent
    while not anchor.exists():
        anchor = anchor.parent
    toplevel = _git('rev-parse', '--show-toplevel', cwd=anchor, check=False)
    if toplevel.returncode != 0:
        return None
    if _git('check-ignore', '-q', target.as_posix() + '/', cwd=anchor, check=False).returncode == 0:
        return None
    return Path(toplevel.stdout.strip())


def ignore_entry(root: Path, output: Path) -> str:
    """Return the root-anchored ``.gitignore`` pattern for the output directory, such as ``/qq_docs/``.

    :param root: Work tree top level.
    :param output: Export output directory inside ``root``.
    :return: Pattern matching exactly that directory.
    """
    # os.path.relpath compares drive letters case-insensitively on Windows; Git reports them in upper case.
    return '/' + Path(os.path.relpath(output.resolve(), root)).as_posix() + '/'


def add_ignore_entry(root: Path, output: Path) -> str:
    """Append the output directory to the work tree's root ``.gitignore``, keeping its line endings.

    :param root: Work tree top level containing ``.gitignore``.
    :param output: Export output directory inside ``root``.
    :return: The appended pattern.
    """
    entry = ignore_entry(root, output)
    path = root / '.gitignore'
    content = path.read_bytes()
    newline = b'\r\n' if b'\r\n' in content else b'\n'
    if content and not content.endswith(b'\n'):
        content += newline
    path.write_bytes(content + entry.encode('utf-8') + newline)
    return entry


def check_history_target(output: Path, *, can_ignore_later: bool) -> None:
    """Fail before fetching when the output directory cannot safely hold its own repository.

    A repository inside another work tree is only allowed when that work tree ignores the directory;
    otherwise the outer repository would pick it up as an embedded repository.

    :param output: Export output directory; it may not exist yet.
    :param can_ignore_later: Whether the caller will offer to add the directory to the root ``.gitignore``
        after fetching; the check then only fails when that file does not exist.
    :raises RuntimeError: Git is not installed, or the directory is inside a work tree that does not ignore it
        and cannot be ignored later.
    """
    if shutil.which('git') is None:
        raise RuntimeError('--git needs the git executable on PATH')
    root = unignored_parent_repository(output)
    if root is not None and not (can_ignore_later and (root / '.gitignore').is_file()):
        raise RuntimeError('{} is inside the Git work tree {} but not ignored; add it to that .gitignore before using --git'.format(output, root))


def commit_history(output: Path, result: ExportResult, base_url: str) -> str | None:
    """Commit the exported directory when any page or image changed, creating the repository on first use.

    Changes to only ``README.md`` and ``manifest.json`` (for example a transient fetch error) are not committed.

    :param output: Export output directory.
    :param result: Result of the export just written to ``output``.
    :param base_url: Crawled documentation directory, recorded in the commit message.
    :return: Short hash and subject of the new commit, or None when nothing changed.
    :raises RuntimeError: A Git command failed.
    """
    if not (output / '.git').exists():
        _git('init', '-q', cwd=output)
        # The exporter writes LF files; keep them byte-identical on Windows.
        _git('config', 'core.autocrlf', 'false', cwd=output)
    first = _git('rev-parse', '--verify', '-q', 'HEAD', cwd=output, check=False).returncode != 0
    _git('add', '-A', cwd=output)
    changes = [line.split('\t', 1) for line in _git('diff', '--cached', '--name-status', '--no-renames', cwd=output).stdout.splitlines()]
    changes = [(status, path) for status, path in changes if path not in _SUMMARY_FILES]
    if not changes:
        return None
    pages = [(status, path) for status, path in changes if path.endswith('.md')]
    counts = {status: sum(1 for item, _ in pages if item == status) for status in 'AMD'}
    if first:
        subject = 'docs: snapshot official docs ({} pages)'.format(counts['A'])
    else:
        subject = 'docs: update official docs (+{} ~{} -{} pages)'.format(counts['A'], counts['M'], counts['D'])
    body = ['Source: {}'.format(base_url),
            'Discovered {} documents, exported {}, {} errors.'.format(result.discovered, result.exported, len(result.errors))]
    if not result.complete:
        body.append('Export incomplete; see manifest.json for the errors.')
    if not first:
        body.append('')
        body.extend('{} {}'.format(status, path) for status, path in changes[:_LISTED_CHANGES])
        if len(changes) > _LISTED_CHANGES:
            body.append('... and {} more'.format(len(changes) - _LISTED_CHANGES))
    _git('-c', 'commit.gpgsign=false', 'commit', '-q', '--no-verify', '-F', '-', cwd=output, stdin='\n'.join([subject, '', *body]) + '\n')
    return '{} {}'.format(_git('rev-parse', '--short', 'HEAD', cwd=output).stdout.strip(), subject)
