# API 索引

读完这一页，你能查到插件能用的全部公开接口，以及每个接口放在哪个子模块里。

从 `botcraft.api` 的公开子模块导入插件接口。`botcraft.api` 根模块本身不导出对象，按用途选择下面的模块。各模块的 `__all__` 定义公开导出。

```python
from botcraft.api.command import Literal, QQCommandSource
from botcraft.api.qtext import QMarkdown
from botcraft.api.types import QQPluginServerInterface
```

## `botcraft.api.command`

命令树、参数解析和 QQ 命令来源。用法见[命令系统](commands.md)、[SimpleCommandBuilder](simple-command-builder.md)和[命令树](command-tree.md)。

- 来源与解析：`QQCommandSource`、`CommandContext`、`ParseResult`、`command_builder_utils`。
- 节点：`AbstractNode`、`Literal`、`ArgumentNode`、`Number`、`Integer`、`Float`、`Text`、`QuotableText`、`GreedyText`、`Boolean`、`Enumeration`、`CountingLiteral`。
- 构建工具：`SimpleCommandBuilder`、`Requirements`、`NodeDefinition`。
- 命令异常：`CommandErrorBase`、`IllegalNodeOperation`、`CommandError`、`UnknownCommand`、`UnknownArgument`、`UnknownRootArgument`、`RequirementNotMet`、`CommandSyntaxError`、`IllegalArgument`、`LiteralNotMatch`、`AbstractOutOfRange`、`NumberOutOfRange`、`InvalidNumber`、`InvalidInteger`、`InvalidFloat`、`TextLengthOutOfRange`、`IllegalEscapesUsage`、`UnclosedQuotedString`、`EmptyText`、`InvalidBoolean`、`InvalidEnumeration`。

## `botcraft.api.event`

本地事件和 QQ 入站事件。用法见[插件事件](events.md)、[事件消息格式](message-format.md)和[交互事件](interactions.md)。

- 本地事件：`Event`、`PluginEvents`、`PluginEvent`、`LiteralEvent`、`EventListener`。
- QQ 入站对象：`QQEvent`、`QQInteraction`、`QQMessageReceived`。

## `botcraft.api.decorator`

- `event_listener`：本地插件事件监听。
- `qq_event_listener`：QQ 官方事件监听。
- `new_thread`、`FunctionThread`：沿用 MCDR 的线程装饰器与线程类型。
- `spam_proof`：沿用 MCDR 的防重复调用装饰器。

创建后台工作后，要在卸载时安排停止和资源关闭，参见[后台任务与卸载](tasks.md)。

## `botcraft.api.qtext`

QQ 消息、翻译与键盘。用法见[Markdown、文本交互与键盘](markdown.md)和[翻译与用户语言](translation.md)。

- 文本：`QTextBase`、`QText`、`QMarkdown`、`QTextAt`、`QTextInput`。
- 翻译：`QQTranslationText`、`tr`、`rtr`。
- 键盘：`QKeyboardBase`、`QKeyboardTemplate`、`QKeyboardCustom`、`QKeyboardButton`。
- 键盘字段：`QKeyboardRenderData`、`QKeyboardPermission`、`QKeyboardModal`。
- 动作：`QKeyboardAction`、`QKeyboardActionJump`、`QKeyboardActionCallback`、`QKeyboardActionCommand`。
- 枚举：`QKeyboardActionType`、`QKeyboardPermissionType`。

## `botcraft.api.types`

接口、身份、消息数据、交互数据和权限偏好类型。

