# 响应事件与回复消息

读完这一页，你会知道收到消息后怎么回一条，怎么在有效期内回复，以及发送失败时怎么处理。

在消息回调里调用 `event.get_command_source()`，再用 `source.reply(...)` 回复。命令回调已经拿到 `QQCommandSource`，可以直接用。

## 回复一条消息

把下面的回调加到已加载插件的入口模块。然后在群聊或 C2C 发送 `/ping`：

```python
from botcraft.api.event import QQMessageReceived
from botcraft.api.types import QQPluginServerInterface

def on_message(server: QQPluginServerInterface, event: QQMessageReceived):
    if event.message_data.content == '/ping':
        source = event.get_command_source()
        source.reply('Pong')
```

群消息正文已经过[前缀处理](message-format.md#提及与前缀处理)。本例只处理 `/ping`。如果你同时为 `/ping` 注册了命令，就按职责选一条回复路径，保证一次响应只回一条。

`source.reply(message)` 和 `server.reply(source, message)` 都使用原始消息 ID 和原会话，属于**被动回复**。被动回复的意思是：平台允许你在收到消息后一段时间内回复这条消息。

`message` 支持 `str`、`QText`、`QMarkdown` 和延迟翻译文本。回复会按来源当前偏好的语言解析翻译。

## 使用原始来源

`QQCommandSource` 从 `botcraft.api.command` 导入。常用字段如下：

| 字段或方法        | 用途                                 |
| ----------------- | ------------------------------------ |
| `user`            | 原始收到的消息里的真实用户。         |
| `scene`           | `group` 或 `c2c`。                   |
| `conversation`    | 原会话 OpenID。                      |
| `msg_id`          | 原始消息 ID。                        |
| `message_data`    | 和收到的消息共用的正文模型。         |
| `origin_received` | 原始 `QQMessageReceived` 事件。      |
| `get_server()`    | 返回所属实例的 `QQServerInterface`。 |

插件的 `on_load` 收到绑定插件的 `QQPluginServerInterface`。`server.reply` 只接收本实例真实消息产生的来源。

会话地址和被动回复资格都以原始收到的数据为准。编辑正文模型只影响正文副本。创建来源需要真实身份、原始消息 ID 和有效会话地址，缺一个就会被拒绝。身份与 OpenID 的用途见[事件消息格式](message-format.md#区分用户身份和会话地址)。

## 在有效期内回复

被动上下文大约有 600 秒有效期，同时还受原始平台时间和账号发送规则限制。收到消息后请及时回复，并把原始来源留给相关操作用。

过期或上下文已失效时，提交会抛出 `PassiveReplyExpiredError`，从 `botcraft.api.exception` 导入。需要长期发送时，改用真实目标和平台允许的[主动发送接口](sending.md#主动发送)。

默认回复只提供被动关联。需要展示引用时，显式传入 `refer_msg`。引用索引和同会话的要求见[引用消息](sending.md#引用消息)。

## 回复关系事件

群关系事件使用 `server.reply_event(event, message)`。它只接受真实的 `GROUP_ADD_ROBOT` 或 `GROUP_MSG_RECEIVE` 事件，并使用原始事件 ID 和群会话做事件关联的被动发送：

```python
from botcraft.api.decorator import qq_event_listener
from botcraft.api.event import QQEvent
from botcraft.api.types import QQPluginServerInterface

@qq_event_listener('GROUP_ADD_ROBOT')
def greet_new_group(server: QQPluginServerInterface, event: QQEvent):
    server.reply_event(event, 'Hello!')
```

事件需要有有效的原始事件 ID、群 OpenID、平台时间和已登记的被动上下文。有效期和平台限制同样适用。其他事件类型请用各自的处理接口。

调用 `server.reply_event(event, message, return_future=True)` 可以拿到发送回执。发送回执就是发送成功后返回的结果对象。需要引用展示时，可以传入同会话、带有效索引的 `refer_msg`，规则见[引用消息](sending.md#引用消息)。

## 等待平台结果

发送、回复和撤回默认返回 `None`，表示操作已经提交。传入 `return_future=True` 后，接口返回 `concurrent.futures.Future`。发送或回复成功时，结果是 `QQMessageReceipt`。

异步协程用 `asyncio.wrap_future` 等待这个普通 Future：

```python
import asyncio

from botcraft.api.command import QQCommandSource
from botcraft.api.exception import NetworkError

async def reply_result(source: QQCommandSource):
    try:
        future = source.reply('Accepted', return_future=True)
        receipt = await asyncio.wrap_future(future)
    except NetworkError as error:
        return {'status': error.category.value, 'message_id': None}
    return {'status': 'confirmed', 'message_id': receipt.receipt_data.id}
```

从异步回调或已调度的协程里调用这个函数，就能拿到已确认的消息 ID 或失败类别。网络失败的日志由框架统一记录。任务调度方法见[任务](tasks.md)。

同步代码可以用 `future.result()` 等待结果。Future 的完成回调适合处理简短结果。耗时工作请保留需要的数据，再用 `server.schedule_task(...)` 调度。回调需要的命令上下文也要显式传进去。

发送回执提供 `receipt_data`、`raw_response`、`scene` 和 `conversation`。保留回执，就能继续做同会话的引用或撤回，见[发送消息](sending.md)。撤回成功的 Future 结果是 `None`。

## 处理提交与网络错误

来源、类型、会话地址和连接状态都在提交时验证，所以错误可能立刻抛出。HTTP 错误和平台错误通过 Future 报告。

- 类型不对时，处理 `TypeError`。
- 缺少身份、消息 ID、会话地址或引用索引等参数错误时，处理 `ValueError`。
- 被动上下文过期时，处理 `PassiveReplyExpiredError`。
- 连接还没 READY 或已经变化时，处理 `NotReadyError`。
- HTTP 和平台失败时，读取 `NetworkError` 的 `category`、`http_code`、`err_code`、`code` 和 `trace_id`。异常文字用于阅读和诊断。

相关框架异常都从 `botcraft.api.exception` 导入。发送前用 `server.is_ready()` 查询状态，同时也要处理检查之后状态变化造成的提交失败。

`ResultUnknownError` 表示平台可能已经执行了操作。再次提交前先核实结果，避免重复回复或重复撤回。

接下来，读[命令系统](commands.md)，把消息变成用户能敲的命令。
