# 主动发送、引用与撤回

> **场景**：我的插件每天早上 8 点要往群里发一条提醒。这时候没人给机器人发消息，没法“回复”，该怎么发？发错了还想撤回。

读完这一页，你能主动向群聊或 C2C 私聊发消息，给消息加上引用，并撤回已经发出的消息。

主动发送和被动回复是两条不同的路。被动回复跟在收到的消息后面，用它的消息 ID 回复。主动发送则由你指定一个目标，随时都能发起。

## 主动发送

主动发送只有一个接口：

```python
server.send(target, message, refer_msg=None, return_future=False)
```

`refer_msg` 和 `return_future` 只能按关键字传入。

`target` 决定消息发到哪个会话。它只能是下面两种之一，都从 `botqraft.api.types` 导入：

| 目标                  | 发到哪里              |
| --------------------- | --------------------- |
| `Group(group_openid)` | 指定的群聊。          |
| `C2C(user_openid)`    | 指定用户的 C2C 私聊。 |

C2C 就是机器人和用户之间的一对一私聊。目标里的 OpenID 必须来自平台推送的数据，不能自己编。

最常见的情况是发回命令所在的会话。这时用 `source.target` 就行，它会根据收到的消息直接给出对应的 `Group` 或 `C2C`，不用你自己判断场景：

```python
from botqraft.api.command import QQCommandSource
from botqraft.api.types import QQPluginServerInterface

def notify_later(server: QQPluginServerInterface, source: QQCommandSource):
    return server.send(source.target, 'Task completed', return_future=True)
```

