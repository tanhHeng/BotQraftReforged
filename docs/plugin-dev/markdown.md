# Markdown 消息与文本交互

> **场景**：我想让回复带粗体标题和列表，还想在消息里放一个提及，让对方收到 @ 提醒。该怎么写？

这一页讲怎么在插件里拼出 QQ 的 Markdown 消息，以及“点一下就提及用户”“点一下填入输入框”这类文本交互。读完你能构造出可直接发送的消息数据。

从 `botqraft.api.qtext` 导入消息对象。先构造消息数据，再把它传给[回复接口](reply.md)。实际发送需要账号拥有 Markdown 权限。

## 构造 Markdown 消息

`QMarkdown` 构造器中的字符串按 Markdown 处理。追加用户文本时使用 `append`，普通字符串和 `QText` 会按纯文本转义：

```python
from botqraft.api.qtext import QMarkdown, QText

message = QMarkdown('**Echo**: ').append(QText('<hello>'))
payload = message.to_payload()
assert payload['msg_type'] == 2
assert payload['markdown']['content'] == '**Echo**: &lt;hello&gt;'
```

`QText` 发送时是普通文本消息（`msg_type` 为 0），`QMarkdown` 是 Markdown 消息（`msg_type` 为 2）。`QMarkdown.append(...)` 遇到 `str` 或 `QText` 时，会自动转义 HTML（`&`、`<`、`>`）和 Markdown 特殊字符；追加另一个 `QMarkdown` 时保留其 Markdown 标记。

`append`、`set_keyboard` 修改自身并返回自身，`+` 生成新对象、不改动两边的操作数，`copy()` 复制消息并隔离键盘。`QText` 与 `QMarkdown` 相加时结果是 `QMarkdown`，`QText` 部分按纯文本转义。`set_keyboard(None)` 移除键盘。每条组合消息最多包含一个键盘：组合出第二个键盘时抛出 `ValueError`，原内容和键盘保持不变。键盘和按钮的写法见[按钮：键盘与点击响应](interactions.md)。

## 添加文本交互

使用对象表达交互能力。追加到 `QMarkdown` 的普通字符串里，标签样式的文字会被转义成普通文本；但 `QMarkdown(...)` 构造器里的字符串和直接发送的 `QText` 文本都会原样提交，不要把用户输入放进去。`QTextAt`、`QTextInput` 可以直接发送，也可以通过加法组合，或作为 `tr/rtr` 的格式化参数。交互对象的标签身份在 Markdown 转换、复制和延迟翻译中保留。

```python
from botqraft.api.qtext import QTextAt, QTextInput, QMarkdown

message = QMarkdown('**请选择：** ').append(
    QTextAt('actual_member_openid'), ' ',
    QTextInput('/echo 编辑内容', show='编辑后发送', reference=True),
)
```

### 提及用户

`QTextAt(target)` 接收 `User`（包括它的子类 `MentionedUser`）或提及 ID 字符串。传入 `User` 时只读取它的 `member_openid`；`id`、`user_openid` 和昵称都不参与生成提及。生成的消息内容是 `<qqbot-at-user id="member_openid" />` 标签，直接发送时是普通文本消息，追加到 `QMarkdown` 时标签原样保留。群消息里的 `source.user` 和 `event.message_data.mentions` 中的用户都带有 `member_openid`，可以直接传入。

`member_openid` 为 `None`（例如私聊用户）或目标既不是 `User` 也不是字符串时，抛出 `TypeError`。空字符串，或包含 `<`、`>`、`"`、`&`、换行符的 ID 会抛出 `ValueError`。框架不检查发送场景；按平台说明，提及只在群聊中生效。BotQraft 没有提供 @全体成员 对象。

### 填入输入框

`QTextInput(text, *, show=None, reference=False, keyboard=None)` 是 `QMarkdown` 的子类，只用于 Markdown。传入编码前的 `text` 和 `show` 字符串，各最多 100 个 Unicode 字符。接口校验长度后对它们各做一次 URL 编码。`show=None` 时省略展示文本，客户端默认展示 `text`。

`reference` 必须是 bool，写入标签的 `reference="true"`/`"false"`，控制用户点击后填入输入框时是否带上本消息的引用回复。发送消息时的引用使用 `refer_msg` 单独设置。参数类型错误抛出 `TypeError`，编码前超出 100 字符抛出 `ValueError`。

`str` / `QText` 与 `QTextInput` 通过加法组合时，结果自动转换为 `QMarkdown`，并发出 `UserWarning`。显式使用 `QMarkdown` 组合即可直接获得 Markdown 结果。`QText.append(QTextInput)` 会抛出 `TypeError` 并保留原对象，请改用加法或 `QMarkdown`。

复制会隔离键盘，追加失败时保留原内容。给 `QText`（包括 `QTextAt` 和含提及的组合结果）直接重新赋值 `.text` 后，新文本会被当成普通文本：转成 Markdown 时整体转义，原先的提及标签不再保留。

协议依据见 QQ 官方文档[文本交互](https://bot.q.qq.com/wiki/develop/api-v2/server-inter/message/trans/text-chain.html)。编码前 100 字符校验是本库自己的选择。客户端展示、点击填入和引用效果由 QQ 平台支持决定。

接下来，阅读[按钮：键盘与点击响应](interactions.md)，在消息下面挂上按钮。
