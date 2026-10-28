# API 索引

> **场景**：我记得有个能发 Markdown 的类，但忘了它叫什么、该从哪个模块导入。去哪里查？

读完这一页，你能查到插件能用的全部公开接口，以及每个接口放在哪个子模块里。

插件接口都从 `botqraft.api` 的公开子模块导入。`botqraft.api` 根模块本身不导出任何对象，请按用途从下面的模块里挑。每个模块公开导出哪些名字，以它的 `__all__` 为准。

```python
from botqraft.api.command import Literal, QQCommandSource
from botqraft.api.qtext import QMarkdown
from botqraft.api.types import QQPluginServerInterface
```

## `botqraft.api.command`

命令树、参数解析和 QQ 命令来源。用法见[注册命令](commands.md)和[命令树](command-tree.md)。

- 来源与解析：`QQCommandSource`、`CommandContext`、`ParseResult`、`command_builder_utils`。
- 节点：`AbstractNode`、`Literal`、`ArgumentNode`、`Number`、`Integer`、`Float`、`Text`、`QuotableText`、`GreedyText`、`Boolean`、`Enumeration`、`CountingLiteral`。
- 构建工具：`SimpleCommandBuilder`、`Requirements`、`NodeDefinition`。
- 命令异常：`CommandErrorBase`、`IllegalNodeOperation`、`CommandError`、`UnknownCommand`、`UnknownArgument`、`UnknownRootArgument`、`RequirementNotMet`、`CommandSyntaxError`、`IllegalArgument`、`LiteralNotMatch`、`AbstractOutOfRange`、`NumberOutOfRange`、`InvalidNumber`、`InvalidInteger`、`InvalidFloat`、`TextLengthOutOfRange`、`IllegalEscapesUsage`、`UnclosedQuotedString`、`EmptyText`、`InvalidBoolean`、`InvalidEnumeration`。

## `botqraft.api.event`

事件定义、监听器和 QQ 入站事件。用法见[监听消息与事件](events.md)、[读取消息内容](message-format.md)和[按钮：键盘与点击响应](interactions.md)。

- 事件定义与监听器：`Event`、`PluginEvents`、`PluginEvent`、`LiteralEvent`、`EventListener`。`PluginEvents` 同时列出 BotQraft 生命周期事件和 QQ 消息、交互事件。
- QQ 入站对象：`QQEvent`、`QQInteraction`、`QQMessageReceived`。

## `botqraft.api.decorator`

- `qq_event_listener`：把回调注册为当前插件的事件监听器，事件可以是 `PluginEvents` 中的事件、QQ 事件类型或自定义事件 ID。
- `event_listener`：`qq_event_listener` 的别名，行为完全相同。
- `new_thread`、`FunctionThread`：MCDR 的线程装饰器与线程类型。被装饰的函数在新的守护线程中运行，调用后返回 `FunctionThread`。
- `spam_proof`：MCDR 的防并发装饰器。同一时刻已有调用在执行时，后来的调用会被跳过。

如果你创建了后台工作，记得在卸载时停止它并关闭资源，做法见[后台任务与卸载](tasks.md)。

## `botqraft.api.qtext`

QQ 消息、翻译与键盘。用法见[Markdown 消息与文本交互](markdown.md)、[按钮：键盘与点击响应](interactions.md)和[多语言与用户偏好](translation.md)。

- 文本：`QTextBase`、`QText`、`QMarkdown`、`QTextAt`、`QTextInput`。
- 媒体：`QMediaBase`、`QImage`、`QVideo`、`QVoice`、`QFile`，见[发送图片、视频和文件](media.md)。
- 翻译：`QQTranslationText`、`tr`、`rtr`。
- 键盘：`QKeyboardBase`、`QKeyboardTemplate`、`QKeyboardCustom`、`QKeyboardButton`。
- 键盘字段：`QKeyboardRenderData`、`QKeyboardPermission`、`QKeyboardModal`。
- 动作：`QKeyboardAction`、`QKeyboardActionJump`、`QKeyboardActionCallback`、`QKeyboardActionCommand`。
- 枚举：`QKeyboardActionType`、`QKeyboardPermissionType`。

