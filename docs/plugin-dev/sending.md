# 主动发送、引用与撤回

读完这一页，你能主动向群聊或 C2C 私聊发消息，发送图片、视频、语音和文件，给消息加上引用，并撤回已经发出的消息。

主动发送和被动回复是两条不同的路。被动回复跟在收到的消息后面，用它的消息 ID 回复。主动发送由你指定一个目标，随时发起。

## 主动发送

主动发送只有一个接口：

```python
server.send(target, message, refer_msg=None, return_future=False)
```

`target` 说明消息发到哪个会话，只能是下面两种之一，都从 `botqraft.api.types` 导入：

| 目标                  | 发到哪里              |
| --------------------- | --------------------- |
| `Group(group_openid)` | 指定的群聊。          |
| `C2C(user_openid)`    | 指定用户的 C2C 私聊。 |

C2C 就是机器人和用户之间的一对一私聊。目标里的 OpenID 必须来自平台推送的数据，不能自己编。

最常见的情况，是发回命令所在的会话。`source.target` 会根据收到的消息，直接给出对应的 `Group` 或 `C2C`，不用自己判断场景：

```python
from botqraft.api.command import QQCommandSource
from botqraft.api.types import QQPluginServerInterface

def notify_later(server: QQPluginServerInterface, source: QQCommandSource):
    return server.send(source.target, 'Task completed', return_future=True)
```

