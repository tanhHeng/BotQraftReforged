# 监听消息与事件

> **场景**：我想让用户在群里直接发“今日人品”（不带 `/`）也能触发插件，或者把每条群消息都记进日志。该怎么接收这些消息？

读完这一页，你能不经过命令，直接接住群聊、私聊消息和按钮交互。比如用户发“今日人品”这种没有 `/` 的文字时，也能让插件做出反应。

在插件入口模块中定义事件回调。框架会自动发现回调，并传入绑定当前插件的 `QQPluginServerInterface`。

先选择需要的事件入口，再按[读取消息内容](message-format.md)读取事件内容。收到消息后，按[回复消息](reply.md)获取来源并回复。

## 注册自动回调

`on_load`、`on_unload`、`on_botqraft_start` 和 `on_botqraft_stop` 的触发时机与职责见[插件是怎么运行的](basic.md#插件的生命周期)。

消息与交互回调同样由框架自动发现：

| 回调                              | 时机与参数                                                                                        |
| --------------------------------- | ------------------------------------------------------------------------------------------------- |
| `on_qq_event(server, event)`      | 接收通用 `QQEvent` 平台事件。                                                                     |
| `on_message(server, event)`       | 接收解析成功的 `QQMessageReceived` 群聊和 C2C 消息。                                              |
| `on_group_message(server, event)` | 接收两种群消息投递：`GROUP_AT_MESSAGE_CREATE` 和 `GROUP_MESSAGE_CREATE`。                         |
| `on_c2c_message(server, event)`   | 接收解析成功的 C2C 消息。                                                                         |
| `on_interaction(server, event)`   | 接收解析成功的 `QQInteraction` 交互事件，处理方法见[响应按钮点击](interactions.md#响应按钮点击)。 |

大多数时候，你只需要知道 `on_message` 或 `on_group_message` 就够了。这两个回调会在消息成功解析后触发，你可以在里面读取消息正文、用户身份，并回复。

例如，在入口模块中记录群消息：

```python
from botqraft.api.event import QQMessageReceived
from botqraft.api.types import QQPluginServerInterface

def on_group_message(server: QQPluginServerInterface, event: QQMessageReceived):
    server.logger.info('Received group message: %s', event.message_data.content)
```

发送前用 `server.is_ready()` 检查连接状态，并处理检查后状态变化造成的提交失败。

## 显式注册监听

在 `on_load` 中调用 `server.register_event_listener(event, callback)`。回调仍接收 `(server, event)`：

```python
from botqraft.api.event import QQMessageReceived
from botqraft.api.types import QQPluginServerInterface

def handle_private_message(server: QQPluginServerInterface, event: QQMessageReceived):
    server.logger.info('Received C2C message: %s', event.message_data.content)

def on_load(server: QQPluginServerInterface, prev_module):
    server.register_event_listener('C2C_MESSAGE_CREATE', handle_private_message)
```

事件 ID 按大小写等价匹配。`'C2C_MESSAGE_CREATE'` 与 `'c2c_message_create'` 指向同一事件。可通过 `priority` 参数指定监听优先级，默认值为 `1000`。

一个处理逻辑选择一种登记方式就够了：要么使用自动回调，要么在 `on_load` 里显式注册。这样每条回复、写入或其他动作都有清楚的唯一入口。

## 精确监听官方事件

只处理平台 AT 投递时，使用官方事件名：

```python
from botqraft.api.decorator import qq_event_listener
from botqraft.api.event import QQEvent
from botqraft.api.types import QQPluginServerInterface

@qq_event_listener('GROUP_AT_MESSAGE_CREATE')
def handle_at_delivery(server: QQPluginServerInterface, event: QQEvent):
    server.logger.info('Received platform AT delivery')
```

也可以定义自动回调 `on_group_at_message_create_event(server, event)`，或在 `on_load` 中显式登记 `'GROUP_AT_MESSAGE_CREATE'`。

事件类型描述平台的投递方式。`GROUP_MESSAGE_CREATE` 也可能包含机器人提及。检查正文中的 AT 时，按[提及与前缀处理](message-format.md#提及与前缀处理)读取字段和标签。

旧插件的 `on_group_at_message` 迁移为 `on_group_message`，或改用官方事件的精确订阅。自动发现只登记当前回调名称。

## 进阶：调用顺序与本地事件

刚开始写插件时可以跳过这一节。等你同时用了命令和消息回调，或者需要插件内部的自定义事件时，再回来看。

### 消息回调的调用顺序

把它想成一条固定流水线：先处理命令，再进入 `on_qq_event`，然后是 `on_message`，接着是 `on_group_message`，最后才到官方事件的精确监听。每一步都共享同一个事件对象，但异步任务的完成时间仍可能不同。

`on_group_message` 对应框架事件 `botqraft.group_message`。两个官方群事件 ID 各自保留。

C2C 消息不走这条链路，它使用自己的专用回调 `on_c2c_message`。各入口共享同一个事件对象，异步处理的完成顺序由各自的运行时间决定。

统一回调与精确监听同时登记时，两者都会被调用。命令与消息回调也会同时收到符合条件的消息。按职责划分处理范围，让每项回复、写入或其他副作用只执行一次。

消息解析失败时，全局 `on_qq_event` 和官方精确监听仍接收通用 `QQEvent`。精确监听包括显式登记、装饰器和 `on_<官方事件名小写>_event` 自动发现入口。在这些入口中先确认事件类型，再读取已解析的对象。`on_message`、`on_group_message`、`on_c2c_message` 和 `on_interaction` 只接收解析成功的事件。通过 `model_parse_failed` 和 `parse_error` 查看失败信息。

### 使用本地事件

`botqraft.api.event` 导出 `Event`、`PluginEvents`、原生 `PluginEvent` / `LiteralEvent`，以及 QQ 入站类型 `QQEvent`、`QQInteraction`、`QQMessageReceived`。

平台监听通常直接使用官方事件名字符串。本地自定义事件使用 `LiteralEvent('my_plugin.event')`，由本地事件系统处理。`on_qq_event` 负责平台推送。

接下来，按[读取消息内容](message-format.md)读取正文、用户身份和会话信息。
