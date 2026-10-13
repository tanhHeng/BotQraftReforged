# Markdown、文本交互与键盘

这一页讲怎么在插件里拼出 QQ 的 Markdown 消息、自定义键盘和文本交互。读完你能构造出可直接发送的消息数据。

从 `botcraft.api.qtext` 导入消息和键盘对象。先构造消息数据，再把它传给[回复接口](reply.md)。实际发送需要账号拥有 Markdown 和键盘权限。

## 构造 Markdown 消息

`QMarkdown` 构造器中的字符串按 Markdown 处理。追加用户文本时使用 `append`，普通字符串和 `QText` 会按纯文本转义：

```python
from botcraft.api.qtext import QMarkdown, QText

message = QMarkdown('**Echo**: ').append(QText('<hello>'))
payload = message.to_payload()
assert payload['msg_type'] == 2
assert payload['markdown']['content'] == '**Echo**: &lt;hello&gt;'
```

- `QText` 编码普通文本。
- `QMarkdown.append(str_or_QText)` 转义 HTML 和 Markdown 特殊字符。
- 追加 `QMarkdown` 时保留其 Markdown。
- `append`、`set_keyboard` 修改自身，`+` 生成副本，`copy()` 复制消息并隔离键盘。
- `set_keyboard(None)` 移除键盘。每条组合消息最多包含一个键盘。重复组合会抛出 `ValueError`，原内容和键盘保持不变。

## 添加自定义键盘

把按钮按行排列，再附加到消息：

```python
from botcraft.api.qtext import (
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

上例只在本地构造消息数据。在真实的命令回调里要调用 `source.reply(message)` 提交到 QQ。键盘的命令文本要和[命令系统](commands.md)注册的根名称保持一致。

使用平台模板时，改为 `QKeyboardTemplate(actual_template_id)`。模板 ID 使用非空字符串。

## 选择按钮行为

| 对象                      | 行为                                                                     |
| ------------------------- | ------------------------------------------------------------------------ |
| `QKeyboardActionJump`     | 跳转，动作类型为 0。                                                     |
| `QKeyboardActionCallback` | 回调，动作类型为 1，`data` 必填。处理方式见[交互事件](interactions.md)。 |
| `QKeyboardActionCommand`  | 命令，动作类型为 2，`data` 必填。                                        |

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

## 添加文本交互

使用对象表达交互能力。普通字符串中的标签样式文字按文本处理。`QTextAt`、`QTextInput` 可以直接发送，也可以通过加法组合，或作为 `tr/rtr` 的格式化参数。交互对象的标签身份在 Markdown 转换、复制和延迟翻译中保留。

```python
from botcraft.api.qtext import QTextAt, QTextInput, QMarkdown

message = QMarkdown('**请选择：** ').append(
    QTextAt('actual_member_openid'), ' ',
    QTextInput('/echo 编辑内容', show='编辑后发送', reference=True),
)
```

### 提及用户

`QTextAt(target)` 接收 `User` 或明确的提及 ID 字符串。传入 `User` 时，提及地址取 `member_openid`，真实身份取 `User.id`，昵称用于展示。

请使用非空、可用的 `member_openid`。缺少该字段或目标类型错误会抛出 `TypeError`。空 ID 或包含协议分隔符的 ID 会抛出 `ValueError`。当前支持群聊文本与 Markdown 中的单用户提及，@全体成员不在当前支持范围内。

### 填入输入框

`QTextInput(text, *, show=None, reference=False)` 用于 Markdown。传入编码前的 `text` 和 `show` 字符串，各最多 100 个 Unicode 字符。接口校验长度后进行一次 URL 编码。`show=None` 时省略展示文本。

`reference` 使用 bool，控制客户端填入输入框时的回复引用。发送消息的引用使用 `refer_msg` 单独设置。参数类型错误抛出 `TypeError`，编码前超出 100 字符抛出 `ValueError`。

`str` / `QText` 与 `QTextInput` 通过加法组合时，结果自动转换为 `QMarkdown`，并发出 `UserWarning`。显式使用 `QMarkdown` 组合即可直接获得 Markdown 结果。`QText.append(QTextInput)` 会抛出 `TypeError` 并保留原对象，请改用加法或 `QMarkdown`。

复制会隔离键盘，追加失败时保留原内容。直接重新赋值 `.text` 会按新的普通文本重建 Markdown 副本，旧交互片段的身份随旧副本一起替换。

协议依据见仓库中的 [QQ 文本链文档](https://github.com/BotCraftReforged/BotCraftReforged/blob/main/reference/qq_docs/server-inter/message/trans/text-chain.md)。编码前 100 字符校验是本库自己的选择。客户端展示、点击填入和引用效果由 QQ 平台支持决定。

接下来，阅读[翻译与用户语言](translation.md)，让消息按用户的语言显示。
