# 监听消息与事件

> **场景**：我想让用户在群里直接发“今日人品”（不带 `/`）也能触发插件，或者把每条群消息都记进日志。该怎么接收这些消息？

读完这一页，你能不经过命令，直接接住群聊、私聊消息和按钮交互。比如用户发“今日人品”这种没有 `/` 的文字时，也能让插件做出反应。

在插件的入口模块里定义事件回调就行。框架会自动找到这些回调，调用时传入绑定当前插件的 `QQPluginServerInterface`。

先在这一页选好要用的事件入口，再看[读取消息内容](message-format.md)，取出事件里的内容。想回复收到的消息，就按[回复消息](reply.md)拿到来源再回复。

## 注册自动回调

`on_load`、`on_unload`、`on_botqraft_start` 和 `on_botqraft_stop` 什么时候触发、各自该做什么，见[插件是怎么运行的](basic.md#插件的生命周期)。

消息和交互回调也一样，框架会自动发现它们：

| 回调                              | 时机与参数                                                                                        |
| --------------------------------- | ------------------------------------------------------------------------------------------------- |
| `on_qq_event(server, event)`      | 接收所有 QQ 平台事件：`QQEvent` 及其子类，包括解析失败的通用 `QQEvent`。                          |
| `on_message(server, event)`       | 接收解析成功的 `QQMessageReceived` 群聊和 C2C 消息。                                              |
| `on_group_message(server, event)` | 接收解析成功的两种群消息投递：`GROUP_AT_MESSAGE_CREATE` 和 `GROUP_MESSAGE_CREATE`。               |
| `on_c2c_message(server, event)`   | 接收解析成功的 C2C 消息（`C2C_MESSAGE_CREATE`）。                                                 |
| `on_interaction(server, event)`   | 接收解析成功的 `QQInteraction` 交互事件，处理方法见[响应按钮点击](interactions.md#响应按钮点击)。 |

大多数时候，你只需要知道 `on_message` 或 `on_group_message` 就够了。这两个回调会在消息成功解析后触发，你可以在里面读取消息正文、用户身份，并回复。

例如，在入口模块中记录群消息：

```python
from botqraft.api.event import QQMessageReceived
from botqraft.api.types import QQPluginServerInterface

def on_group_message(server: QQPluginServerInterface, event: QQMessageReceived):
    server.logger.info('Received group message: %s', event.message_data.content)
```

如果要在回调里发消息，先用 `server.is_ready()` 检查连接状态。检查之后状态仍可能变化，所以提交失败的情况也要处理。

## 显式注册监听

在 `on_load` 里调用 `server.register_event_listener(event, callback)`，就能显式登记监听。回调的参数仍然是 `(server, event)`：

```python
from botqraft.api.event import QQMessageReceived
from botqraft.api.types import QQPluginServerInterface

def handle_private_message(server: QQPluginServerInterface, event: QQMessageReceived):
    server.logger.info('Received C2C message: %s', event.message_data.content)

def on_load(server: QQPluginServerInterface, prev_module):
    server.register_event_listener('C2C_MESSAGE_CREATE', handle_private_message)
```

事件 ID 不区分大小写，`'C2C_MESSAGE_CREATE'` 和 `'c2c_message_create'` 指的是同一个事件。

`priority` 参数用来指定监听的优先级，默认是 `1000`。同一个事件有多个监听时，按这个数值从小到大依次调用。

同一段处理逻辑，选一种登记方式就够了：要么用自动回调，要么在 `on_load` 里显式注册。这样每条回复、每次写入或其他动作，都只有一个清楚的入口。

## 精确监听官方事件

如果你只想处理平台的 AT 投递，就直接监听官方事件名：

```python
from botqraft.api.decorator import qq_event_listener
from botqraft.api.event import QQEvent
from botqraft.api.types import QQPluginServerInterface

@qq_event_listener('GROUP_AT_MESSAGE_CREATE')
def handle_at_delivery(server: QQPluginServerInterface, event: QQEvent):
    server.logger.info('Received platform AT delivery')
```

除了装饰器，你也可以定义自动回调 `on_group_at_message_create_event(server, event)`，或者在 `on_load` 里显式登记 `'GROUP_AT_MESSAGE_CREATE'`。

注意，事件类型只说明平台是怎么投递这条消息的。`GROUP_MESSAGE_CREATE` 里也可能有对机器人的提及。想检查正文里有没有 AT，请按[提及与前缀处理](message-format.md#提及与前缀处理)读取相应的字段和标签。

如果你的旧插件用了 `on_group_at_message`，请改成 `on_group_message`，或者改用官方事件的精确订阅。自动发现只认当前的回调名称。

## 进阶：调用顺序与本地事件

刚开始写插件时可以跳过这一节。等你同时用了命令和消息回调，或者需要插件内部的自定义事件时，再回来看。

### 消息回调的调用顺序

你可以把它想成一条固定的流水线：先同步执行匹配的命令，再进入 `on_qq_event`，然后是 `on_message`，接着是 `on_group_message`，最后才轮到官方事件的精确监听。

每个回调都是一个单独的任务，按这个顺序排队，共享同一个事件对象。不过，异步回调各自完成的时间仍可能不同。

`on_group_message` 对应框架事件 `botqraft.group_message`，两个官方群事件 ID 仍然各自保留。

C2C 消息没有 `on_group_message` 这一步：命令之后依次是 `on_qq_event`、`on_message`，最后是官方事件 `c2c_message_create` 的监听。`on_c2c_message` 就登记在这个官方事件上，和该事件的精确监听一起按 `priority` 排序调用。`on_interaction` 也是这样，它登记在 `interaction_create` 上，排在 `on_qq_event` 之后。

如果同时登记了统一回调和精确监听，两者都会被调用。同样，命令和消息回调也会同时收到符合条件的消息。所以请按职责划分好各自的处理范围，让每次回复、写入或其他副作用只发生一次。

消息解析失败时，全局的 `on_qq_event` 和官方事件的精确监听仍会收到一个通用的 `QQEvent`。这里的精确监听包括三种入口：显式登记、装饰器，以及自动发现的 `on_<官方事件名小写>_event`。所以在这些入口里，请先确认事件类型，再读取已解析的对象。

`on_message`、`on_group_message`、`on_c2c_message` 和 `on_interaction` 只接收解析成功的事件。想查看失败信息，读 `model_parse_failed` 和 `parse_error`。

### 使用本地事件

`botqraft.api.event` 导出 `Event`、`PluginEvents`、原生 `PluginEvent` / `LiteralEvent` / `EventListener`，以及 QQ 入站类型 `QQEvent`、`QQInteraction`、`QQMessageReceived`。

平台事件的监听，通常直接用官方事件名字符串就行。

插件内部的本地自定义事件，用 `LiteralEvent('my_plugin.event')` 表示。先用 `server.register_event_listener(...)` 登记监听，再用 `server.dispatch_event(LiteralEvent('my_plugin.event'), (data,))` 派发，监听收到的参数是 `(server, data)`。

以 `botqraft.` 开头、全大写或与内置事件同名的 ID 不能手动派发，否则会抛出 `UnsupportedOperationError`。平台推送交给 `on_qq_event` 接收。

接下来，看看[读取消息内容](message-format.md)，学习怎么读取正文、用户身份和会话信息。
