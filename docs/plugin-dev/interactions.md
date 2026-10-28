# 按钮：键盘与点击响应

> **场景**：我想在今日人品的结果下面放“再测一次”和“投稿”两个按钮，用户点了按钮，插件还要能接住这次点击。该怎么做？

读完这一页，你能在消息下面挂一排按钮，并接住用户点击按钮的操作，告诉平台这次交互处理完了。

按钮挂在消息的键盘上。消息和键盘对象从 `botqraft.api.qtext` 导入。先构造消息，再把它传给[回复接口](reply.md)。实际发送需要账号拥有 Markdown 和键盘权限；Markdown 正文的写法见[Markdown 消息与文本交互](markdown.md)。

## 添加自定义键盘

把按钮按行排列，再附加到消息：

```python
from botqraft.api.qtext import (
    QMarkdown, QText, QKeyboardActionCommand, QKeyboardButton,
    QKeyboardCustom, QKeyboardPermission, QKeyboardRenderData,
)

keyboard = QKeyboardCustom([[
    QKeyboardButton(
        id='echo_button',
        render_data=QKeyboardRenderData(label='Echo', style=1),
        action=QKeyboardActionCommand(
            data='/echo Hello',
            permission=QKeyboardPermission(),
            enter=True,
            reply=True,
        ),
    ),
]])
message = QMarkdown('**Echo**: ').append(QText('<hello>')).set_keyboard(keyboard)
payload = message.to_payload()
button = payload['keyboard']['content']['rows'][0]['buttons'][0]
assert button['action']['type'] == 2
assert button['action']['data'] == '/echo Hello'
print('Markdown and keyboard payload verified')
```

上例只在本地构造消息数据。在真实的命令回调里要调用 `source.reply(message)` 提交到 QQ。键盘的命令文本要和[注册命令](commands.md)时的根名称保持一致。

`set_keyboard` 修改消息自身，`set_keyboard(None)` 移除键盘。每条组合消息最多包含一个键盘。

使用平台模板时，改为 `QKeyboardTemplate(actual_template_id)`。模板 ID 使用非空字符串。

## 选择按钮行为

| 对象                      | 行为                                                                                   |
| ------------------------- | -------------------------------------------------------------------------------------- |
| `QKeyboardActionJump`     | 跳转，动作类型为 0。                                                                   |
| `QKeyboardActionCallback` | 回调，动作类型为 1，`data` 必填。点击后推送交互事件，见[响应按钮点击](#响应按钮点击)。 |
| `QKeyboardActionCommand`  | 命令，动作类型为 2，`data` 必填。点击后由用户发出命令文本，走普通命令流程。            |

`enter=True` 让命令按钮点击后自动发送 `data`。该能力按平台说明用于单聊。`reply=True` 让该指令引用回复键盘所在的消息。`anchor` 按平台语义可以覆盖 `enter`。这些效果受客户端版本和场景支持限制。发送接口的引用通过 `refer_msg` 单独设置。

`QKeyboardPermission()` 默认允许所有人。使用 `QKeyboardPermissionType.SPECIFY` 和非空 `specify_user_ids` 列表指定用户。使用 `ADMIN` 限定管理员。`ADMIN`、`ALL` 使用省略的用户列表。切换权限类型时创建新对象。

按钮权限控制平台交互资格。服务器端的执行权限通过命令节点单独检查，参见[权限系统](permissions.md)。

## 设置键盘字段

键盘对象提供可以连着调用的设置方法，例如 `render_data.set_label('Echo').set_style(1)`。使用 `None` 省略可选字段，`False` 和整数 `0` 会保留在消息数据中。

创建、设置方法和编码时都会检查类型与字段约束。设置方法校验成功后才替换字段。类型错误抛出 `TypeError`，非法值、重复按钮 ID 和超长字段抛出 `ValueError`。

- `QKeyboardCustom` 接收按钮行列表，每行也是列表。全部按钮使用 `QKeyboardButton`，非 `None` 的按钮 ID 在整个键盘内保持唯一。
- `QKeyboardRenderData.label` 最多 10 字符。`style` 使用 0、1、3、4。
- `QKeyboardModal.content` 最多 40 字符，内容使用纯文本，含 URL 会被拒绝。`confirm_text`、`cancel_text` 各最多 4 字符。
- 动作与权限类型使用公开枚举或合法整数代码，bool 会被拒绝。动作子类保留自己的固定类型。

最终长度、行列数量和账号能力还需符合 QQ 平台规则。客户端展示与点击效果由平台支持决定。

## 响应按钮点击

用户在 QQ 点了回调按钮，平台会推送一条交互事件。框架把它解析成 `QQInteraction`，交给你的 `on_interaction(server, event)`。你要做的是：确认这是自己按钮的点击，然后回一个响应码，告诉平台处理结果。

回调怎么登记见[监听消息与事件](events.md)。交互响应用独立接口，普通消息回复用[回复消息](reply.md)。

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

给每类交互划好处理范围，保证同一个交互只由一个地方提交响应。

`respond_interaction` 接收真实的 `QQInteraction`。响应码用整数 `0`–`5`，也可以传值为该范围整数的枚举。布尔值、其他类型和范围外的值都会被拒绝。

这个接口直接返回 `concurrent.futures.Future`，成功结果为 `None`。调用形式是 `server.respond_interaction(event, code)`，Future 的用法见[确认发送结果](reply.md#确认发送结果)。

## 读取交互数据

`QQInteraction` 继承 `QQEvent`，保留 `event_type`、`event_id`、`raw_payload`、`data` 等字段。`raw_payload` 是平台推送的原始 JSON，`data` 是其中的原始事件数据 `d`。详见[读取事件的原始数据](message-format.md#读取事件的原始数据)。

交互专用字段在 `QQInteraction` 解析后的两个位置：

| 字段                    | 位置与用途                                                      |
| ----------------------- | --------------------------------------------------------------- |
| `interaction_id`        | `QQInteraction` 顶层字段，取自原始事件数据 `d.id` 中的交互 ID。 |
| `interaction_data`      | `QQInteraction` 顶层字段，解析后的 `QQInteractionData` 对象。   |
| `interaction_data.id`   | 交互 ID（和 `interaction_id` 一致）。                           |
| `interaction_data.data` | 具体交互内容，包含 `resolved`、按钮数据、选择和授权等字段。     |

`event_id` 是事件 ID，`interaction_id` 是交互 ID，两者不同。把收到的事件传进去，框架会从原始交互数据确定要响应哪次交互。

`interaction_data` 顶层包含 `id`、`type`、`scene`、`chat_type`、`timestamp`、`version`、`application_id`，以及平台提供的 `guild_id`、`channel_id`、`user_openid`、`group_openid` 和 `group_member_openid`。

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

发送前调用 `server.is_ready()` 查询连接状态，同时处理状态变化导致的提交失败。异常类型和 Future 处理见[处理提交与网络错误](reply.md#处理提交与网络错误)。

接下来，阅读[多语言与用户偏好](translation.md)，让消息按用户的语言显示。