目标里只有会话地址，所以你可以先把它存起来，等后台任务完成后再发。想拿到平台的确认结果，就用返回的 Future，见[确认发送结果](reply.md#确认发送结果)。主动消息要受 QQ 账号和平台规则的约束，所以请把发送失败当作一种正常结果来处理。

`message` 支持 `str`、`QText`、`QMarkdown`、延迟翻译文本，以及[图片、视频和文件](media.md)。富文本与翻译分别见 [Markdown 消息与文本交互](markdown.md)和[多语言与用户偏好](translation.md)。

## 目标、用户与 AT 是三件事

`send` 不接受 `User`。用户对象回答"是谁"，发送目标回答"发到哪里"，两者分开写，读代码时就不用猜消息会进群还是进私聊：

- 发到群：使用 `Group`，或在群消息的命令里用 `source.target`。
- 发到私聊：使用 `C2C`，或在 C2C 消息的命令里用 `source.target`。群消息里的用户不带私聊地址，没法拿它发起私聊。
- 在群里 AT 某人：AT 是消息内容的一部分，用 `QTextAt` 拼进消息里，见[提及用户](markdown.md#提及用户)。`QTextAt(source.user)` 读的是 `member_openid`，而只有群消息里的用户才带这个字段，所以下面的例子只适用于群消息里的命令。

```python
from botqraft.api.command import QQCommandSource
from botqraft.api.types import QQPluginServerInterface
from botqraft.api.qtext import QMarkdown, QTextAt

def remind_member(server: QQPluginServerInterface, source: QQCommandSource):
    # QQ only renders the mention as @ in Markdown messages for now.
    message = QMarkdown().append(QTextAt(source.user), ' Task completed')
    return server.send(source.target, message, return_future=True)
```

`User.id` 用于真实身份、权限和偏好，见[区分用户身份和会话地址](message-format.md#区分用户身份和会话地址)。

要发给多个会话时，把所有目标列出来，逐个调用 `send`，再分别处理每个 Future 的结果。

## 引用消息

想在消息里展示引用，要显式传入 `refer_msg`。它和能不能被动回复是两回事。给 `send`、`reply` 或 `reply_event` 传入同一会话的 `QQMessageReceived` 或 `QQMessageReceipt`，消息就会带上引用：

```python
from botqraft.api.command import QQCommandSource

def reply_with_quote(source: QQCommandSource):
    return source.reply(
        'Quoted reply',
        refer_msg=True,
        return_future=True,
    )
```

本例要求原消息带有可用的引用索引。默认的回复只关联被动上下文，只有传入了 `refer_msg`，框架才会提交用于展示引用的字段。

回复触发命令的那条原消息时，`source.reply(..., refer_msg=True)` 等同于传入 `source.message_received`，`server.reply(source, ..., refer_msg=True)` 也支持同样的简写。传 `False` 或不传这个参数时，不展示引用。

想引用另一条消息，照常传入消息事件或发送回执即可。这个布尔简写只用于 `reply`，其他发送接口仍然要明确指定引用对象。原消息缺少引用索引时，仍会抛出 `ValueError`，请根据平台实际提供的信息选择引用。

这里有三种"编号"，不用一次全记住：消息 ID 用来定位消息，被动关联字段用来回复原消息，引用索引用来显示引用卡片。只要保留好原事件或发送回执，框架就会帮你取对字段。

| 引用对象            | 索引来源                                      |
| ------------------- | --------------------------------------------- |
| `QQMessageReceived` | 原始 `message_scene.ext` 中的 `msg_idx=...`。 |
| `QQMessageReceipt`  | 原始发送响应 `ext_info.ref_idx`。             |

引用对象必须和发送目标在同一个会话里，并且带有非空的索引。跨会话引用或缺少索引时，提交会抛出 `ValueError`。

发送成功后返回的 `QQMessageReceipt` 就是发送回执，从 `botqraft.api.types` 导入。它提供 `scene`、`conversation`、`raw_response` 和 `receipt_data`。`receipt_data` 包含 `id`、`timestamp` 以及可选的 `ext_info`。即使平台没给引用索引，发送回执也仍然可以用来读取发送结果和消息 ID。

## 撤回消息

撤回消息时，优先传入原始消息或发送回执：

```python
from botqraft.api.event import QQMessageReceived
from botqraft.api.types import QQPluginServerInterface

def remove_received_message(server: QQPluginServerInterface, event: QQMessageReceived):
    return server.delete_message(event, return_future=True)
```

撤回有两种方式：

| 接口                                                             | 用法                                                                                            |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `server.delete_message(received_or_receipt, return_future=True)` | 撤回 `QQMessageReceived` 或 `QQMessageReceipt` 指定的消息。会话地址和消息 ID 都从原始数据读取。 |
| `server.delete_message_with_id(target, id, return_future=True)`  | 传入明确的 `Group` / `C2C` 目标和官方消息 ID，撤回该会话中的消息。                              |

`delete_message_with_id` 的 `id` 要传官方消息 ID，引用索引只用于展示引用。消息能不能真的撤回、谁有权撤回，都由平台决定，撤回收到的消息也一样。

撤回默认返回 `None`，表示请求已经提交。传入 `return_future=True` 后，返回的是 `concurrent.futures.Future`，确认撤回成功时，它的结果是 `None`。

## 处理发送结果

发送、回复和撤回的参数、目标和连接状态，在提交时就会检查，有问题会立刻抛出错误。HTTP 和平台错误则通过 Future 报告。

发送前可以先调用 `server.is_ready()` 查询连接状态。检查之后状态仍可能变化，所以提交失败的情况也要处理。

想知道失败的细节，就用 `return_future=True` 留下 Future，再读取 `NetworkError` 的结构化字段。遇到 `ResultUnknownError` 时，先核实平台上的结果，再决定下一步。完整的处理方式见[回复消息](reply.md#处理提交与网络错误)。

要被动回复 `GROUP_ADD_ROBOT` 和 `GROUP_MSG_RECEIVE` 事件，见[关系事件回复](reply.md#回复关系事件)；要确认按钮点击，见[响应按钮点击](interactions.md#响应按钮点击)。

接下来，读一读[发送图片、视频和文件](media.md)，让消息里不只有文字。