## `botqraft.api.types`

接口、身份、消息数据、交互数据和权限偏好类型。

| 分类       | 公开对象                                                                                                                                |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| 服务接口   | `QQServerInterface`、`QQPluginServerInterface`                                                                                          |
| 身份与场景 | `User`、`MentionedUser`、`Group`、`C2C`、`Scene`、`MemberRole`                                                                          |
| 收件数据   | `QQMessageReceivedData`、`MessageScene`、`MessageAttachment`、`ARKData`、`MsgElement`                                                   |
| 消息枚举   | `MessageType`、`MessageSceneSource`、`AttachmentContentType`、`ARKType`                                                                 |
| 发送回执   | `QQMessageReceipt`、`QQMessageReceiptData`、`MessageExtInfo`                                                                            |
| 交互数据   | `QQInteractionData`、`InteractionData`、`InteractionResolved`、`InteractionMessageScene`、`AuthorizeData`                               |
| 交互枚举   | `InteractionType`、`InteractionScene`、`InteractionChatType`、`FeedbackOption`、`InteractionAction`、`AuthorizeScene`、`AuthorizeScope` |
| 权限与偏好 | `PreferenceItem`、`PermissionLevel`、`PermissionLevelItem`                                                                              |

插件回调拿到的是绑定了当前插件的 `QQPluginServerInterface`，而命令来源的 `get_server()` 返回的是 `QQServerInterface`。插件登记、数据目录和打包资源访问，都由绑定插件的接口提供。

识别用户身份用 `User.id`；会话地址和 AT 则用各自的 OpenID 字段。收到的消息和发送回执各有对应的类型，见[读取消息内容](message-format.md)和[主动发送](sending.md)。

## `botqraft.api.exception`

| 公开对象                        | 用途                                                                                                    |
| ------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `UnsupportedOperationError`     | 调用的 MCDR 接口在 QQ 侧没有对应能力时抛出，例如 Minecraft 服务端操作、插件命令来源、手动派发内置事件。 |
| `RuntimeNotReadyError`          | 实例状态不接受当前操作，例如停止后注册或调度任务。                                                      |
| `PassiveReplyExpiredError`      | 被动回复上下文过期（群聊 5 分钟、C2C 60 分钟）或未登记。                                                |
| `NetworkError`                  | 网络和平台失败的公开异常基类，表示操作确定没有完成。                                                    |
| `PlatformError`、`GatewayError` | `NetworkError` 的子类：平台有证据地明确拒绝、网关连接失败。                                             |
| `NotReadyError`                 | 运行时或网关未就绪时同步拒绝 QQ 操作。它是 `RuntimeNotReadyError` 的子类，不属于 `NetworkError`。       |
| `ResultUnknownError`            | `NetworkError` 的子类：平台可能已经执行操作，结果尚未确认，不要自动重试。                               |
| `ErrorCategory`                 | 稳定的失败分类枚举。                                                                                    |

判断失败原因时，请看 `NetworkError` 的 `category`、`http_code`、`err_code`、`code`、`trace_id`；异常文字只用于阅读和诊断。遇到 `ResultUnknownError` 时，先核实结果，再决定要不要提交，保证每项操作只执行一次。具体怎么处理结果，见[回复消息](reply.md#处理提交与网络错误)。

## `botqraft.api.utils`

导出 MCDR 的序列化工具 `Serializable`、`serialize`、`deserialize`。数据存储的用法见[插件数据与打包资源](data.md)。

## `botqraft.api.all`

汇总 `command`、`decorator`、`event`、`qtext`、`types`、`exception`、`utils` 的公开导出，并去掉重复。想从一个地方集中导入时，可以从这里取名字。不过常规插件更适合按用途显式导入，这样每个接口来自哪里一眼就能看清。

接下来，[今日人品插件](jrrp-plugin.md)会把这些公开接口组合成一个完整功能。
