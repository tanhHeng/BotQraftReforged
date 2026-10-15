# 命令树

读完这一页，你能用节点自己搭出命令分支，让每条输入都在正确的位置结束。

命令树就是把一条命令拆成一个个节点：固定词是分叉，参数是输入位置，回调是终点。它和 [SimpleCommandBuilder](simple-command-builder.md) 使用同一套解析规则，所以学会一种后，另一种也很好理解。

## 从 Literal 开始

命令根使用 `Literal`。`then(...)` 添加子节点，`runs(...)` 指定在当前节点结束时执行的回调：

```python
from botqraft.api.command import CommandContext, GreedyText, Literal, QQCommandSource
from botqraft.api.types import QQPluginServerInterface

def echo(source: QQCommandSource, context: CommandContext) -> None:
    source.reply(context['text'])

def on_load(server: QQPluginServerInterface, prev_module) -> None:
    root = Literal('/echo')
    root.runs(lambda source: source.reply('Usage: /echo <text>'))
    root.then(GreedyText('text').runs(echo))
    server.register_command(root)
```

这棵树有两个结束位置：

- `/echo` 在根节点结束，回复使用说明。
- `/echo Hello world` 在 `text` 参数节点结束，回复 `Hello world`。

`Literal` 匹配固定词。参数节点把解析结果放进 `CommandContext`，你用节点名取值。

## 用 then 组织分支

固定子命令也用 `Literal`。例如，在注册前给上例加一个帮助分支：

```python
root.then(
    Literal('help').runs(lambda source: source.reply('Usage: /echo <text>'))
)
```

这时 `/echo help` 匹配到固定子命令，执行帮助回调。

`then(...)` 返回当前的父节点。所以连续的 `root.then(a).then(b)` 添加的是两个并列子节点。要嵌套下一层，就在子节点上继续调用 `then(...)`：

```python
root.then(
    Literal('repeat').then(GreedyText('text').runs(echo))
)
```

这条分支对应 `/echo repeat Hello world`。

## 把 runs 放在输入可以结束的位置

`runs(...)` 设置当前节点的回调。请把它放在用户输入可以结束的位置：

- 放在根上，处理只有命令根的输入。
- 放在固定子命令上，处理不带参数的子命令。
- 放在最后一个参数节点上，处理完整参数。

回调支持零到两个参数，依次是 `source`、`context`。要读取参数就用两个参数。只回复固定内容时，可以只接收 `source`。

## 用 requires 检查条件

`requires(...)` 就像命令入口处的一道门。条件返回 `True`，用户继续往下走；返回 `False`，框架会用 `RequirementNotMet` 告诉用户这条分支当前不能执行。

下面只允许权限达到 2 的用户执行 `/admin ping`：

```python
from botqraft.api.command import Literal

root = Literal('/admin').requires(lambda source: source.has_permission(2))
root.then(Literal('ping').runs(lambda source: source.reply('pong')))
server.register_command(root, scope=('group',))
```

把这段注册代码放进 `on_load`。根上的条件覆盖它下面的所有子分支。只需要保护单个操作时，把条件放在对应的子节点上。

多次调用 `requires(...)` 会把条件组合起来，全部满足才继续。条件可以读取来源，也可以读取已经解析出的上下文。权限查询在真正执行的那一刻解析当前有效值，具体规则见[权限](permissions.md)。

登记[帮助](help.md)时，`permission` 和 `scope` 要分别填写。帮助可见性和节点执行检查各自生效。

接下来，把前面学到的串起来，写[第一个插件](first-plugin.md)。
