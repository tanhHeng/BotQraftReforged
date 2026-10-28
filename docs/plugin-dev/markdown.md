# Markdown 消息与文本交互

> **场景**：我想让回复带粗体标题和列表，还想在消息里放一个提及，让对方收到 @ 提醒。该怎么写？

这一页讲怎么在插件里拼出 QQ 的 Markdown 消息，以及“点一下就提及用户”“点一下填入输入框”这类文本交互。读完这一页，你能构造出可以直接发送的消息数据。

消息对象都从 `botqraft.api.qtext` 导入。先构造消息数据，再把它交给[回复接口](reply.md)发出去。要真正发送，账号需要拥有 Markdown 权限。

## 构造 Markdown 消息

写进 `QMarkdown` 构造器的字符串会被当成 Markdown。追加用户文本时用 `append`，普通字符串和 `QText` 会按纯文本转义：

```python
from botqraft.api.qtext import QMarkdown, QText

message = QMarkdown('**Echo**: ').append(QText('<hello>'))
payload = message.to_payload()
assert payload['msg_type'] == 2
assert payload['markdown']['content'] == '**Echo**: &lt;hello&gt;'
```

`QText` 发出去是普通文本消息（`msg_type` 为 0），`QMarkdown` 则是 Markdown 消息（`msg_type` 为 2）。`QMarkdown.append(...)` 遇到 `str` 或 `QText`，会自动转义 HTML（`&`、`<`、`>`）和 Markdown 特殊字符；遇到另一个 `QMarkdown`，则保留它的 Markdown 标记。

几种组合方式的区别：

- `append`、`set_keyboard` 修改消息本身，并返回它自己。
- `+` 生成一个新对象，两边的操作数都不变。
- `copy()` 复制消息，副本有自己的键盘，不和原消息共享。

`QText` 和 `QMarkdown` 相加，结果是 `QMarkdown`，其中 `QText` 部分按纯文本转义。`set_keyboard(None)` 会移除键盘。每条组合消息最多只能有一个键盘：组合出第二个键盘时会抛出 `ValueError`，原来的内容和键盘保持不变。键盘和按钮的写法见[按钮：键盘与点击响应](interactions.md)。

## 添加文本交互

文本交互用专门的对象来表达。追加到 `QMarkdown` 的普通字符串里，即使出现标签样式的文字，也会被转义成普通文本。但 `QMarkdown(...)` 构造器里的字符串，以及直接发送的 `QText` 文本，都会原样提交，所以不要把用户输入放进去。

`QTextAt`、`QTextInput` 可以直接发送，可以用加法和其他消息组合，也可以作为 `tr/rtr` 的格式化参数。无论经过 Markdown 转换、复制还是延迟翻译，它们都仍然是交互标签。

```python
from botqraft.api.qtext import QTextAt, QTextInput, QMarkdown

message = QMarkdown('**请选择：** ').append(
    QTextAt('actual_member_openid'), ' ',
    QTextInput('/echo 编辑内容', show='编辑后发送', reference=True),
)
```

### 提及用户

`QTextAt(target)` 可以接收一个 `User`（包括它的子类 `MentionedUser`），也可以接收提及 ID 字符串。传入 `User` 时，它只看 `member_openid`；`id`、`user_openid` 和昵称都不参与生成提及。群消息里的 `source.user`，以及 `event.message_data.mentions` 中的用户，都带有 `member_openid`，直接传进去就行。

生成的内容是一个 `<qqbot-at-user id="member_openid" />` 标签。直接发送时，它是一条普通文本消息；追加到 `QMarkdown` 时，标签原样保留。

以下情况会出错：

- `member_openid` 为 `None`（例如私聊用户），或者目标既不是 `User` 也不是字符串：抛出 `TypeError`。
- ID 是空字符串，或包含 `<`、`>`、`"`、`&`、换行符：抛出 `ValueError`。

框架不会检查你在什么场景下发送。按平台说明，提及只在群聊中生效。另外，BotQraft 没有提供 @全体成员 对象。

### 填入输入框

`QTextInput(text, *, show=None, reference=False, keyboard=None)` 是 `QMarkdown` 的子类，只能用在 Markdown 里。`text` 和 `show` 都传编码前的原始字符串，各最多 100 个 Unicode 字符。接口先检查长度，再分别对它们做一次 URL 编码。`show=None` 时不写展示文本，客户端会默认展示 `text`。

`reference` 必须是 bool，会写成标签里的 `reference="true"` 或 `"false"`。它决定用户点击、内容填入输入框时，是否同时带上对这条消息的引用回复。这和发送消息时的引用是两回事，后者用 `refer_msg` 单独设置。

参数类型不对会抛出 `TypeError`；编码前超过 100 字符会抛出 `ValueError`。

用加法把 `str` / `QText` 和 `QTextInput` 组合起来，结果会自动变成 `QMarkdown`，同时发出一条 `UserWarning`。如果一开始就用 `QMarkdown` 组合，就能直接得到 Markdown 结果。`QText.append(QTextInput)` 会抛出 `TypeError`，原对象不受影响；这时请改用加法或 `QMarkdown`。

复制出的消息有自己的键盘，追加失败时原内容保持不变。还有一点要留意：如果直接给 `QText`（包括 `QTextAt` 和含提及的组合结果）的 `.text` 重新赋值，新文本会被当成普通文本。转成 Markdown 时它会被整体转义，原先的提及标签也就不在了。

这些标签的协议依据见 QQ 官方文档[文本交互](https://bot.q.qq.com/wiki/develop/api-v2/server-inter/message/trans/text-chain.html)。其中，编码前 100 字符的限制是 BotQraft 自己定的。客户端怎么展示、能否点击填入、引用是否生效，取决于 QQ 平台的支持情况。

接下来，阅读[按钮：键盘与点击响应](interactions.md)，在消息下面挂上按钮。
