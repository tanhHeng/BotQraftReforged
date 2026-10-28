# 第一个插件

> **场景**：我刚装好 BotQraft，想先写一个最简单的插件：用户发 `/echo 你好`，机器人就回一句 `你好`。该从哪里开始？

读完这一页，你会装好一个 Echo 插件。它注册 `/echo <text>`，收到文本后回复原消息，把这段文本发回去。每一步的代码都可以直接复制。

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

这段代码做了三件事：`PLUGIN_METADATA` 让单文件插件可以直接加载；`on_load` 在插件加载时注册命令和帮助；`GreedyText` 把 `/echo Hello world` 的剩余部分当成一个值，交给 `context['text']`。

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

启动时，框架会先加载插件，再连接 QQ。稍等一会，看到 `BotQraft READY` 就说明连接已经就绪，Echo 也已经随启动加载好了。

如果实例已经在运行，也可以直接刷新插件。下面这些命令在运维控制台输入；在 QQ 里，只有 `permission.super_admins` 中的超级管理员能用：

```text
/botqraft plugin refresh
/botqraft plugin list
```

`/botqraft plugin refresh` 会重新扫描插件目录：加载新放进去的插件，卸载文件已经删除的插件，并重载已加载的插件。`/botqraft plugin list` 会列出已加载、已禁用和未加载的插件。

以后修改了 Echo，执行下面的命令重载它：

```text
/botqraft plugin reload echo
```

注意，每个插件 ID 在插件目录里只放一份。同一个 ID 出现多份时，只会加载其中一份，其余的会在日志里报重复错误。

Echo 没有加载？没关系，先打开日志。重点看元数据、入口导入和依赖这三类提示，通常很快就能找到是哪一块还没准备好。

## 在 QQ 中验证

在 C2C 私聊里直接发送下面的消息，或者在群聊里 @机器人 后发送：

```text
/echo Hello world
```

群里通常只有 @机器人 的消息才会推送给机器人。开头的这个提及会在匹配命令前去掉。

发送之后，逐项确认下面这些现象：

- [ ] 机器人回复 `Hello world`。
- [ ] `/echo Hello world` 保留 `Hello world` 里的空格。
- [ ] 发送 `/botqraft`，列表中出现 `/echo`，说明文字是当前来源的语言。
- [ ] `/botqraft help` 只展示内置的 BotQraft 运维命令。
- [ ] 群聊和 C2C 私聊都能用。这是因为 Builder 和帮助登记都用了默认的 `('group', 'c2c')`。

Echo 的回调用 `source.reply(...)` 回复，这条回复会作为被动回复关联到原消息上。更多来源字段见[注册命令](commands.md)，回复规则见[回复消息](reply.md)。

## 扩展 Echo

想了解更多命令细节？[命令树](command-tree.md)能帮你给命令添加固定子命令、参数约束和权限检查。想给命令补充短描述，或者查看平台面板状态？读[帮助](help.md)。想把插件改成目录或压缩格式？读[插件格式](plugin-format.md)。

接下来，读[插件是怎么运行的](basic.md)，看看 Echo 背后框架做了什么。
