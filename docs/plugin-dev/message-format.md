# 读取消息内容

> **场景**：收到一条群消息后，我想知道是谁发的、发在哪个群、有没有 @ 机器人，正文里还带了几张图片。这些信息去哪里取？

读完这一页，你能看懂 QQ 事件里的每个字段，也知道什么时候读原始数据、什么时候读已解析的对象。

先按[监听消息与事件](events.md)选好回调，再按这里的方式取字段。需要平台原始字段时，读 `raw_payload`。写命令时一般用 `context` 取参数就够了，用不到这一页。

## 读取消息正文与基础字段

`QQMessageReceived` 表示一条群聊或 C2C 消息。结构化消息字段在 `event.message_data` 里，它的类型是 `QQMessageReceivedData`。

```python
from botqraft.api.event import QQMessageReceived
from botqraft.api.types import QQPluginServerInterface

def on_message(server: QQPluginServerInterface, event: QQMessageReceived):
    content = event.message_data.content
    if isinstance(content, str):
        server.logger.info('Message text: %s', content)
```

最常用的字段：

| `message_data` 字段 | 内容                                       |
| ------------------- | ------------------------------------------ |
| `content`           | 可选正文字符串。                           |
| `author`            | `User`，包含作者的用户身份和会话地址字段。 |
| `group_openid`      | 群会话 OpenID。私聊通常没有。              |
| `id`                | 官方消息 ID，用于被动关联和撤回。          |
| `timestamp`         | 平台原始时间字符串。                       |

这些字段可能缺失，也可能是 `None`。请按消息实际包含的字段处理正文、附件和其他内容。

## 区分用户身份和会话地址

`message_data.author` 是 `User` 类型。`message_data.mentions` 是 `MentionedUser` 类型，它继承 `User`。两者都从 `botqraft.api.types` 导入。

记忆方法很简单：找会话，用对应的 OpenID；认用户，用 `User.id`。被动回复沿用收到的来源；主动发送使用 `Group` 或 `C2C` 目标，最常用的是 `source.target`。

| 字段                   | 用途                                                                |
| ---------------------- | ------------------------------------------------------------------- |
| `User.id`              | 真实用户身份，用于权限和偏好。                                      |
| `user_openid`          | C2C 会话地址。                                                      |
| `group_openid`         | 群会话地址。                                                        |
| `member_openid`        | 群内 AT 对象的会话地址。                                            |
| `scene`                | 场景，取值为 `group` 或 `c2c`。入站消息会为作者和提及对象补上场景。 |
| `member_role`          | 平台群角色，用于对应的角色权限模式。                                |
| `MentionedUser.is_you` | 该提及是否指向当前机器人。                                          |

具体用法见[回复消息](reply.md)和[发送消息](sending.md)。

`is_you` 的类型是 `Optional[bool]`。字段缺失或为 null 时，它是 `None`。判断是否是机器人的提及时，用 `is_you is True`。

## 复杂消息元素

大多数消息只有正文。当需要处理附件、卡片或提及时，再来看这些字段：

| `message_data` 字段 | 内容                                                      |
| ------------------- | --------------------------------------------------------- |
| `message_type`      | 消息类型。已识别的值用 `MessageType` 枚举表示。           |
| `message_scene`     | 可选 `MessageScene`，包含 `source`、`ext` 等来源上下文。  |
| `attachments`       | 可选 `MessageAttachment` 列表。                           |
| `mentions`          | 可选 `MentionedUser` 列表，完整保留机器人自身和其他用户。 |
| `ark_data`          | 可选 `ARKData` 卡片信息。                                 |
| `msg_elements`      | 可选 `MsgElement` 列表，可包含嵌套的合并转发内容。        |

`MessageAttachment` 提供 URL、文件名、宽高、大小和内容类型。它还提供语音 URL 和识别文本。

`ARKData` 提供提示文字、卡片类型、名称和开放的 JSON 字段。`MsgElement` 提供 `msg_idx`、作者、类型、正文、附件、卡片和嵌套元素。相关模型和枚举都从 `botqraft.api.types` 导入。

## 读取事件的原始数据

所有 QQ 入站事件都继承 `QQEvent`，从 `botqraft.api.event` 导入。

| 字段                 | 用途                                        |
| -------------------- | ------------------------------------------- |
| `event_type`         | 官方事件类型，对应平台原始字段 `t`。        |
| `event_id`           | 事件 ID，对应平台原始字段 `id`。            |
| `sequence`           | 平台推送序号，对应平台原始字段 `s`。        |
| `raw_payload`        | 平台推送的完整原始 JSON，包括事件数据 `d`。 |
| `data`               | 事件数据 JSON 的独立副本，可以编辑。        |
| `model_parse_failed` | 事件解析成对象是否失败。                    |
| `parse_error`        | 解析成对象失败时的异常。                    |

`raw_payload` 是平台原样送来的快照，`data` 是可以处理的另一份数据。想保留现场时看 `raw_payload`；想在代码里整理字段时用 `data`，两者各司其职。

用户身份、会话地址和能否被动回复，都以原始收到的数据为准。编辑 `data` 或已解析对象的字段，只会改变对应的副本。

解析失败时，框架回退成通用的 `QQEvent`，并保留原始数据和解析错误。全局监听和显式订阅官方事件的监听仍会收到它。

## 提及与前缀处理

框架在解析阶段统一处理正文前缀。命令和所有回调读到的都是同一个 `message_data.content`：

- `GROUP_AT_MESSAGE_CREATE` 移除正文前导 ASCII 空格。
- 当前 dev 版本对 `GROUP_MESSAGE_CREATE` 做临时修正。正文可以先有 ASCII 空格，之后必须是匹配某个 `MentionedUser.id` 的 `<@id>`，且该对象的 `is_you is True`。满足条件时，框架移除一个标签及其后的 ASCII 空格。
- `<@!id>`、正文中间的标签、重复出现的后续标签以及其他条件之外的正文均保持原样。
- 内部和尾部空格、引用元素、完整 mentions、`raw_payload` 和 `data` 保持原样。临时修正也保留原始收件日志。
- C2C 正文保持原样。

机器人提及列表和正文标签共同决定前缀。平台 AT 投递类型、正文是否含 AT 是两个不同的事实，请按各自的字段处理。

临时修正的代码在 [`botqraft/event/dev_group_message_prefix.py`](https://github.com/tanhHeng/BotQraftReforged/blob/main/botqraft/event/dev_group_message_prefix.py)。解析器调用后会把正文写回模型，事件类型和调用次数保持原样。

这个模块只处理当前事件的正文。持久配置、机器人身份缓存和网络状态查询由各自的服务负责。

平台修复后，移除此模块及解析器的导入和调用，保留 `MentionedUser` 公开 API。

## 获取消息来源

调用 `event.get_command_source()`，取得这条消息对应的原始 `QQCommandSource`。第一次调用会检查真实身份、消息 ID 和会话地址，然后缓存结果。缺少任何一项时会拒绝创建。

接下来，读[主动发送、引用与撤回](sending.md)，在回复之外主动发出消息。
