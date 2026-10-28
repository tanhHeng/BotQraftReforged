# 回复消息

> **场景**：用户发了 `/jrrp`，我想回他一句，顺便引用他发的那条消息；要是回复没发出去，我也想知道是什么原因。该怎么做？

读完这一页，你会知道收到消息后怎么回一条，怎么在有效期内回复，以及发送失败时该怎么处理。

做法很简单：在消息回调里调用 `event.get_command_source()` 拿到来源，再用 `source.reply(...)` 回复。如果是命令回调，它已经拿到了 `QQCommandSource`，直接用就行。

## 回复一条消息

把下面的回调加到一个已加载插件的入口模块里，然后在群聊或 C2C 私聊里发送 `/ping`：

```python
from botqraft.api.event import QQMessageReceived
from botqraft.api.types import QQPluginServerInterface

def on_message(server: QQPluginServerInterface, event: QQMessageReceived):
    if event.message_data.content == '/ping':
        source = event.get_command_source()
        source.reply('Pong')
```

群消息的正文已经做过[前缀处理](message-format.md#提及与前缀处理)。本例只处理 `/ping` 这一种正文。如果你同时还为 `/ping` 注册了命令，请按职责选一条路径负责回复，保证一次只回一条。

`source.reply(...)` 和 `server.reply(source, ...)` 都会带上原消息 ID，发回原来的会话，所以叫"被动回复"。你可以把它理解成：在平台给出的回复窗口里，接着刚才那条消息回话。如果要晚些时候再发，就改用主动发送。

`message` 支持 `str`、`QText`、`QMarkdown`、延迟翻译文本，以及[图片、视频和文件](media.md)。延迟翻译文本会按来源当前偏好的语言翻译后再回复。

## 使用原始来源

`QQCommandSource` 从 `botqraft.api.command` 导入。常用字段如下：

| 字段或方法         | 用途                                     |
| ------------------ | ---------------------------------------- |
| `user`             | 原始收到的消息里的真实用户。             |
| `scene`            | `group` 或 `c2c`。                       |
| `conversation`     | 原会话 OpenID。                          |
| `target`           | 原会话的 `Group` 或 `C2C` 主动发送目标。 |
| `msg_id`           | 原始消息 ID。                            |
| `message_data`     | 和收到的消息共用的正文模型。             |
| `message_received` | 原始 `QQMessageReceived` 事件。          |
| `get_server()`     | 返回所属实例的 `QQServerInterface`。     |

插件的 `on_load` 收到的是绑定当前插件的 `QQPluginServerInterface`。`server.reply` 只接受本实例收到的真实消息所产生的来源。

会话地址和能否被动回复，都以原始收到的数据为准；编辑正文模型只会影响正文副本。创建来源需要真实身份、原始消息 ID 和有效的会话地址，缺一个都会被拒绝。身份和 OpenID 分别用来做什么，见[读取消息内容](message-format.md#区分用户身份和会话地址)。

## 在有效期内回复

框架为每条收到的消息保留最多 600 秒的被动上下文，从本机收到消息时算起。如果消息里的平台时间早于本机收到时间（比如推送有延迟），窗口会相应缩短，相当于从平台时间起算 600 秒。消息缺少可用的平台时间时，不能被动回复；平台时间比本机时间超前 15 秒以上时，提交会抛出 `ValueError`，超前 5 秒以上时框架会在日志里提醒你检查系统时钟。

这只是框架这一侧的窗口，平台另有自己的被动回复时效和次数限制：官方文档写的是群聊 5 分钟、每条消息最多回复 5 次，C2C 60 分钟、每条最多 4 次。群聊的平台时效比框架窗口短，超出时由平台拒绝，错误通过 Future 报告；C2C 消息过了 600 秒，即使平台仍允许，框架也会拒绝。收到消息后请及时回复，并把原始来源留给相关操作用。

超过框架窗口或上下文未登记时，提交会抛出 `PassiveReplyExpiredError`，从 `botqraft.api.exception` 导入。需要长期发送时，改用真实目标和平台允许的[主动发送接口](sending.md#主动发送)。

默认回复只提供被动关联。需要展示引用时，显式传入 `refer_msg`。引用索引和同会话的要求见[引用消息](sending.md#引用消息)。

## 回复关系事件

回复群关系事件，用 `server.reply_event(event, message)`。它只接受真实的 `GROUP_ADD_ROBOT` 或 `GROUP_MSG_RECEIVE` 事件，会用原始事件 ID 和群会话，做一次关联到该事件的被动发送：

```python
from botqraft.api.decorator import qq_event_listener
from botqraft.api.event import QQEvent
from botqraft.api.types import QQPluginServerInterface

@qq_event_listener('GROUP_ADD_ROBOT')
def greet_new_group(server: QQPluginServerInterface, event: QQEvent):
    server.reply_event(event, 'Hello!')
```

这个事件必须带有有效的原始事件 ID、群 OpenID 和平台时间，并且已经登记了被动上下文。前面说的有效期和平台限制在这里同样适用。其他类型的事件，请用各自的处理接口。

想拿到发送回执，就调用 `server.reply_event(event, message, return_future=True)`。发送回执就是发送成功后返回的结果对象。想展示引用时，可以传入同一会话、带有效索引的 `refer_msg`，规则见[引用消息](sending.md#引用消息)。

## 确认发送结果

默认情况下，接口把操作提交出去就返回 `None`。如果你还想等平台确认，就传 `return_future=True`。这时你拿到的是一个 `Future`，它像一张"结果取件单"，完成后凭它取到回执或错误。

在异步协程里，用 `asyncio.wrap_future` 包一层，就能等待这个普通 Future：

```python
import asyncio

from botqraft.api.command import QQCommandSource
from botqraft.api.exception import NetworkError

async def reply_result(source: QQCommandSource):
    try:
        future = source.reply('Accepted', return_future=True)
        receipt = await asyncio.wrap_future(future)
    except NetworkError as error:
        return {'status': error.category.value, 'message_id': None}
    return {'status': 'confirmed', 'message_id': receipt.receipt_data.id}
```

在异步回调或已调度的协程里调用这个函数，就能拿到已确认的消息 ID 或失败类别。网络失败的日志由框架统一记录。怎么调度任务，见[任务](tasks.md)。

同步代码可以用 `future.result()` 等待结果。Future 的完成回调适合做简短的处理。如果有耗时的工作，先把需要的数据留下来，再用 `server.schedule_task(...)` 调度。回调里要用到的命令上下文，也要显式传进去。

发送回执提供 `receipt_data`、`raw_response`、`scene` 和 `conversation`。把回执留着，之后就能在同一会话里引用或撤回这条消息，见[发送消息](sending.md)。撤回成功时，Future 的结果是 `None`。

## 处理提交与网络错误

来源、类型、会话地址和连接状态在提交时就会检查，所以这类错误可能当场抛出。HTTP 错误和平台错误则通过 Future 报告。

- 类型不对时，处理 `TypeError`。
- 缺少身份、消息 ID、会话地址或引用索引等参数错误时，处理 `ValueError`。
- 被动上下文过期时，处理 `PassiveReplyExpiredError`。它是 `ValueError` 的子类，要单独处理时写在 `except ValueError` 前面。
- 连接还没 READY 或已经变化时，处理 `NotReadyError`。
- HTTP 和平台失败时，读取 `NetworkError` 的 `category`、`http_code`、`err_code`、`code` 和 `trace_id`。异常文字用于阅读和排查问题。

相关的框架异常都从 `botqraft.api.exception` 导入。发送前可以先用 `server.is_ready()` 查一下连接状态。但检查之后状态仍可能变化，所以提交失败的情况也要处理。

遇到 `ResultUnknownError` 时要小心：它表示平台可能已经执行了这次操作。重新提交前，请先核实结果，避免重复回复或重复撤回。

接下来，看看[帮助消息与指令面板](help.md)，让你的命令出现在帮助列表里。