| 分类       | 公开对象                                                                                                                                |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| 服务接口   | `QQServerInterface`、`QQPluginServerInterface`                                                                                          |
| 身份与场景 | `User`、`MentionedUser`、`Group`、`Scene`、`MemberRole`                                                                                 |
| 收件数据   | `QQMessageReceivedData`、`MessageScene`、`MessageAttachment`、`ARKData`、`MsgElement`                                                   |
| 消息枚举   | `MessageType`、`MessageSceneSource`、`AttachmentContentType`、`ARKType`                                                                 |
| 发送回执   | `QQMessageReceipt`、`QQMessageReceiptData`、`MessageExtInfo`                                                                            |
| 交互数据   | `QQInteractionData`、`InteractionData`、`InteractionResolved`、`InteractionMessageScene`、`AuthorizeData`                               |
| 交互枚举   | `InteractionType`、`InteractionScene`、`InteractionChatType`、`FeedbackOption`、`InteractionAction`、`AuthorizeScene`、`AuthorizeScope` |
| 权限与偏好 | `PreferenceItem`、`PermissionLevel`、`PermissionLevelItem`                                                                              |

插件回调拿到的是绑定当前插件的 `QQPluginServerInterface`。命令来源的 `get_server()` 返回 `QQServerInterface`。绑定插件接口提供插件登记、数据目录和打包资源访问。

身份用 `User.id`，会话地址和 AT 用各自的 OpenID 字段。收到的消息和发送回执分别用对应类型，参见[事件消息格式](message-format.md)和[主动发送](sending.md)。

## `botcraft.api.exception`

| 公开对象                                         | 用途                                      |
| ------------------------------------------------ | ----------------------------------------- |
| `UnsupportedOperationError`                      | 操作需要 Minecraft 等其他宿主能力时抛出。 |
| `RuntimeNotReadyError`                           | 实例状态不接受当前操作。                  |
| `PassiveReplyExpiredError`                       | 被动回复上下文过期。                      |
| `NetworkError`                                   | 网络和平台失败的公开异常基类。            |
| `PlatformError`、`GatewayError`、`NotReadyError` | 平台、网关和发送连接状态相关的失败。      |
| `ResultUnknownError`                             | 平台可能已经执行操作，结果尚未确认。      |
| `ErrorCategory`                                  | 稳定的失败分类枚举。                      |

用 `NetworkError` 的 `category`、`http_code`、`err_code`、`code`、`trace_id` 判断失败。异常文字用于阅读和诊断。遇到 `ResultUnknownError` 先核实结果，再决定要不要提交，保证每项操作只执行一次。结果处理见[响应事件与回复消息](reply.md)。

## `botcraft.api.utils`

导出 MCDR 序列化工具 `Serializable`、`serialize`、`deserialize`。数据存储用法见[插件数据与打包资源](data.md)。

## `botcraft.api.all`

聚合 `command`、`decorator`、`event`、`qtext`、`types`、`exception`、`utils` 的公开导出，并去重。想集中导入时，从这里选名称。常规插件按用途显式导入，接口来自哪里一眼能看清。

## 与 MCDR 插件的差异

把 MCDR 插件迁到 BotCraft 时，运行宿主换成了 QQ 机器人。命令节点、插件元数据和生命周期都能沿用，但输入、身份、消息和宿主操作都要跟着换。逐条对照：

- Minecraft 子进程、RCON 和服务端信息都属于 Minecraft 宿主能力。在 BotCraft 里调用它们会抛出 `UnsupportedOperationError`，请把业务改写成 QQ 事件和接口能完成的动作。
- QQ 发送接口接受 `str`、`QText`、`QMarkdown` 或延迟翻译文本。原生 `RText` 先转换成这些公开格式。
- 公共 `execute_command(command, source)` 接收本实例真实的 `QQCommandSource`。从命令回调或入站消息的 `event.get_command_source()` 取来源。`get_plugin_command_source()` 会抛出 `UnsupportedOperationError`。QQ 命令直接用真实入站消息的来源。
- `QQServerInterface.si()` 需要 BotCraft 正在运行，实例没跑起来时会抛出 `RuntimeError`。可选访问用 `si_opt()`，没有接口时返回 `None`。插件回调优先用传入的 `server`，访问实例用公共 QQ 接口。
- `.mcdr` 是共享的压缩格式，迁到 QQ 时把输入事件、身份、消息和宿主操作一起改。格式与入口见[插件格式](plugin-format.md)。

接下来，[今日人品插件](jrrp-plugin.md)会把这些公开接口组合成一个完整功能。
