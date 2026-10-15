# 基本知识

想象一下，如果你想给 BotQraft 添加新功能，其实就是写一个 Python 文件放进 `plugins/` 目录。在这个文件里，你声明一下"我是谁"（元数据），然后告诉框架"在什么时候做什么"（回调函数），剩下的事情框架会帮你搞定。

BotQraft 独立运行，用 QQ 机器人作为运行环境，并且沿用了 MCDR 那套久经考验的插件系统，所以如果你用过 MCDR，会很熟悉。

## 你的第一个插件长什么样

来看一个最小化的插件代码。保存成 `plugins/hello.py`：

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

这就能用了。`PLUGIN_METADATA` 告诉框架这个插件的身份信息，`on_load` 是框架加载插件时会调用的函数，`server` 是你和框架沟通的"管道"。

## 框架怎么找到并加载你的插件

框架会定期扫描实例的 `plugins/` 目录（或你在配置里指定的其他位置）。无论是单个 `.py` 文件、整个文件夹、还是压缩包（`.mcdr`、`.pyz`），框架都能识别。如果同一个插件 ID 有多份，框架会按优先级选一个。

启动实例的时候，框架会读取每个插件的元数据、导入代码，然后按顺序触发生命周期函数。实例启动后，你还可以用命令重新扫描目录或重载单个插件。

完整的安装和测试步骤详见[第一个插件](first-plugin.md)，想了解三种插件形式的区别可以看[插件格式](plugin-format.md)。

## 插件的生命周期

框架会自动在你的入口模块里寻找这些约定好名字的函数。当它找到的时候，就会在对应的时机调用：

| 函数名                         | 什么时候被调用                     | 你可以在这里做什么                                                                                                 |
| ------------------------------ | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `on_load(server, prev_module)` | 插件加载或重载时                   | 注册命令、帮助文本、事件监听和多语言翻译。首次加载时 `prev_module` 是 `None`，重载时可以用它来恢复上次保存的状态。 |
| `on_botqraft_start(server)`    | QQ 连接建立后启动完成时            | 可以开始主动发消息了，连接已经稳定可用。                                                                           |
| `on_botqraft_stop(server)`     | 实例即将关闭时                     | 停止发送消息，收拾好你的东西准备说再见。                                                                           |
| `on_unload(server)`            | 插件即将卸载时，或重载时旧版本退出 | 停止后台任务、关闭连接、释放资源。                                                                                 |

几个细节值得注意：

- `on_load` 只表示"你的代码成功加载了"，不代表 QQ 连接已经就绪。如果你在 `on_load` 里需要发消息，先用 `server.is_ready()` 检查一下。
- `on_botqraft_start` 只在实例真正启动的时候触发一次。如果你后来热加载或重载了某个插件，这个函数不会再被调用。所以热加载时需要做的初始化，放在 `on_load` 里比较安全。
- 框架会自动清理你注册的命令、帮助、事件和翻译。但是你自己创建的后台任务、计时器、网络连接这些东西，需要在 `on_unload` 里手动收拾干净。
- 特别提醒：如果插件在加载过程中出错了，有可能 `on_unload` 不会被调用。所以初始化代码要防守好——如果中途出异常，要立即释放已经申请的资源，别指望 `on_unload` 来救场。

如果你想看事件和消息怎么处理，可以看[插件事件](events.md)。想知道后台任务怎么优雅地停止，看[后台任务与卸载](tasks.md)。

## 你能用到的工具和接口

从 `botqraft.api` 这几个子模块里导入你需要的东西：

```python
from botqraft.api.types import QQPluginServerInterface
from botqraft.api.command import SimpleCommandBuilder, QQCommandSource
```

简单介绍一下各个模块都有什么：

| 模块                     | 里面有什么                       |
| ------------------------ | -------------------------------- |
| `botqraft.api.types`     | 服务接口、QQ 数据类型。          |
| `botqraft.api.command`   | 命令来源、参数节点、命令构建器。 |
| `botqraft.api.event`     | 插件事件、QQ 消息和交互类型。    |
| `botqraft.api.qtext`     | 纯文本、Markdown、按钮键盘。     |
| `botqraft.api.exception` | 异常类型。                       |

插件生命周期和事件回调里拿到的 `server` 是 `QQPluginServerInterface`。它绑定了当前插件，你用它来注册命令、获取插件数据目录、读日志——总之，凡是和你这个插件相关的事，都找它。

命令回调里拿到的是 `QQCommandSource`。`source.get_server()` 返回的是实例级的 `QQServerInterface`，和上面的 `server` 不是一个东西。如果你需要注册功能、访问插件数据目录或打包资源，还是要用生命周期回调传给你的那个 `server`。回复用户的消息？直接用 `source.reply(...)` 最方便。

想看完整的 API 列表，可以查[API 索引](api.md)。消息来源和回复的细节在[响应事件与回复消息](reply.md)里。

## 动手试试吧

仓库的 [`example_plugins/`](https://github.com/BotQraftReforged/BotQraftReforged/tree/main/example_plugins) 里放着几个现成的插件示例，复制到你的 `plugins/` 目录就能直接用。

想先跑通一条简单命令看看效果，从[第一个插件](first-plugin.md)开始最舒服。

想看一个功能更完整的、真正能用的插件示例，里面有命令、Markdown、按钮、多语言翻译还有数据存储，看看[今日人品插件](jrrp-plugin.md)就有感觉了。

准备好了？下一步是为你的插件写[元数据](metadata.md)。
