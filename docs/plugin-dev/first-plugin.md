# 第一个插件

读完这一页，你会得到一个装好的 Echo 插件。它注册 `/echo <text>`，把收到的文本用原消息关联回复，每一步都可以直接复制。

## 创建插件文件

先初始化实例，并确认实例插件目录是 `plugins/`：

```bash
python -m botqraft init
```

在实例目录创建 `plugins/echo.py`，写入以下内容：

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

这段代码做了三件事。`PLUGIN_METADATA` 让单文件插件可以直接加载。`on_load` 在插件加载时注册命令和帮助。`GreedyText` 把 `/echo Hello world` 的剩余部分当成一个值，交给 `context['text']`。

## 启动并加载

在实例目录填写 QQ 开放平台凭据：

```yaml
appid: "YOUR_APPID"
secret: "YOUR_APP_SECRET"
```

启动实例：

```bash
python -m botqraft
```

看到 `BotQraft READY` 后，插件会随启动加载。已经运行的实例也可以刷新插件：

```text
/botqraft plugin refresh
/botqraft plugin list
```

`/botqraft plugin refresh` 重新扫描插件目录，`/botqraft plugin list` 显示已加载的插件。修改 Echo 之后，执行：

```text
/botqraft plugin reload echo
```

每个插件 ID 只保留一个可加载副本。如果 Echo 没有加载，先打开日志。优先看看元数据、入口导入和依赖这三类提示，通常很快就能找到是哪一块还没准备好。

## 在 QQ 中验证

在群聊或 C2C 私聊发送：

```text
/echo Hello world
```

逐项确认下面的现象：

- [ ] 机器人回复 `Hello world`。
- [ ] `/echo Hello world` 保留 `Hello world` 里的空格。
- [ ] 发送 `/botqraft`，列表中出现 `/echo`，说明文字是当前来源的语言。
- [ ] `/botqraft help` 只展示内置的 BotQraft 运维命令。
- [ ] 群聊和 C2C 私聊都能用，因为 Builder 和帮助登记都用了默认的 `('group', 'c2c')`。

Echo 的回调通过 `source.reply(...)` 使用原消息的被动回复关联。更多来源字段见[命令系统](commands.md)，回复规则见[响应回复](reply.md)。

## 扩展 Echo

接下来，了解[插件事件](events.md)，看看插件怎么收到 QQ 消息。

想了解更多命令细节？[命令树](command-tree.md)能帮你给命令添加固定子命令、参数约束和权限检查。想给命令补充短描述并查看平台面板状态？读[帮助](help.md)。想把插件改成目录或压缩格式？读[插件格式](plugin-format.md)。
