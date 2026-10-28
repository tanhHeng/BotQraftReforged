# 注册命令

> **场景**：我想加一条 `/roll <次数>` 命令，用户发 `/roll 3` 时机器人掷三次骰子，而且这条命令只在群里能用。该怎么注册？

读完这一页，你能用 `SimpleCommandBuilder` 注册带参数的命令，知道命令回调收到什么，还能把命令限定在群聊或私聊里。

命令要在插件的 `on_load` 里注册。用户在 QQ 发送命令后，框架解析命令，再调用对应的函数。命令相关的类都从 `botqraft.api.command` 导入。

## 用 SimpleCommandBuilder 注册命令

用 `SimpleCommandBuilder` 注册命令只要三步：先声明路径，再定义参数，最后登记到实例。下面的代码放在插件模块里。加载插件后，在 QQ 发送 `/echo Hello world`：

```python
from botqraft.api.command import CommandContext, GreedyText, QQCommandSource, SimpleCommandBuilder
from botqraft.api.types import QQPluginServerInterface

def echo(source: QQCommandSource, context: CommandContext) -> None:
    source.reply(context['text'])

def on_load(server: QQPluginServerInterface, prev_module) -> None:
    builder = SimpleCommandBuilder()
    builder.command('/echo <text>', echo)
    builder.arg('text', GreedyText)
    builder.register(server)
```

1. 先声明路径：`command('/echo <text>', echo)` 告诉框架这条命令长什么样，并指定路径末尾执行哪个回调。
2. 再定义参数：`arg('text', GreedyText)` 说明 `<text>` 这个占位符该收什么内容，这里收一段文本。
3. 最后登记到实例：`register(server)` 把前面的声明构建成命令树，注册到插件上。默认群聊和 C2C 都能用。

路径按空格分段。普通片段是固定词，`<参数名>` 是参数节点。每个参数都要用 `arg(...)` 定义一次，名字要和回调里读的 `context` 键一致。

这里的 `GreedyText` 接收剩余文本，并保留文本里的空格。完整可安装的版本见[第一个插件](first-plugin.md)。

## 接收 source 和 context

带参数的回调使用两个参数：

- `source` 是这次命令的真实 QQ 消息来源。
- `context` 保存命令解析出的参数。参数名叫 `text` 时，就用 `context['text']` 取值。
- `source.reply(...)` 回复触发命令的那条消息。回复关联使用原始消息 ID 和原会话。

只用来源的回调可以写成 `def ping(source): ...`。回调支持零到两个参数，依次是来源和上下文。

`QQCommandSource` 的常用成员如下：

| 成员                    | 用途                                                         |
| ----------------------- | ------------------------------------------------------------ |
| `user`                  | 查看发起命令的用户。                                         |
| `scene`                 | 查看当前场景：`group` 或 `c2c`。                             |
| `conversation`          | 查看当前会话地址。                                           |
| `target`                | 取得当前会话的 `Group` 或 `C2C` 目标，可传给 `server.send`。 |
| `msg_id`                | 查看原始入站消息 ID。                                        |
| `message_data`          | 读取消息正文等解析结果。                                     |
| `message_received`      | 取得原始收到的消息事件。                                     |
| `get_server()`          | 取得当前实例的 `QQServerInterface`。                         |
| `has_permission(level)` | 检查当前有效权限。                                           |

插件的 `on_load` 收到绑定插件的 `QQPluginServerInterface`。用这个接口登记命令、帮助和其他插件资源。回复细节见[回复消息](reply.md)，权限规则见[权限](permissions.md)。

## 选择参数类型

公开参数节点从 `botqraft.api.command` 导入：

| 节点           | 输入与结果                                   |
| -------------- | -------------------------------------------- |
| `Text`         | 单个文本片段。                               |
| `QuotableText` | 单个文本片段，或者引号包起来、含空格的文本。 |
| `GreedyText`   | 命令剩余的整段文本，要放在路径末尾。         |
| `Integer`      | 解析为整数。                                 |
| `Float`        | 解析为浮点数。                               |
| `Boolean`      | 解析为布尔值。                               |

