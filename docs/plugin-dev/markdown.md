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

`QText` 编码普通文本，`QMarkdown.append(str_or_QText)` 会自动转义 HTML 和 Markdown 特殊字符。追加另一个 `QMarkdown` 时保留其 Markdown 标记。

`append`、`set_keyboard` 修改自身，`+` 生成副本，`copy()` 复制消息并隔离键盘。`set_keyboard(None)` 移除键盘。每条组合消息最多包含一个键盘。重复组合会抛出 `ValueError`，原内容和键盘保持不变。键盘和按钮的写法见[按钮：键盘与点击响应](interactions.md)。

## 添加文本交互

使用对象表达交互能力。普通字符串中的标签样式文字按文本处理。`QTextAt`、`QTextInput` 可以直接发送，也可以通过加法组合，或作为 `tr/rtr` 的格式化参数。交互对象的标签身份在 Markdown 转换、复制和延迟翻译中保留。

```python
from botqraft.api.qtext import QTextAt, QTextInput, QMarkdown

message = QMarkdown('**请选择：** ').append(
    QTextAt('actual_member_openid'), ' ',
    QTextInput('/echo 编辑内容', show='编辑后发送', reference=True),
)
```

### 提及用户

`QTextAt(target)` 接收 `User` 或明确的提及 ID 字符串。传入 `User` 时只读取它的 `member_openid` 作为提及地址；`User.id` 和昵称不会参与生成提及，也不会写进消息。群消息里的 `source.user` 带有 `member_openid`，可以直接传入。

请使用非空、可用的 `member_openid`。缺少该字段或目标类型错误会抛出 `TypeError`。空 ID 或包含协议分隔符的 ID 会抛出 `ValueError`。当前支持群聊文本与 Markdown 中的单用户提及，@全体成员不在当前支持范围内。

### 填入输入框

`QTextInput(text, *, show=None, reference=False)` 用于 Markdown。传入编码前的 `text` 和 `show` 字符串，各最多 100 个 Unicode 字符。接口校验长度后进行一次 URL 编码。`show=None` 时省略展示文本。

`reference` 使用 bool，控制客户端填入输入框时的回复引用。发送消息的引用使用 `refer_msg` 单独设置。参数类型错误抛出 `TypeError`，编码前超出 100 字符抛出 `ValueError`。

`str` / `QText` 与 `QTextInput` 通过加法组合时，结果自动转换为 `QMarkdown`，并发出 `UserWarning`。显式使用 `QMarkdown` 组合即可直接获得 Markdown 结果。`QText.append(QTextInput)` 会抛出 `TypeError` 并保留原对象，请改用加法或 `QMarkdown`。

复制会隔离键盘，追加失败时保留原内容。直接重新赋值 `.text` 会按新的普通文本重建 Markdown 副本，旧交互片段的身份随旧副本一起替换。

协议依据见仓库中的 [QQ 文本链文档](https://github.com/tanhHeng/BotQraftReforged/blob/main/reference/qq_docs/server-inter/message/trans/text-chain.md)。编码前 100 字符校验是本库自己的选择。客户端展示、点击填入和引用效果由 QQ 平台支持决定。

接下来，阅读[按钮：键盘与点击响应](interactions.md)，在消息下面挂上按钮。
