# 交互事件与按钮响应

读完这一页，你能接住用户在 QQ 里点按钮的操作，并告诉平台这次交互处理完了。

用户在 QQ 点了按钮，平台会推送一条交互事件。框架把它解析成 `QQInteraction`，交给你的 `on_interaction(server, event)`。你要做的是：确认这是自己按钮的点击，然后回一个响应码，告诉平台处理结果。

回调怎么登记见[插件事件](events.md)。交互响应用独立接口。普通消息回复用[响应回复](reply.md)。

## 响应自己的交互

给插件的按钮分配稳定的 `button_id`。在回调里筛出这个 ID，再提交响应。下面示例接收 ID 为 `example_confirm` 的按钮，用响应码 `0` 确认成功：

```python
from botqraft.api.event import QQInteraction
from botqraft.api.types import QQPluginServerInterface

def on_interaction(server: QQPluginServerInterface, event: QQInteraction):
    data = event.interaction_data.data
    resolved = data.resolved if data is not None else None
    if resolved is not None and resolved.button_id == 'example_confirm':
        server.respond_interaction(event, 0)
```

按钮怎么发出去见 [Markdown、文本交互与键盘](markdown.md)。给每类交互划好处理范围，保证同一个交互只由一个地方提交响应。

`respond_interaction` 接收真实的 `QQInteraction`。响应码用整数 `0`–`5`，也可以传值为该范围整数的枚举。布尔值、其他类型和范围外的值都会被拒绝。

这个接口直接返回 `concurrent.futures.Future`，成功结果为 `None`。调用形式是 `server.respond_interaction(event, code)`，Future 的用法见[等待平台结果](reply.md#等待平台结果)。

## 读取交互数据

`QQInteraction` 继承 `QQEvent`，保留 `event_type`、`event_id`、`raw_payload`、`data` 等字段。`raw_payload` 是平台推送的原始 JSON，`data` 是其中的原始事件数据。详见[读取事件的原始数据](message-format.md#读取事件的原始数据)。

交互专用字段如下：

| 字段               | 用途                                |
| ------------------ | ----------------------------------- |
| `interaction_id`   | 原始事件数据 `d.id` 中的交互 ID。   |
| `interaction_data` | 解析后的 `QQInteractionData` 对象。 |

`event_id` 是事件 ID，`interaction_id` 是交互 ID，两者不同。把收到的事件传进去，框架会从原始交互数据确定要响应哪次交互。

`interaction_data` 包含 `id`、`type`、`scene`、`chat_type`、`timestamp`、`version`、`application_id`，以及平台提供的 `guild_id`、`channel_id`、`user_openid`、`group_openid` 和 `group_member_openid`。

具体交互内容在 `interaction_data.data`：

- `type` 表示交互种类。
- `resolved` 提供 `button_id`、`button_data`、`user_id`、`feature_id` 和 `message_id` 等已解析字段。
- 反馈、选择和动作数据位于 `feedback_opt`、`checked`、`action`。
- 来源扩展位于 `message_scene`，授权场景与范围位于 `authorize_data`。

这些字段可能缺失或为 `None`，按当前交互实际带来的字段处理。`QQInteractionData`、`InteractionData`、`InteractionResolved` 和相应枚举从 `botqraft.api.types` 导入。

`on_interaction` 只接收解析成功的交互。想看解析失败的原始数据，在 `on_qq_event` 或官方 `INTERACTION_CREATE` 精确监听里检查 `model_parse_failed` 和 `parse_error`。

## 一次交互只响应一次

同一个交互 ID，在提交中、提交成功后，或结果未知时，都只保留一次响应。重复提交会立刻抛出 `ValueError`。

类型、交互 ID、响应码和连接状态在提交时检查。HTTP 和平台错误通过 Future 报告，用 `NetworkError` 的结构化字段判断结果。

确定失败后，框架会释放该交互的提交记录，你可以按失败原因决定要不要重试。`ResultUnknownError` 表示平台可能已经接受了响应，框架会保留提交记录。先核实结果，别重复操作。

发送前调用 `server.is_ready()` 查询连接状态，同时处理状态变化导致的提交失败。异常类型和 Future 处理见[响应回复](reply.md#处理提交与网络错误)。

接下来，用[键盘](markdown.md)把按钮放进消息里。
