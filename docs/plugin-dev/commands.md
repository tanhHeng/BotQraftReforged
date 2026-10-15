# 命令系统

读完这一页，你会知道命令回调收到什么、命令在哪些场景生效。你还会明白为什么用户必须按你注册的写法来敲。

命令要在插件的 `on_load` 里注册。用户在 QQ 发送命令后，框架解析命令树，再调用对应的函数。

命令节点和 Builder 都从 `botqraft.api.command` 导入。先认识回调的来源、参数和场景，再用 [SimpleCommandBuilder](simple-command-builder.md) 注册命令。

## 接收 source 和 context

带参数的回调使用两个参数：

```python
from botqraft.api.command import CommandContext, QQCommandSource

def echo(source: QQCommandSource, context: CommandContext) -> None:
    source.reply(context['text'])
```

- `source` 是这次命令的真实 QQ 消息来源。
- `context` 保存命令节点解析出的参数。参数节点名叫 `text` 时，就用 `context['text']` 取值。
- `source.reply(...)` 回复触发命令的那条消息。回复关联使用原始消息 ID 和原会话。

只用来源的回调可以写成 `def ping(source): ...`。节点回调支持零到两个参数，依次是来源和上下文。

`QQCommandSource` 的常用成员如下：

| 成员                    | 用途                                 |
| ----------------------- | ------------------------------------ |
| `user`                  | 查看发起命令的用户。                 |
| `scene`                 | 查看当前场景：`group` 或 `c2c`。     |
| `conversation`          | 查看当前会话地址。                   |
| `msg_id`                | 查看原始入站消息 ID。                |
| `message_data`          | 读取消息正文等解析结果。             |
| `origin_received`       | 取得原始收到的事件。                 |
| `get_server()`          | 取得当前实例的 `QQServerInterface`。 |
| `has_permission(level)` | 检查当前有效权限。                   |

插件的 `on_load` 收到绑定插件的 `QQPluginServerInterface`。用这个接口登记命令、帮助和其他插件资源。回复细节见[响应事件与回复消息](reply.md)，权限规则见[权限](permissions.md)。

## 选择 scope

`scope` 决定命令在哪种 QQ 场景里可用：

| 注册值             | 场景                      |
| ------------------ | ------------------------- |
| `('group', 'c2c')` | 群聊和 C2C 私聊，默认值。 |
| `('group',)`       | 群聊。                    |
| `('c2c',)`         | C2C 私聊。                |

原生命令树通过 `server.register_command(root, scope=('group',))` 指定场景。Builder 的 `register(server)` 使用默认场景。要指定场景，方法见[下一页](simple-command-builder.md#指定注册场景)。

命令和帮助分别登记 `scope`。同一条命令要填相同的场景。能不能执行由节点的 `requires(...)` 检查，帮助的权限只控制帮助显不显示。

## 命令名称要和注册时一致

命令根会按字面匹配，而且 `/` 也是名字的一部分。可以把它当成门牌号：你注册 `/echo`，用户就从 `/echo` 这扇门进来。

比如注册 `/echo` 之后，在 QQ 发送：

```text
/echo Hello world
```

`echo Hello world` 用的是另一个根名称，匹配不上。请让用户的写法和注册的路径保持一致。

群消息进入命令解析前，正文按下面的规则处理：

- `GROUP_AT_MESSAGE_CREATE` 去掉前导 ASCII 空格。
- 当前 dev 版本会先整理 `GROUP_MESSAGE_CREATE` 的前缀。它会跳过开头的 ASCII 空格，然后检查正文是否以指向机器人的 `<@id>` 开头；只有对应的 `MentionedUser.is_you is True` 时，才会移除这个提及标签和后面的 ASCII 空格。
- 其他正文保持原样，包括 `<@!id>`、正文中间的标签和重复的后续标签。内部与尾部空格、引用元素、完整 mentions、`raw_payload`、`data` 和原始收件日志也保持原样。
- C2C 正文保持原样。

事件字段见[事件消息格式](message-format.md)。

## 在真实 QQ 消息中执行

插件命令要在 QQ 里验证。运维控制台执行的是内置的 `/botqraft` 命令树。

需要从插件触发另一条命令时，调用 `server.execute_command(command, source)`。传入本实例真实的 `QQCommandSource`：可以用命令回调的来源，也可以用入站消息的 `event.get_command_source()`。来源的身份、消息 ID 和会话地址都来自真实收到的数据。

接下来，用 [SimpleCommandBuilder](simple-command-builder.md) 声明命令路径。
