# 主动发送、引用与撤回

读完这一页，你能用真实用户或群发消息，给消息加上引用，并撤回已经发出的消息。

主动发送和被动回复是两条不同的路。被动回复跟在收到的消息后面，用它的消息 ID 回复。主动发送由你指定一个目标，随时发起。

## 主动发送

主动发送使用真实的 `User` 或 `Group` 目标。目标里的 OpenID 必须来自平台推送的数据，不能自己编。下面这个函数向指定群主动发送：

```python
from botqraft.api.types import Group, QQPluginServerInterface

def notify_group(server: QQPluginServerInterface, actual_group_openid: str):
    target = Group(group_openid=actual_group_openid)
    return server.say(target, 'Task completed', return_future=True)
```

从插件事件或后台任务里调用它，并传入实际的群 OpenID。想拿到平台的确认结果，就用返回的 Future，见[等待平台结果](reply.md#等待平台结果)。主动消息受 QQ 账号和平台规则约束。实际使用时，优先从真实事件或任务里取得目标，并把发送失败当作正常结果来处理。

三种发送方式：

| 接口                                                    | 目标与行为                                                                    |
| ------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `server.say(target, message, return_future=True)`       | 向指定 `User` 或 `Group` 主动发送。                                           |
| `server.tell(user, message, return_future=True)`        | 向 `User` 所在会话主动发送；群聊中附带对该用户的 AT。                         |
| `server.broadcast(target, message, return_future=True)` | 向指定 `User` 或 `Group` 主动发送，并记录提交日志。目标范围由调用者明确提供。 |

每次调用 `broadcast` 只使用传入的一个目标。要发给多个会话时，你列出所有目标，逐个调用。

`message` 支持 `str`、`QText`、`QMarkdown` 和延迟翻译文本。富文本与翻译分别见 [Markdown、文本交互与键盘](markdown.md)和[翻译与用户语言](translation.md)。

## 选择目标与会话地址

目标类型从 `botqraft.api.types` 导入。这三个字段名字很像，但各自负责不同位置：`user_openid` 找 C2C 会话，`group_openid` 找群，`member_openid` 找群里的某位成员。先确定你要发给谁，再选对应字段。

- 群目标使用 `Group(group_openid=actual_group_openid)`。
- C2C 用户目标使用平台提供的 `User`，会话地址取 `user_openid`，场景为 `c2c`。只提供有效的 `user_openid` 时，`User` 也能识别 C2C 会话。
- 群用户目标的场景为 `group`，会话地址取 `group_openid`。`tell` 另外使用 `member_openid`，用来在群里 AT 该用户。

`User.id` 用于真实身份、权限和偏好。按用途分别传入 `user_openid`、`group_openid` 和 `member_openid`，见[区分用户身份和会话地址](message-format.md#区分用户身份和会话地址)。收到的 `source.user` 可以提供真实的用户目标，但 `say`、`tell`、`broadcast` 仍然走主动发送规则。

群内 `tell` 需要有效的 `member_openid`，消息内容使用 `QText` 或 `QMarkdown`。普通字符串按 `QText` 处理。提交时会检查 AT 字段与内容类型。

这些发送接口只在群聊和 C2C 中可用，请提供对应的真实目标。

## 引用消息

引用展示用显式的 `refer_msg`，它和被动回复的资格是两回事。给 `say`、`tell`、`broadcast`、`reply` 或 `reply_event` 传入同会话的 `QQMessageReceived` 或 `QQMessageReceipt`，就能带上引用：

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
| `server.delete_message_with_id(target, id, return_future=True)`  | 传入明确的 `User` / `Group` 目标和官方消息 ID，撤回该会话中的消息。                             |

`delete_message_with_id` 的 `id` 用官方消息 ID。引用索引只用于引用展示。能不能真的撤回、谁有权撤回，由平台决定，撤回收到的消息也一样。

撤回默认返回 `None`，表示已经提交。传入 `return_future=True` 后返回 `concurrent.futures.Future`，确认撤回成功时结果为 `None`。

## 处理发送结果

发送、回复和撤回的参数、目标和连接状态在提交时检查，错误会立刻抛出。HTTP 和平台错误通过 Future 报告。先调用 `server.is_ready()` 查询连接状态，同时处理检查之后状态变化导致的提交失败。

用 `return_future=True` 留下 Future，再读取 `NetworkError` 的结构化字段。遇到 `ResultUnknownError` 时，先核实平台结果，再决定下一步。完整处理方式见[响应回复](reply.md#处理提交与网络错误)。

`GROUP_ADD_ROBOT` 和 `GROUP_MSG_RECEIVE` 的被动回复见[关系事件回复](reply.md#回复关系事件)。交互确认见[交互事件](interactions.md)。

接下来，看[API 索引](api.md)里还有哪些公开接口可用。
