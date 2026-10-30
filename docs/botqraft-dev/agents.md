# 用 AI Agent 开发框架

这一页写给用 AI Agent 改 BotQraft 框架的贡献者。读完这一页，你能在源码仓库根目录放好一份 `AGENTS.md`，让 Agent 了解仓库结构、架构约束和验证方式。

Agent 每次开工前会先读仓库根目录的说明文件。把下面的模板保存成源码仓库根目录的 `AGENTS.md` 就行。模板用英文写，和仓库里代码、注释、提交信息的语言保持一致。Codex、Cursor 等读 `AGENTS.md`；Claude Code 读 `CLAUDE.md`，可以新建一个只写一行 `@AGENTS.md` 的 `CLAUDE.md`。

只是写插件的话，请用[插件开发里的模板](../plugin-dev/agents.md)。

## 模板

```md
# AGENTS.md

This is the source repository of the BotQraft framework itself: a Python framework built on MCDReforged 2.16.2 that talks to the official QQ bot API and supports group and C2C (one-to-one) chats.

## Repository map

- `botqraft/`: framework code. Subpackage responsibilities are described in `docs/botqraft-dev/architecture.md`.
- `botqraft/api/`: the complete public plugin API, defined by each module's `__all__`. Changing it changes the public contract.
- `example_plugins/`: example plugins `echo.py` and `qq_jrrp/`. `qq_jrrp` is GPL-3.0-only: when modifying it, append dated modification notes to the module docstrings and `NOTICE`; never rewrite earlier notes.
- `docs/`: VitePress documentation site, written in Simplified Chinese. `docs/plugin-dev/` is the public contract plugin developers rely on.
- `tests/` (local regression tests) and `test/` (local running instance) are Git-ignored and may be absent from a fresh clone. Never assume they are available or add them to commits.

## Order of authority

1. Code and observed runtime behavior.
2. Official QQ platform documentation at https://bot.q.qq.com/wiki/. Cite the relevant page when changing platform-dependent behavior. If observed platform behavior differs from the docs, explain the evidence and document the constraint in the relevant tracked documentation.
3. Tracked documentation in `docs/`. If it conflicts with the code, report the discrepancy to the maintainer before changing behavior. Local reference snapshots and design notes are not included in this repository; do not require them for development.

## Architecture constraints

- Three execution lanes: a network event loop on its own thread (gateway, HTTP); a single-threaded synchronous executor (plugin callbacks, commands, plugin load and unload); an asynchronous executor (plugin coroutines). Never block the network loop, and never make code wait on the executor it is running on.
- Every QQ send is validated by `MessageSender` before being submitted to the network loop. Failures are delivered through Futures and logged exactly once via `observe_future` / `report_error`. New send paths must use the same chain.
- Passive reply contexts are kept per scene: 300 seconds for groups, 3600 seconds for C2C (`MessageSender.PASSIVE_LIFETIME`).
- Credentials and access tokens must never appear in logs. New sensitive fields must be wired into the logger's `secret_filter` and the raw-response log redaction.
- After a gateway disconnect the client identifies again instead of resuming; reconnects do not fire `on_botqraft_start` again.

## Code conventions

- Logs, exceptions and comments are in English; no Chinese literals in source code. User-visible text is a translation key in `botqraft/resources/lang/`.
- Public APIs get English Sphinx field-list docstrings (`:param:`, `:return:`, `:raises:`); no `:type:` or `:rtype:`.
- Annotate instance methods with `self: Self` (from `typing_extensions`); put type-checking-only imports under `if TYPE_CHECKING:`.
- The version lives only in `VERSION` in `botqraft/constants/core_constant.py`.
- Rename public APIs in one cutover: update every caller, example and doc page, and leave no compatibility aliases.

## Verification

- Install with `python -m pip install -e .`. If a local instance runs an older non-editable install, your changes will not take effect; confirm with `python -c "import botqraft; print(botqraft.__file__)"` that the source tree is imported.
- Regression tests: when `tests/` exists, run `python -m unittest discover -s tests -q`. Tests use local aiohttp fake servers and never contact real QQ.
- Capability probe: `python -m botqraft.compatibility.probes`.
- Docs: `pnpm run docs:build`. The build only checks page links; verify `#anchors` separately.
- Live verification needs QQ credentials and a human sending messages: state exactly what to send and what to look for, then wait for the maintainer's report and treat it as fact.
- Only call a check "verified" if it was actually run.

## Commits

- Format: `<type>: <lowercase English imperative>`, subject at most 72 characters; types are `feat`, `fix`, `refactor`, `docs`, `chore`.
- The pre-commit hook runs `vp check --fix` on staged files.
- When public behavior changes, update the matching `docs/plugin-dev/` pages in the same commit.
- Do not push on your own; leave that to the maintainer.
```

## 和 Agent 协作的小建议

- 让 Agent 先读[框架结构](architecture.md)和[代码与文档约定](conventions.md)，再动手。
- 涉及 QQ 平台行为的改动，让它先查阅 [QQ 官方文档](https://bot.q.qq.com/wiki/)，并在回复里引用具体页面。
- Agent 说“测试通过”时，确认它说的是哪一组测试；真机上的表现，还需要你自己在 QQ 里看一看。

接下来，回到[栏目首页](index.md)挑一个方向开始吧。
