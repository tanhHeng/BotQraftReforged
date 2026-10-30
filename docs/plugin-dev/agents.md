# 用 AI Agent 开发插件

> **场景**：我想让 Codex、Claude Code 或 Cursor 这类 AI Agent 帮我写插件，可它总是照着 NoneBot 或 MCDR 的写法乱猜接口。怎么让它按 BotQraft 的规矩来？

读完这一页，你能在插件项目里放好一份 `AGENTS.md`，让 AI Agent 按 BotQraft 的公开接口写代码、按正确的步骤验证。

AI Agent 每次开工前，会先读项目根目录的说明文件。把下面的模板保存成插件项目根目录的 `AGENTS.md`，再把 `<your_plugin_id>` 换成你的插件 ID 就行。模板用英文写，各家 Agent 都能稳定理解；你和 Agent 对话时照样可以用中文。

不同工具认的文件名不一样：Codex、Cursor 等读 `AGENTS.md`，Claude Code 读 `CLAUDE.md`。用 Claude Code 的话，新建一个 `CLAUDE.md`，里面只写一行 `@AGENTS.md`，它就会把模板一起读进来。

## 模板

```md
# AGENTS.md

This repository is a BotQraft plugin. BotQraft is an official QQ bot framework built on MCDReforged; plugins run in QQ group chats and C2C (one-to-one) chats.

Plugin ID: `<your_plugin_id>`. The data folder, translation key prefix and dependency declarations all use this ID.

## Read the docs; do not guess APIs

- Plugin development docs: https://botqraft.tanh.moe/plugin-dev/ (Chinese). Read the pages relevant to the task before writing code.
- The installed `botqraft` package is the source of truth for names. When unsure, run `python -c "import botqraft.api.<module> as m; print(m.__all__)"`.
- Do not apply patterns from NoneBot, go-cqhttp, OneBot or MCDR server plugins. BotQraft reuses only MCDR's plugin, command tree, permission and translation systems.

## Plugin layout

- A single-file plugin defines module-level `PLUGIN_METADATA`. A directory plugin has `botqraft.plugin.json` at its root; its source package must be named exactly like the plugin ID, and the root must not contain `__init__.py`.
- Declare the framework dependency as `"botqraft": ">=0.1.0"`, never `mcdreforged`. Third-party libraries go in `requirements.txt`; the framework checks them but never installs them.
- Translation files live in the root `lang/<language>.yml`. When packing, list `lang` in the metadata `resources`.

## Coding rules

- Import only from the public `botqraft.api` submodules: `command`, `event`, `decorator`, `qtext`, `types`, `exception`, `utils`. Never import internal `botqraft` modules.
- Do not use Minecraft features (RCON, server info, `RText`); they raise `UnsupportedOperationError` or `TypeError`.
- Register commands, help entries, event listeners and translations in `on_load(server, prev_module)`. These registrations are cleared automatically on unload.
- Prefer `SimpleCommandBuilder`. Root names include the `/`, e.g. `/roll <count>`. To restrict scenes, use `for root in builder.build(): server.register_command(root, scope=('group',))` and pass the same `scope` to `server.register_help_message(...)`.
- Reply to the triggering message with `source.reply(...)`. This is a passive reply, valid for 5 minutes in groups and 60 minutes in C2C.
- For later or scheduled messages use `server.send(source.target, ...)`. `send` accepts only `Group` or `C2C` targets, never `User`.
- To mention someone, put `QTextAt(...)` into the message content. Mentions work only in group chats.
- Send images, video, voice and files with `QImage`, `QVideo`, `QVoice`, `QFile`; pass local files as `pathlib.Path`. Media messages cannot carry text, so send any caption as a separate message.
- User-visible text must be translation keys `<your_plugin_id>.<key>`, sent with `server.rtr(...)`. Use `server.tr(...)` only when a plain string is needed immediately (e.g. button labels).
- Plugin callbacks run on the framework's single synchronous executor thread. Never `time.sleep`, loop for long, or make blocking network calls in a callback, and never use `schedule_task(..., block=True)` or call `.result()` on your own scheduled task there.
- For long-running loops, start a thread with `botqraft.api.decorator.new_thread` and a `threading.Event`; in `on_unload`, `set()` the event and `join(timeout=...)` the thread.
- Store runtime data under `server.get_data_folder()` (`config/<your_plugin_id>/`). Read packaged resources with `server.open_bundled_file(...)`.
- Pass `return_future=True` when you need the send result; on failure read `category`, `err_code` and `trace_id` from `NetworkError`. Never resend automatically after `ResultUnknownError`; the platform may already have accepted it.
- Write logs, exceptions and code comments in English. Never put the `appid` or `secret` from `config.yml` into code or logs.

## Verification

1. Offline: check syntax with `python -m py_compile`. For messages that can be built offline, assert fields on `message.to_payload()`.
2. Instance: put the plugin into the instance `plugins/` folder. In the ops console run `/botqraft plugin refresh` (new plugin) or `/botqraft plugin reload <your_plugin_id>` (already loaded), then confirm with `/botqraft plugin list`.
3. QQ: send the command once in a group chat (mention the bot first) and once in a C2C chat. On errors, read `logs/botqraft.log` first.
4. Step 3 needs a human in QQ. Tell the user exactly what to send and what to look for, then wait for their report; treat what they report as fact.
5. Only call a step "verified" if it was actually run.
```

## 用起来更顺手的小建议

- 第一次让 Agent 干活时，先让它读一遍模板里列出的文档页面，再开始写代码。
- 提需求时，像页面开头的“场景”那样写：要什么命令、在哪种聊天里用、回复长什么样。需求越具体，它越少猜。
- Agent 说“已经验证过了”的时候，问一句它具体跑了哪一步。QQ 里的实际效果，最后还是要你自己发条消息看一看。

接下来，可以对照[今日人品示例](jrrp-plugin.md)，看看一个完整插件的结构，再让 Agent 照着写。
