# 按钮：键盘与点击响应

> **场景**：我想在今日人品的结果下面放“再测一次”和“投稿”两个按钮，用户点了按钮，插件还要能接住这次点击。该怎么做？

读完这一页，你能在消息下面挂一排按钮，并接住用户点击按钮的操作，告诉平台这次交互处理完了。

按钮挂在消息的键盘上。消息和键盘对象都从 `botqraft.api.qtext` 导入。和普通消息一样，先构造消息，再把它交给[回复接口](reply.md)。要真正发送，账号需要拥有 Markdown 和键盘权限。Markdown 正文怎么写，见[Markdown 消息与文本交互](markdown.md)。

## 添加自定义键盘

先把按钮一行一行排好，再挂到消息上：

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

上面的例子只在本地构造了消息数据。在真实的命令回调里，调用 `source.reply(message)` 才会把它发到 QQ。另外，键盘里的命令文本要和[注册命令](commands.md)时的根名称一致。

`set_keyboard` 会直接修改消息本身，`set_keyboard(None)` 则移除键盘。每条组合消息最多只能有一个键盘。

使用平台模板时，改用 `QKeyboardTemplate(actual_template_id)`。模板 ID 必须是非空字符串。

## 选择按钮行为

| 对象                      | 行为                                                                                           |
| ------------------------- | ---------------------------------------------------------------------------------------------- |
| `QKeyboardActionJump`     | 跳转，动作类型为 0。                                                                           |
| `QKeyboardActionCallback` | 回调，动作类型为 1，`data` 必填。点击后推送交互事件，见[响应按钮点击](#响应按钮点击)。         |
| `QKeyboardActionCommand`  | 命令，动作类型为 2，`data` 必填。点击后在输入框插入 `@机器人 data`，用户发出后走普通命令流程。 |

下面几个字段控制按钮的额外效果：

- `enter=True`：命令按钮点击后直接发送 `data`。按平台说明，只在单聊里可用。
- `reply=True`：发出的指令会引用回复键盘所在的那条消息。
- `anchor`：设置后平台会忽略 `enter`。平台目前只定义了 `anchor=1`，用来唤起手机 QQ 的选图器，仅限手机端单聊。

这些效果能否生效，还要看客户端版本和使用场景。发送接口自己的引用则通过 `refer_msg` 单独设置。

`QKeyboardPermission()` 默认允许所有人（`ALL`）。想只让某些用户点击，就用 `QKeyboardPermissionType.SPECIFY`，并通过 `specify_user_ids` 传入一个非空的字符串列表。想只让管理员点击，就用 `ADMIN`。`ADMIN` 和 `ALL` 都不能带用户列表。权限类型创建后不能用 `set_type` 切换，需要换类型时，请新建一个对象。

按钮权限只决定谁能在平台上和这个按钮交互。服务器端的执行权限会通过命令节点单独检查，参见[权限系统](permissions.md)。

## 设置键盘字段

键盘对象的设置方法可以连着调用，例如 `render_data.set_label('Echo').set_style(1)`。可选字段传 `None` 就会被省略；`False` 和整数 `0` 则会保留在消息数据里。

创建对象、调用设置方法和编码时，都会检查类型和字段约束。设置方法只在校验通过后才替换字段。类型错误抛出 `TypeError`；非法值、重复的按钮 ID 和超长字段抛出 `ValueError`。主要约束如下：

- `QKeyboardCustom` 接收按钮行的列表，每一行也是一个列表。所有按钮都用 `QKeyboardButton`，非 `None` 的按钮 ID 在整个键盘里不能重复。
- `QKeyboardRenderData.label` 最多 10 字符，`style` 可选 0、1、3、4。
- `QKeyboardModal.content` 最多 40 字符，并且不能包含 URL（含 `://` 或 `www.` 的文本会被拒绝）。`confirm_text`、`cancel_text` 各最多 4 字符。
- 动作和权限类型用公开枚举或合法的整数代码，bool 会被拒绝。每个动作子类都有自己固定的类型。

除此之外，最终长度、行列数量和账号能力还要符合 QQ 平台的规则。客户端怎么展示、点击后有什么效果，取决于平台的支持情况。

## 响应按钮点击

用户在 QQ 点了回调按钮，平台会推送一条交互事件。框架把它解析成 `QQInteraction`，交给你的 `on_interaction(server, event)`。你要做的是：确认这是自己按钮的点击，然后回一个响应码，告诉平台处理结果。

回调怎么登记，见[监听消息与事件](events.md)。响应交互走的是一个独立接口，和[回复消息](reply.md)里的普通回复不是一回事。

先给插件的按钮分配一个稳定的 `button_id`。在回调里认出这个 ID，再提交响应。下面的示例处理 ID 为 `example_confirm` 的按钮，用响应码 `0` 告诉平台处理成功：

```python
from botqraft.api.event import QQInteraction
from botqraft.api.types import QQPluginServerInterface

def on_interaction(server: QQPluginServerInterface, event: QQInteraction):
    data = event.interaction_data.data
    resolved = data.resolved if data is not None else None
    if resolved is not None and resolved.button_id == 'example_confirm':
        server.respond_interaction(event, 0)
```

每类交互由哪段代码处理，最好事先划分清楚，保证同一个交互只在一个地方提交响应。

`respond_interaction` 只接收真实的 `QQInteraction`，传入其他对象会抛出 `TypeError`。

响应码是整数 `0`–`5`，也可以传一个值在这个范围内的整数枚举。按平台定义，0 成功、1 操作失败、2 操作频繁、3 重复操作、4 没有权限、5 仅管理员操作。传布尔值、其他类型或范围外的值，都会抛出 `ValueError`。

调用形式是 `server.respond_interaction(event, code)`。它直接返回一个 `concurrent.futures.Future`，成功时结果为 `None`。Future 怎么用，见[确认发送结果](reply.md#确认发送结果)。

## 读取交互数据

`QQInteraction` 继承自 `QQEvent`，所以 `event_type`、`event_id`、`raw_payload`、`data` 这些字段都还在。`raw_payload` 是平台推送的原始 JSON，`data` 是其中的原始事件数据 `d`。详见[读取事件的原始数据](message-format.md#读取事件的原始数据)。

交互专用的字段解析后放在 `QQInteraction` 的两个位置：

| 字段                    | 位置与用途                                                        |
| ----------------------- | ----------------------------------------------------------------- |
| `interaction_id`        | `QQInteraction` 顶层字段，取自原始事件数据 `d.id` 中的交互 ID。   |
| `interaction_data`      | `QQInteraction` 顶层字段，解析后的 `QQInteractionData` 对象。     |
| `interaction_data.id`   | 交互 ID（和 `interaction_id` 一致）。                             |
| `interaction_data.data` | 具体交互内容，`InteractionData` 对象，包含 `type` 和 `resolved`。 |

注意区分：`event_id` 是事件 ID，`interaction_id` 是交互 ID，两者不是一回事。不过你不用自己挑，把收到的事件整个传进去，框架会从原始交互数据里确定要响应哪一次交互。

`interaction_data` 的顶层有 `id`、`type`、`scene`、`chat_type`、`timestamp`、`version`、`application_id`，以及平台提供的 `guild_id`、`channel_id`、`user_openid`、`group_openid` 和 `group_member_openid`。

具体的交互内容在 `interaction_data.data` 里：

- `type` 表示交互种类。
- `resolved` 是 `InteractionResolved` 对象，提供 `button_id`、`button_data`、`user_id`、`feature_id` 和 `message_id`。
- 反馈、选择和动作数据也在 `resolved` 里：`feedback_opt`、`checked`、`action`。
- 来源扩展在 `resolved.message_scene`，授权场景与范围在 `resolved.authorize_data`。

这些字段都可能缺失或为 `None`，请以当前交互实际带来的字段为准。`QQInteractionData`、`InteractionData`、`InteractionResolved` 和相应的枚举都从 `botqraft.api.types` 导入。

`on_interaction` 只会收到解析成功的交互。如果想查看解析失败的原始数据，可以在 `on_qq_event` 或对官方 `INTERACTION_CREATE` 的精确监听里，检查 `model_parse_failed` 和 `parse_error`。

## 一次交互只响应一次

同一个交互 ID 只能响应一次。无论响应正在提交、已经提交成功，还是结果未知，再次提交都会立刻抛出 `ValueError`。

类型、交互 ID、响应码和连接状态会在提交时检查。HTTP 和平台返回的错误则通过 Future 报告，你可以用 `NetworkError` 的结构化字段判断结果。

如果确定失败，框架会释放这次交互的提交记录，你可以根据失败原因决定要不要重试。如果收到 `ResultUnknownError`，说明平台可能已经接受了响应，框架会保留提交记录。这时请先核实结果，不要重复操作。

发送前先调用 `server.is_ready()` 查看连接状态，同时也要处理状态变化导致的提交失败。异常类型和 Future 的处理方式见[处理提交与网络错误](reply.md#处理提交与网络错误)。

接下来，阅读[多语言与用户偏好](translation.md)，让消息按用户的语言显示。
