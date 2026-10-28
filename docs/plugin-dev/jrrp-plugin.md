# 今日人品插件

> **场景**：我已经会写命令和回复了，想看一个真正能用的插件，是怎么把命令、按钮、翻译和数据存储组合在一起的。

读完这一页，你能把一个完整的示例插件装进实例，跑通查询、投稿和撤回的每一步。

这个插件移植自 [LazyAlienWS](https://github.com/UnknownBits/LazyAlienWS) 的今日人品插件（GPL-3.0-only）。它用 QQ Markdown、命令键盘和被动回复拼出完整的功能，运行时只依赖 BotQraft。你可以先从 [qq_jrrp 示例](https://github.com/tanhHeng/BotQraftReforged/blob/main/example_plugins/qq_jrrp/botqraft.plugin.json)看起。

插件本身不带语录。如果想沿用已有的语录，把旧的语录 JSON 列表放到运行实例的 `config/qq_jrrp/luck_sentence.json` 就行，格式见[数据与持久化](#数据与持久化)。

## 安装

按下面三步操作：

1. 把整个 `example_plugins/qq_jrrp` 目录复制到实例的插件目录（默认是 `plugins/`）。`botqraft.plugin.json`、入口包 `qq_jrrp/` 和翻译目录 `lang/` 是插件运行必需的；`LICENSE` 和 `NOTICE` 是许可协议与来源说明，也请一起保留。
2. 启动实例。BotQraft 会自动注册插件根目录 `lang/` 里的翻译文件。

   假设仓库在 `..\BotQraftReforged`，在实例目录里可以这样安装并启动：

   ```powershell
   Copy-Item -Recurse ..\BotQraftReforged\example_plugins\qq_jrrp .\plugins\qq_jrrp
   python -m botqraft start
   ```

3. 如果实例已经在运行，在运维控制台执行 `/botqraft plugin refresh`，就能加载新插件。

插件用 `register_help_message` 为群聊和 C2C 登记了一个 `/jrrp` 帮助项，框架会据此生成帮助和 QQ 面板条目。同一个插件 ID 只能加载一个插件，所以目录版和打包版的 `qq_jrrp` 只放一份就好。

## 查询与文字触发

按下面三步查询：

1. 确认接收设置。想在群里不 @ 机器人、直接发文字触发，需要 QQ 平台推送全量群消息 `GROUP_MESSAGE_CREATE`，这要求账号已经开通接收所有群消息。群里 @ 机器人和 C2C 不需要额外设置。
2. 发送下面任意一种消息：

| 输入               | 支持的消息场景                                              |
| ------------------ | ----------------------------------------------------------- |
| `/jrrp`            | 群聊和 C2C；群 AT 消息会先由框架去掉正文前导空格            |
| `@机器人 今日人品` | 群 AT 消息（平台已去掉提及），以及开头 @ 机器人的全量群消息 |
| `今日人品`         | 普通群消息、群 AT 和 C2C                                    |
| `#今日人品`        | 普通群消息、群 AT 和 C2C                                    |

3. 查看回复。插件用原消息发送被动回复，查询结果会通过 `refer_msg=True` 引用你发的那条查询消息；帮助、投稿和撤回的回复不带引用。发送仍然受平台被动回复时效和 Markdown/键盘权限的限制。

中文触发由 `on_message` 处理。它取出消息的文字正文 `event.message_data.content`，去掉两端空白，只有完全等于「今日人品」或「#今日人品」才算命中。「看看今日人品」、后面带参数的消息、没有文字正文的消息，以及引用消息里的文字，都不会触发。命中后，它用 `server.execute_command('/jrrp', event.get_command_source())` 把消息转交给 `/jrrp` 命令。`/jrrp` 本身由命令树直接处理，不经过这两个别名，所以每条消息只会得到一次回复。

## 评分、语录与按钮

- 幸运指数用的是原插件的算法：结果由发送者的 `User.id` 和运行机器的本地日期共同决定。纯数字 ID 直接作为数值种子，其他 ID 先算 SHA-256。指数在 0–100% 之间，同一天、同一 ID 的结果是固定的；如果更换运行机器的时区，日期切换的时间可能会变。
- 指数从高到低对应六档签文：大吉（85–100）、吉（68–84）、末吉（51–67）、末凶（35–50）、凶（18–34）、大凶（0–17）。
- 群聊和 C2C 都按收到消息里的 `User.id` 计算。两边的 ID 不同时，就当作两个身份分别计算。
- 语录池为空时，回复里会提示用户投稿。语录池不变的情况下，同一个人同一天最多会抽到三种语录，每次查询从中随机选一句。
- 投稿成功的回复带两行四个按钮：「今日人品」「投稿」/「帮助」「撤回投稿」，撤回按钮携带本条投稿的 UUID。其他回复只带一行「今日人品」「投稿」「帮助」。按钮的点击权限对所有人开放，能不能撤回由命令处理函数检查。
- 群聊里所有按钮只把命令填入输入框。C2C 里「今日人品」和「帮助」点击后直接发送；「投稿」填入完整的多行模板，「撤回投稿」填入撤回命令，都要用户确认后再发送。
- 每个用户都可以在 QQ 里发送 `/botqraft pref language set en_us`，把自己的输出语言切换成英文。中英文内容都来自根目录的 `lang/`。回复正文用带 `qq_jrrp.` 命名空间的 `server.rtr(...)` 延迟翻译；按钮标签和投稿模板则用 `server.tr(...)`，在发送前按当前用户的语言翻译成字符串。

## 投稿与撤回

插件提供下面几条命令：

```text
/jrrp help
/jrrp post
/jrrp withdraw <id>
```

投稿按下面两步：

1. 先发送 `/jrrp post`，看看投稿方法。
2. 点投稿按钮填入模板，或者直接发送下面的多行消息：

   ```text
   /jrrp post '''
   在此处填写文本 可换行
   '''
   作者《出处》
   ```

写的时候注意：`post` 后面先空一格，再写起始标记 `'''`，然后立即换行。结束标记 `'''` 要独占一行，作者或出处写在它的下一行。文本和出处都不能为空，否则插件会回复「投稿参数错误」，并附上投稿方法。

正文里的空格和换行会原样保留，出处会去掉两端空白。普通引号和反斜杠可以直接输入。正文之后第一个独占一行的 `'''` 会被当作结束标记，所以正文里需要出现同样的内容时，请把它和其他文字放在同一行。

`/jrrp`、`/jrrp help`、`/jrrp post` 和 `/jrrp withdraw` 分别由 `jrrp_handler`、`help_handler`、`post_handler` 和 `withdraw_handler` 处理。`post` 后面的投稿内容用 `GreedyText` 整段收集，再交给 `parse_submission` 检查标记和非空字段；`withdraw` 后面的 ID 用 `Text` 读取一个词。

撤回按下面两步：

1. 先取得要撤回的 UUID。投稿成功消息里的撤回按钮已经带上了它。
2. 发送 `/jrrp withdraw <id>`，把 `<id>` 换成该 UUID。只发 `/jrrp withdraw` 会回复撤回方法。

只有投稿者本人，或者权限等级不低于 2 的用户才能撤回。权限等级是怎么来的，见[权限系统](permissions.md#了解权限优先级)。

## 数据与持久化

语录保存在实例的 `config/qq_jrrp/luck_sentence.json`，目录由 `server.get_data_folder()` 得到。文件是 UTF-8 编码的 JSON 列表，每条记录有四个字段：

| 字段       | 内容                          |
| ---------- | ----------------------------- |
| `id`       | 语录的 UUID，撤回时用它定位。 |
| `sender`   | 投稿者的 `User.id`。          |
| `sentence` | 语录正文。                    |
| `from`     | 作者或出处。                  |

```json
[
  {
    "id": "9a529ca0-3aea-4724-992e-8214217f8864",
    "sender": "投稿者的 User.id",
    "sentence": "语录正文",
    "from": "作者《出处》"
  }
]
```

写入时，插件先在同一目录写一个临时文件，再用它整体替换原文件，避免写到一半时损坏数据。读写操作由一把锁保护，一次只进行一个。撤回会把对应的记录从列表中删除。

沿用旧数据时，只要每条记录都有 `sender`、`sentence` 和 `from` 就能读取。缺少 `id` 的记录会补上 UUID；形如 `前缀:group:用户` 或 `前缀:c2c:用户` 的旧 `sender` 只保留最后的用户部分。只要整个文件校验通过，这些改动会在第一次读取时自动写回文件。旧数据里数字形式的 `sender` 会原样保留。它和任何 `User.id` 字符串都不相等，所以这类记录只有权限等级不低于 2 的用户能撤回。

遇到下面任何一种情况，插件会记录日志并回复「语录数据读写失败」，不会改动文件：

- 文件不是合法 JSON，或者不是列表。
- 记录缺少字段，或者正文、出处为空。
- `id` 不是标准 UUID，或者 `id` 重复。

权限检查放在命令处理这一层：

- 投稿时，用发送者的 `User.id` 作为 `sender`，记下投稿者。
- 撤回时先按 `id` 查找，找不到就回复「撤回失败」。找到后，只有 `sender` 和你的 `User.id` 相同，或者你的权限等级不低于 2，才会删除；否则回复「无权撤回」。

## 完整代码

整个插件按目录格式组织。仓库里的 [`example_plugins/qq_jrrp/`](https://github.com/tanhHeng/BotQraftReforged/tree/main/example_plugins/qq_jrrp) 就是完整代码，复制到插件目录就能加载：

| 文件                               | 内容                                                                                           |
| ---------------------------------- | ---------------------------------------------------------------------------------------------- |
| `botqraft.plugin.json`             | 元数据：ID `qq_jrrp`、入口 `qq_jrrp`、资源 `lang`/`LICENSE`/`NOTICE`、依赖 `botqraft>=0.1.0`。 |
| `qq_jrrp/__init__.py`              | `on_load` 命令树、`on_message` 文字别名、四个处理函数和 `parse_submission`。                   |
| `qq_jrrp/fortune.py`               | `daily_luck` 每日指数和 `luck_category` 分档。                                                 |
| `qq_jrrp/storage.py`               | `Sentence` 记录，以及 `SentenceStore` 的 `choose`、`add`、`withdraw` 和原子写入。              |
| `qq_jrrp/messages.py`              | 带插件命名空间的 `_rtr`、Markdown 转义和各条回复的拼装。                                       |
| `qq_jrrp/keyboard.py`              | `command_keyboard`，按群聊/C2C 和是否有投稿 ID 生成按钮。                                      |
| `lang/zh_cn.yml`、`lang/en_us.yml` | 所有回复、按钮标签和投稿模板的中英文文本。                                                     |
| `LICENSE`、`NOTICE`                | GPL-3.0 许可协议与来源说明。                                                                   |

入口模块里注册命令和文字别名的部分如下（摘自 `qq_jrrp/__init__.py`）：

```python
def on_load(server: QQPluginServerInterface, prev_module: ModuleType | None) -> None:
    store = SentenceStore(Path(server.get_data_folder()) / 'luck_sentence.json')
    root = Literal(COMMAND).requires(lambda source: source.has_permission(0))
    root.runs(lambda source: jrrp_handler(server, store, source))
    root.then(Literal('help').runs(lambda source: help_handler(server, source)))
    root.then(Literal('post').runs(lambda source: post_handler(server, store, source)).then(
        GreedyText('payload').runs(lambda source, context: post_handler(server, store, source, context['payload']))
    ))
    root.then(Literal('withdraw').runs(lambda source: withdraw_handler(server, store, source)).then(
        Text('id').runs(lambda source, context: withdraw_handler(server, store, source, context['id']))
    ))
    server.register_command(root, scope=('group', 'c2c'))
    server.register_help_message(COMMAND, _rtr(server, 'panel_description'), scope=('group', 'c2c'))


def on_message(server: QQPluginServerInterface, event: QQMessageReceived) -> None:
    # Exact aliases only: command-tree execution already handles /jrrp.
    # Do not remove apparent mentions or guess identities from message text.
    content = event.message_data.content
    if isinstance(content, str) and content.strip() in _ALIASES:
        server.execute_command(COMMAND, event.get_command_source())
```

想了解撤回流程，可以看 `withdraw_handler` 和 `SentenceStore.withdraw`；按钮怎么区分群聊和 C2C，看 `command_keyboard`。

接下来，回到[插件开发](index.md)，照着这套结构写你自己的插件。