目标只包含会话地址，可以先保存下来，等后台任务完成后再发送。想拿到平台的确认结果，就用返回的 Future，见[等待平台结果](reply.md#等待平台结果)。主动消息受 QQ 账号和平台规则约束，请把发送失败当作正常结果来处理。

`message` 支持 `str`、`QText`、`QMarkdown`、延迟翻译文本，以及下文的[媒体消息](#发送图片视频语音和文件)。富文本与翻译分别见 [Markdown、文本交互与键盘](markdown.md)和[翻译与用户语言](translation.md)。

## 目标、用户与 AT 是三件事

`send` 不接受 `User`。用户对象回答"是谁"，发送目标回答"发到哪里"，两者分开写，读代码时就不用猜消息会进群还是进私聊：

- 发到群：使用 `Group`，或在群消息的命令里用 `source.target`。
- 发到私聊：使用 `C2C`，或在 C2C 消息的命令里用 `source.target`。群消息里的用户不提供私聊地址，不能由此发起私聊。
- 在群里 AT 某人：AT 属于消息内容，用 `QTextAt` 拼进消息，见[Markdown、文本交互与键盘](markdown.md)。

```python
from botqraft.api.command import QQCommandSource
from botqraft.api.types import QQPluginServerInterface
from botqraft.api.qtext import QTextAt

def remind_member(server: QQPluginServerInterface, source: QQCommandSource):
    message = QTextAt(source.user) + ' Task completed'
    return server.send(source.target, message, return_future=True)
```

`User.id` 用于真实身份、权限和偏好，见[区分用户身份和会话地址](message-format.md#区分用户身份和会话地址)。

要发给多个会话时，列出所有目标，逐个调用 `send`，并分别处理每个 Future 的结果。

## 发送图片、视频、语音和文件

媒体消息用 `QImage`、`QVideo`、`QVoice`、`QFile` 表示，从 `botqraft.api.qtext` 导入。它们和文字一样交给 `send` 或 `reply`，上传由框架完成：

```python
from pathlib import Path

from botqraft.api.command import QQCommandSource
from botqraft.api.qtext import QImage

def send_chart(source: QQCommandSource):
    return source.reply(QImage(Path('chart.png')), return_future=True)
```

媒体的来源有四种写法：

| 来源               | 写法                                  | 说明                                                                   |
| ------------------ | ------------------------------------- | ---------------------------------------------------------------------- |
| 公网 URL           | `QImage('https://example.com/a.png')` | 平台自己下载。字符串只接受 `http://` 或 `https://` 开头的地址。        |
| 本地文件           | `QImage(Path('a.png'))`               | 本地文件必须用 `pathlib.Path`，普通字符串会被当作错误的 URL 拒绝。     |
| 内存数据           | `QImage(data, name='a.png')`          | `bytes` 会在构造时复制一份，之后改动原数据不影响发送。                 |
| 可 seek 的二进制流 | `QFile(stream, name='report.pdf')`    | 从流的当前位置读到末尾。发送的 Future 完成前请保持流打开且不要改动它。 |

内存数据和流必须提供 `name`，也就是对方看到的文件名；本地文件默认使用文件名。

构造时就会检查来源：文件不存在、为空、超过 200 MiB，或者流不能 seek，都会立刻抛出异常。文件格式由平台判断，框架不做转换，例如语音需要你自己准备平台支持的格式。

使用时有几点限制：

- 一条媒体消息只有媒体本身，不能附带文字或键盘。`QText('说明') + QImage(...)` 会抛出 `TypeError`；需要说明文字时，单独再发一条。
- 每次发送都会重新上传到目标会话。同一个 `QImage` 对象可以多次发送，但每次都会上传。
- 上传需要时间。用 `reply` 回复时，如果上传结束时已经超过被动回复的有效期，框架不会再发出消息，Future 以 `PassiveReplyExpiredError` 结束。大文件建议改用 `send` 主动发送。
- 上传失败、平台拒绝和网络错误都通过 Future 报告，处理方式与文字消息相同，见[处理发送结果](#处理发送结果)。

## 引用消息

引用展示用显式的 `refer_msg`，它和被动回复的资格是两回事。给 `send`、`reply` 或 `reply_event` 传入同会话的 `QQMessageReceived` 或 `QQMessageReceipt`，就能带上引用：

```python
from botqraft.api.command import QQCommandSource

def reply_with_quote(source: QQCommandSource):
    return source.reply(
        'Quoted reply',
        refer_msg=True,
        return_future=True,
    )
```

本例要求原消息带有可用的引用索引。默认回复只关联被动上下文。传入 `refer_msg` 后，框架才会提交引用展示字段。

回复触发命令的原消息时，`source.reply(..., refer_msg=True)` 就等同于传入 `source.message_received`，`server.reply(source, ..., refer_msg=True)` 也支持同样的简写。传 `False` 或省略参数时不展示引用。想引用另一条消息，继续传入消息事件或发送回执即可。这个布尔简写只用于 `reply`；其他发送接口仍需明确指定引用对象。原消息缺少引用索引时仍会抛出 `ValueError`，请按平台实际提供的信息选择引用。

这里有三种"编号"，不用一次记住全部：消息 ID 用来定位消息，被动关联字段用来回复原消息，引用索引用来显示引用卡片。保留原事件或发送回执，框架会帮你取对字段。

| 引用对象            | 索引来源                                      |
| ------------------- | --------------------------------------------- |
| `QQMessageReceived` | 原始 `message_scene.ext` 中的 `msg_idx=...`。 |
| `QQMessageReceipt`  | 原始发送响应 `ext_info.ref_idx`。             |

引用对象必须和发送目标在同一会话，并且带非空索引。跨会话或缺少索引时，提交会抛出 `ValueError`。

发送成功后返回的 `QQMessageReceipt` 就是发送回执，从 `botqraft.api.types` 导入。它提供 `scene`、`conversation`、`raw_response` 和 `receipt_data`。`receipt_data` 包含 `id`、`timestamp` 以及可选的 `ext_info`。平台没给引用索引时，发送回执仍然可以用来读发送结果和消息 ID。

## 撤回消息

优先传入原始消息或发送回执：

```python
from botqraft.api.event import QQMessageReceived
from botqraft.api.types import QQPluginServerInterface

def remove_received_message(server: QQPluginServerInterface, event: QQMessageReceived):
    return server.delete_message(event, return_future=True)
```

两种撤回方式：

| 接口                                                             | 用法                                                                                            |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `server.delete_message(received_or_receipt, return_future=True)` | 撤回 `QQMessageReceived` 或 `QQMessageReceipt` 指定的消息。会话地址和消息 ID 都从原始数据读取。 |
| `server.delete_message_with_id(target, id, return_future=True)`  | 传入明确的 `Group` / `C2C` 目标和官方消息 ID，撤回该会话中的消息。                              |

`delete_message_with_id` 的 `id` 用官方消息 ID。引用索引只用于引用展示。能不能真的撤回、谁有权撤回，由平台决定，撤回收到的消息也一样。

撤回默认返回 `None`，表示已经提交。传入 `return_future=True` 后返回 `concurrent.futures.Future`，确认撤回成功时结果为 `None`。

## 处理发送结果

发送、回复和撤回的参数、目标和连接状态在提交时检查，错误会立刻抛出。HTTP 和平台错误通过 Future 报告。先调用 `server.is_ready()` 查询连接状态，同时处理检查之后状态变化导致的提交失败。

用 `return_future=True` 留下 Future，再读取 `NetworkError` 的结构化字段。遇到 `ResultUnknownError` 时，先核实平台结果，再决定下一步。完整处理方式见[响应回复](reply.md#处理提交与网络错误)。

`GROUP_ADD_ROBOT` 和 `GROUP_MSG_RECEIVE` 的被动回复见[关系事件回复](reply.md#回复关系事件)。交互确认见[交互事件](interactions.md)。

接下来，看[API 索引](api.md)里还有哪些公开接口可用。
