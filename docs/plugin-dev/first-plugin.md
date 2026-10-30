# 第一个插件

> 我刚刚装好 BotQraft ，现在想装一个简单的回复插件测试功能：用户发送 `/echo Hello BotQraft`，机器人就回复 `Hello BotQraft`。该从哪里开始？

这部分将引导你从零开始熟悉插件开发和测试流程，并理解一个简单的 Echo 插件。

## 创建插件文件

先找一个准备用作实例目录的文件夹，在里面执行下面的命令初始化实例：

```bash
python -m botqraft init
```

这个命令会在当前目录创建 `config.yml`、`permissions.yml`，以及 `plugins/`、`config/botqraft/`、`logs/` 三个目录。其中 `plugins/` 就是默认的插件目录，它由 `config.yml` 的 `plugin_directories` 决定。

接着在实例目录里创建 `plugins/echo.py`，写入下面的内容：

```python
"""Reply passively with the text supplied to /echo."""
from types import ModuleType

from botqraft.api.command import CommandContext, GreedyText, QQCommandSource, SimpleCommandBuilder
from botqraft.api.types import QQPluginServerInterface

PLUGIN_METADATA = {
    'id': 'echo',
    'version': '1.0.0',
    'name': 'Echo',
    'description': 'Passively echo the supplied text',
    'dependencies': {'botqraft': '>=0.1.0'},
}

def echo(source: QQCommandSource, context: CommandContext) -> None:
    source.reply(context['text'])

def on_load(server: QQPluginServerInterface, prev_module: ModuleType | None) -> None:
    builder = SimpleCommandBuilder()
    builder.command('/echo <text>', echo)
    builder.arg('text', GreedyText)
    builder.register(server)
    server.register_help_message('/echo', {
        'zh_cn': '复述提供的文本',
        'en_us': 'Echo the supplied text',
    })
```

这段代码做了三件事：

- `PLUGIN_METADATA` 是插件的[元数据](metadata.md)，让单文件插件可以直接加载；
- `on_load` 是[回调事件](events.md)，在插件加载时注册命令和帮助；
- `SimpleCommandBuilder` 是一个[注册命令工具](commands.md)，其中`/echo <text>`是目标指令，`GreedyText` 是**指令参数类型**，`context['text']` 读取用户消息中`<text>`部分的值。

先不要着急试图全部理解，让我们一步步来。

## 启动并加载

打开实例目录里的 `config.yml`，填入你的 QQ 开放平台凭据：

```yaml
appid: "YOUR_APPID"
secret: "YOUR_APP_SECRET"
```

然后启动实例：

```bash
python -m botqraft
```

启动时，框架会先加载插件，再连接 QQ。等到看到 `BotQraft READY` ，连接就完成了，Echo 也加载好了。

如果实例已经在运行，你也可以直接刷新新增插件。在控制台输入下面的指令：

```text
/botqraft plugin refresh
/botqraft plugin list
```

注意，如果想在 QQ 中执行上面的指令，执行者必须是 `permission.super_admins` 中的超级管理员。

`/botqraft plugin refresh` 会重新扫描插件目录：加载新放进去的插件，卸载文件已经删除的插件，并重载已加载的插件。`/botqraft plugin list` 会列出已加载、已禁用和未加载的插件。

如果 Echo 已经加载了，但你修改了代码，想重新加载，也可以直接执行：

```text
/botqraft plugin reload echo
```

注意，每个插件 ID 在插件目录里只放一份。同一个 ID 出现多份时，只会加载其中一份，其余的会在日志里报重复错误。

Echo 没有加载？没关系，先打开日志看看有没有报错。重点看元数据、入口导入和依赖这三类提示，通常很快就能找到问题。

## 在 QQ 中验证

在 C2C 私聊里直接发送下面的消息，或者在群聊里 @机器人 后发送：

```text
/echo Hello BotQraft!
```

群里通常只有 @机器人 的消息才会推送给机器人。开头的这个 @ 会在匹配命令前去掉。

发送之后，逐项确认这些内容：

- [ ] 机器人回复 `Hello BotQraft!`;
- [ ] 发送 `/botqraft`，列表中出现 `/echo`;
- [ ] `/echo` 应该是群聊和 C2C 私聊通用的。

## 更进一步

想了解更多命令细节、注册更复杂的自定义指令？从[注册命令](commands.md)和[命令树](command-tree.md)开始，实现子命令节点解析、参数约束和权限检查。

想用更规范的插件格式？读[插件格式](plugin-format.md)。

或者，让我们一步步来：下一节[插件是怎么运行的](basic.md)，看看 Echo 背后框架做了什么。