例如把上例的 `GreedyText` 换成 `QuotableText`，就要用 `/echo "Hello world"` 传入含空格的文本。选择 `GreedyText` 时，直接发送 `/echo Hello world` 就行。

`arg` 的第二个参数也可以是工厂函数。它接收参数名，返回参数节点。例如：

```python
from botqraft.api.command import Integer

builder.arg('count', lambda name: Integer(name).at_min(1))
```

把 `<count>` 写进对应的命令路径，再从 `context['count']` 取得整数。

## 为一个根声明多条路径

多次调用 `command(...)`，共用同一个根名称，就能挂多条路径。Builder 会合并相同的路径节点：

```python
builder.command('/echo <text>', echo)
builder.command('/echo help', lambda source: source.reply('Usage: /echo <text>'))
builder.arg('text', GreedyText)
builder.register(server)
```

固定的子命令直接写在路径里。需要调整固定节点的行为时，用 `builder.literal(...)`。更复杂的结构见[命令树](command-tree.md)。

## 命令名称要和注册时一致

命令根会按字面匹配，而且 `/` 也是名字的一部分。可以把它当成门牌号：你注册 `/echo`，用户就从 `/echo` 这扇门进来。

比如注册 `/echo` 之后，在 QQ 发送：

```text
/echo Hello world
```

`echo Hello world` 用的是另一个根名称，匹配不上。请让用户的写法和注册的路径保持一致。

群消息进入命令解析前，正文按下面的规则处理：

- `GROUP_AT_MESSAGE_CREATE`：解析时去掉正文的前导 ASCII 空格（写回 `message_data.content`）。匹配命令时，框架还会再去掉开头指向本机器人的一个 `<@机器人id>` 或 `<@!机器人id>` 以及它前后的空白；这一步只影响命令解析，不改 `message_data.content`。
- `GROUP_MESSAGE_CREATE`：当前 dev 版本会整理正文前缀。它会跳过开头的 ASCII 空格，然后检查正文是否以 `<@id>` 开头；只有 mentions 里有同 id 且 `MentionedUser.is_you is True` 的项时，才会移除这个提及标签和后面的 ASCII 空格，结果写回 `message_data.content`，命令和回调看到的都是整理后的正文。条件不符时正文原样保留（包括前导空格）；`<@!id>`、正文中间的标签和重复的后续标签也不处理。
- 内部与尾部空格、引用元素、完整 mentions、`raw_payload`、`data` 都保持原样。
- C2C 正文保持原样。

事件字段见[读取消息内容](message-format.md)。

## 选择 scope

`scope` 决定命令在哪种 QQ 场景里可用：

| 注册值             | 场景                      |
| ------------------ | ------------------------- |
| `('group', 'c2c')` | 群聊和 C2C 私聊，默认值。 |
| `('group',)`       | 群聊。                    |
| `('c2c',)`         | C2C 私聊。                |

`builder.register(server)` 只接收 `server`，用的是默认场景。要限定为群聊，先 `build()`，再用插件接口逐个注册每个根：

```python
for root in builder.build():
    server.register_command(root, scope=('group',))
```

用这段替换 `builder.register(server)`。用命令树手写的根也一样，通过 `server.register_command(root, scope=...)` 指定场景。在没登记的场景里发送这条命令时，框架不会执行回调，而是回复一条命令错误提示 `Command is not available in this QQ scene`。

命令和帮助分别登记 `scope`。为同一条命令登记[帮助](help.md)时，填上相同的场景。能不能执行由节点的 `requires(...)` 检查，帮助的权限只控制帮助显不显示。

## 在真实 QQ 消息中执行

插件命令要在 QQ 里验证。运维控制台执行的是内置的 `/botqraft` 命令树。

需要从插件触发另一条命令时，调用 `server.execute_command(command, source)`。传入本实例真实的 `QQCommandSource`：可以用命令回调的来源，也可以用入站消息的 `event.get_command_source()`。来源的身份、消息 ID 和会话地址都来自真实收到的数据。

接下来，读[回复消息](reply.md)，把结果回给用户。
