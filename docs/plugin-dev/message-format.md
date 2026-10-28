# 读取消息内容

> **场景**：收到一条群消息后，我想知道是谁发的、发在哪个群、有没有 @ 机器人，正文里还带了几张图片。这些信息去哪里取？

读完这一页，你能看懂 QQ 事件里的每个字段，也知道什么时候读原始数据、什么时候读已解析的对象。

先按[监听消息与事件](events.md)选好回调，再回到这里取字段。需要平台的原始字段时，读 `raw_payload` 就行。如果你只是在写命令，一般用 `context` 取参数就够了，可以先跳过这一页。

## 读取消息正文与基础字段

`QQMessageReceived` 代表一条群聊或 C2C 消息。解析好的消息字段都在 `event.message_data` 里，它的类型是 `QQMessageReceivedData`。

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

这些字段都是可选的，平台没给的字段值就是 `None`。所以读取正文、附件和其他内容之前，先确认这条消息里确实有这个字段。

## 区分用户身份和会话地址

`message_data.author` 是 `User` 类型。`message_data.mentions` 是 `MentionedUser` 类型，它继承 `User`。两者都从 `botqraft.api.types` 导入。

记忆方法很简单：找会话，用对应的 OpenID；认用户，用 `User.id`。被动回复直接用收到消息的来源；主动发送则要用 `Group` 或 `C2C` 目标，最常用的是 `source.target`。

| 字段                   | 用途                                                                                               |
| ---------------------- | -------------------------------------------------------------------------------------------------- |
| `User.id`              | 真实用户身份，用于权限和偏好。                                                                     |
| `user_openid`          | C2C 会话地址。                                                                                     |
| `group_openid`         | 群会话地址。                                                                                       |
| `member_openid`        | 群成员在该群里的 OpenID，`QTextAt` 用它 AT 这个成员。                                              |
| `scene`                | 场景，取值为 `group` 或 `c2c`。入站消息会为作者和提及对象补上场景，群消息还会补上 `group_openid`。 |
| `member_role`          | 平台群角色，用于对应的角色权限模式。                                                               |
| `MentionedUser.is_you` | 该提及是否指向当前机器人。                                                                         |

具体用法见[回复消息](reply.md)和[发送消息](sending.md)。

`is_you` 的类型是 `Optional[bool]`，字段缺失或为 null 时，它的值是 `None`。所以要判断一个提及是不是指向机器人，请写 `is_you is True`。

## 复杂消息元素

大多数消息只有正文。等你需要处理附件、卡片或提及时，再来看这些字段：

| `message_data` 字段 | 内容                                                      |
| ------------------- | --------------------------------------------------------- |
| `message_type`      | 消息类型。已识别的值用 `MessageType` 枚举表示。           |
| `message_scene`     | 可选 `MessageScene`，包含 `source`、`ext` 等来源上下文。  |
| `attachments`       | 可选 `MessageAttachment` 列表。                           |
| `mentions`          | 可选 `MentionedUser` 列表，完整保留机器人自身和其他用户。 |
| `ark_data`          | 可选 `ARKData` 卡片信息。                                 |
| `msg_elements`      | 可选 `MsgElement` 列表，可包含嵌套的合并转发内容。        |

`MessageAttachment` 提供 URL、文件名、宽高、大小和内容类型，还有语音 URL 和识别文本。

`ARKData` 提供提示文字、卡片类型、名称和开放的 JSON 字段。`MsgElement` 提供 `msg_idx`、作者、类型、正文、附件、卡片和嵌套元素。相关模型和枚举都从 `botqraft.api.types` 导入。

## 读取事件的原始数据

所有从 QQ 收到的事件都继承自 `QQEvent`，它从 `botqraft.api.event` 导入。

| 字段                 | 用途                                        |
| -------------------- | ------------------------------------------- |
| `event_type`         | 官方事件类型，对应平台原始字段 `t`。        |
| `event_id`           | 事件 ID，对应平台原始字段 `id`。            |
| `sequence`           | 平台推送序号，对应平台原始字段 `s`。        |
| `raw_payload`        | 平台推送的完整原始 JSON，包括事件数据 `d`。 |
| `data`               | 事件数据 JSON 的独立副本，可以编辑。        |
| `model_parse_failed` | 事件解析成对象是否失败。                    |
| `parse_error`        | 解析成对象失败时的异常。                    |

`raw_payload` 是平台原样送来的快照，`data` 是另一份供你处理的数据。想看原始现场，就读 `raw_payload`；想在代码里整理字段，就用 `data`。

不用担心改坏东西：用户身份、会话地址和能否被动回复，都以原始收到的数据为准。编辑 `data` 或已解析对象的字段，只会改变你手里的那份副本。

如果解析失败，框架会退回到通用的 `QQEvent`，同时保留原始数据和解析错误。`on_qq_event` 和按官方事件名精确监听的回调（显式登记、装饰器和 `on_<官方事件名小写>_event`）仍然会收到它，详见[监听消息与事件](events.md#消息回调的调用顺序)。

## 提及与前缀处理

正文开头的前缀，框架会在解析阶段统一处理好。不管是哪个回调，还是命令来源，读到的都是同一个 `message_data.content`。具体规则如下：

- `GROUP_AT_MESSAGE_CREATE` 会去掉正文开头的 ASCII 空格。
- 当前 dev 版本对 `GROUP_MESSAGE_CREATE` 做了一个临时修正：正文开头可以先有 ASCII 空格，接着必须是一个 `<@id>`，它要匹配某个 `MentionedUser.id`，并且这个提及对象的 `is_you is True`。满足这些条件时，框架会移除这一个标签和它后面的 ASCII 空格。
- `<@!id>`、正文中间的标签、后面重复出现的标签，以及不符合上述条件的其他正文，都保持原样。
- 内部和结尾的空格、引用元素、完整的 mentions、`raw_payload` 和 `data` 都保持原样。临时修正也会保留原始的收件日志。
- C2C 正文保持原样。
- 匹配命令时，`GROUP_AT_MESSAGE_CREATE` 还会再去掉开头一个指向机器人自身的 `<@id>` 或 `<@!id>`（机器人 ID 在连接 READY 时获得），连同它前后的空白。这一步只影响命令匹配，`message_data.content` 不会变。

前缀由机器人提及列表和正文标签共同决定。要注意，平台是不是按 AT 投递、正文里有没有 AT，是两件不同的事，请分别看各自的字段。

临时修正的代码在 [`botqraft/event/dev_group_message_prefix.py`](https://github.com/tanhHeng/BotQraftReforged/blob/main/botqraft/event/dev_group_message_prefix.py)。解析器调用它之后，会把处理好的正文写回模型。事件类型不变，回调也不会因此多触发一次。

这个模块只管当前事件的正文。持久配置、机器人身份缓存和网络状态查询，都由各自的服务负责。

平台修复后，需要移除这个模块，以及解析器里对它的导入和调用；`MentionedUser` 公开 API 保留不变。

## 获取消息来源

调用 `event.get_command_source()`，就能拿到这条消息对应的原始 `QQCommandSource`。

调用时，框架会检查真实身份、消息 ID 和会话地址，缺少任何一项都会抛出 `ValueError`。检查通过后，结果会缓存起来，之后再调用，拿到的都是同一个对象。

接下来，读一读[主动发送、引用与撤回](sending.md)，学习怎么在回复之外主动发出消息。
