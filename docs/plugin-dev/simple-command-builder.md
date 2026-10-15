# SimpleCommandBuilder

读完这一页，你能用 `SimpleCommandBuilder` 把一个带参数的命令注册进插件，还能把它限定在群聊里。

用 `SimpleCommandBuilder` 注册命令只要三步：先声明路径，再定义参数，最后登记到实例。Builder 会把这三步的声明构建成原生命令树。

## 声明路径和参数

下面的代码放在插件模块里。加载插件后，在 QQ 发送 `/echo Hello world`：

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

例如把上例的路径改成 `/echo <text>` 并改用 `QuotableText`，就要用 `/echo "Hello world"` 传入含空格的文本。选择 `GreedyText` 时，直接发送 `/echo Hello world` 就行。

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

固定的子命令直接写在路径里。需要调整固定节点的行为时，用 `builder.literal(...)`。更多用法见[命令树](command-tree.md)。

## 指定注册场景

`builder.register(server)` 只接收 `server`，用的是默认场景。要限定为群聊，先 `build()`，再用插件接口逐个注册每个根：

```python
for root in builder.build():
    server.register_command(root, scope=('group',))
```

用这段替换 `builder.register(server)`。为同一条命令登记[帮助](help.md)时，也填上 `scope=('group',)`。

接下来，把前面学到的串起来，写[第一个插件](first-plugin.md)。
