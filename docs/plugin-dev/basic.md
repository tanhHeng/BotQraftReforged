# 插件是怎么运行的

> **场景**：Echo 已经能回话了，可我还不清楚：插件放进 `plugins/` 之后，框架什么时候调用我的代码？重载插件时，我开的后台任务又该在哪里停掉？

跑通 Echo 之后，我们来看看它背后发生了什么。给 BotQraft 添加新功能，其实就是写一个 Python 文件，放进 `plugins/` 目录。在这个文件里，你声明一下"我是谁"（元数据），再告诉框架"在什么时候做什么"（回调函数），剩下的交给框架就好。

BotQraft 独立运行，以 QQ 机器人作为运行环境。它沿用了 MCDR 那套久经考验的插件系统，所以如果你用过 MCDR，会觉得很熟悉。

## 最小的插件长什么样

来看一个最小的插件。把下面的代码保存成 `plugins/hello.py`：

```python
from types import ModuleType

from botqraft.api.types import QQPluginServerInterface

PLUGIN_METADATA = {
    'id': 'hello',
    'version': '1.0.0',
}


def on_load(server: QQPluginServerInterface, prev_module: ModuleType | None) -> None:
    server.logger.info('Hello plugin loaded')
```

这就能用了。`PLUGIN_METADATA` 告诉框架这个插件是谁；`on_load` 是框架加载插件时会调用的函数；`server` 是你和框架沟通的"管道"。

## 框架怎么找到并加载你的插件

框架在启动时扫描实例的 `plugins/` 目录，或者 `config.yml` 里 `plugin_directories` 列出的其他目录。之后它不会定时自动扫描，需要你用命令让它重新扫描。

框架能识别三种形式：单个 `.py` 文件、带 `botqraft.plugin.json` 的文件夹，以及压缩包（`.mcdr`、`.pyz`）。

同一个插件 ID 只会加载一份。重复的 ID 会在日志里报错并被跳过，而且哪一份先被扫描到并不固定。所以别在插件目录里放同一个插件的多个副本。

启动实例的时候，框架会读取每个插件的元数据，导入代码，然后按顺序触发生命周期函数。实例启动后，你还可以用命令重新扫描目录，或者重载单个插件。

完整的安装和测试步骤见[第一个插件](first-plugin.md)。想了解三种插件形式有什么区别，可以看[插件格式](plugin-format.md)。

## 插件的生命周期

框架会在你的入口模块里寻找下面这些约定好名字的函数。找到了，就在对应的时机调用它们：

| 函数名                         | 什么时候被调用                                 | 你可以在这里做什么                                                                                                 |
| ------------------------------ | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `on_load(server, prev_module)` | 插件加载或重载时                               | 注册命令、帮助文本、事件监听和多语言翻译。首次加载时 `prev_module` 是 `None`，重载时可以用它来恢复上次保存的状态。 |
| `on_botqraft_start(server)`    | 启动时 QQ 连接首次就绪后，触发一次             | 可以开始主动发消息了，连接已经稳定可用。                                                                           |
| `on_botqraft_stop(server)`     | 实例开始关闭时（仅当之前成功进入过 READY）     | 收拾你的东西准备说再见。这时实例已经在关闭，不能再发消息，发送会抛出 `NotReadyError`。                             |
| `on_unload(server)`            | 插件卸载时、重载时旧版本退出时，以及实例关闭时 | 停止后台任务、关闭连接、释放资源。                                                                                 |

几个细节值得注意：

- `on_load` 只表示"你的代码成功加载了"，不代表 QQ 连接已经就绪。如果你在 `on_load` 里需要发消息，先用 `server.is_ready()` 检查一下。
- `on_botqraft_start` 只在实例真正启动的时候触发一次。如果你后来热加载或重载了某个插件，这个函数不会再被调用。所以热加载时需要做的初始化，放在 `on_load` 里比较安全。
- 框架会自动清理你注册的命令、帮助、事件和翻译。但你自己创建的后台任务、计时器、网络连接，需要你在 `on_unload` 里手动收拾干净。
- 特别提醒：如果插件在导入阶段（模块顶层代码）就出错，或者依赖检查没通过，插件根本不会进入可用状态，`on_load` 和 `on_unload` 都不会被调用。所以别在模块顶层创建后台任务或连接，把它们放进 `on_load`。
- `on_load` 自己抛异常时，框架只记录日志，插件仍然保持加载，抛异常之前注册的内容也会保留。之后卸载时，框架照常调用 `on_unload`。所以 `on_unload` 要能应付初始化只做了一半的情况。

想看事件和消息怎么处理，读[监听消息与事件](events.md)。想知道后台任务怎么优雅地停止，看[后台任务与卸载](tasks.md)。

## 你能用到的工具和接口

从 `botqraft.api` 这几个子模块里导入你需要的东西：

```python
from botqraft.api.types import QQPluginServerInterface
from botqraft.api.command import SimpleCommandBuilder, QQCommandSource
```

各个模块里大致有这些：

| 模块                     | 里面有什么                               |
| ------------------------ | ---------------------------------------- |
| `botqraft.api.types`     | 服务接口、QQ 数据类型。                  |
| `botqraft.api.command`   | 命令来源、参数节点、命令构建器。         |
| `botqraft.api.event`     | 插件事件、QQ 消息和交互类型。            |
| `botqraft.api.qtext`     | 纯文本、Markdown、按钮键盘、图片等媒体。 |
| `botqraft.api.exception` | 异常类型。                               |

插件生命周期和事件回调里拿到的 `server` 是 `QQPluginServerInterface`。它绑定了当前插件。注册命令、获取插件数据目录、写日志……总之，凡是和你这个插件相关的事，都找它。

命令回调里拿到的是 `QQCommandSource`。注意，`source.get_server()` 返回的是实例级的 `QQServerInterface`，和上面的 `server` 不是一个东西。需要注册功能、访问插件数据目录或打包资源时，还是要用生命周期回调传给你的那个 `server`。要回复用户的消息？直接用 `source.reply(...)` 最方便。

想看完整的 API 列表，可以查[API 索引](api.md)。消息来源和回复的细节在[回复消息](reply.md)里。

## 接下来

仓库的 [`example_plugins/`](https://github.com/tanhHeng/BotQraftReforged/tree/main/example_plugins) 里放着几个现成的插件示例，复制到你的 `plugins/` 目录就能直接用。想看一个功能更完整的插件？[今日人品插件](jrrp-plugin.md)里有命令、Markdown、按钮、多语言翻译，还有数据存储。

下一步，阅读[注册命令](commands.md)，给插件加上自己的命令。
