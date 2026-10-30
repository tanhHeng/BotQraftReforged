# 插件是怎么运行的

> **场景**：Echo 已经能回话了，可我还不清楚：插件放进 `plugins/` 之后，框架什么时候调用我的代码？重载插件时，我开的后台任务又该在哪里停掉？

Echo 跑通了。这一页我们掀开盖子，看看框架从发现插件到卸载插件，都在什么时候调用你的代码。

一个插件，本质上就是插件目录里的一个 Python 文件。文件里只需要做两件事：声明“我是谁”（元数据），再告诉框架“什么时候做什么”（回调函数）。剩下的交给框架。

BotQraft 独立运行在 QQ 机器人上，沿用了 MCDR 的插件系统。用过 MCDR？那这一页你会读得很快。

## 最小的插件长什么样

最小的插件能有多小？把下面的代码保存成 `plugins/hello.py`：

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

就这么几行，已经是一个能用的插件了：

- `PLUGIN_METADATA` 是元数据，告诉框架这个插件是谁；
- `on_load` 是框架加载插件时会调用的函数；
- `server` 是你和框架沟通的“管道”，后面会经常见到它。

## 框架怎么找到并加载你的插件

启动时，框架会扫描插件目录。默认是 `plugins/`；想换地方，改 `config.yml` 里的 `plugin_directories`。

它认得三种形式：

- 单个 `.py` 文件；
- 带 `botqraft.plugin.json` 的文件夹；
- 压缩包（`.mcdr`、`.pyz`）。

找到插件后，框架会读取元数据、导入代码，再按顺序调用生命周期函数，下一节细说。

注意，扫描只在启动时自动做。之后你往目录里放了新插件，框架不会自己发现，需要用命令让它重新扫描；只改了一个插件的话，也可以单独重载它。完整的安装和测试步骤见[第一个插件](first-plugin.md)。

还有个小坑：同一个插件，别在插件目录里放好几份。同一个插件 ID 只会加载一份，其余的会在日志里报错并被跳过。留下的是哪一份？不一定，看谁先被扫描到。

想了解三种插件形式有什么区别，看[插件格式](plugin-format.md)。

## 插件的生命周期

框架会在你的入口模块里找下面这几个约定好名字的函数，找到了，就在对应的时机调用：

| 函数名                         | 什么时候被调用                                       | 你可以在这里做什么                                                                                                 |
| ------------------------------ | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `on_load(server, prev_module)` | 插件加载或重载时                                     | 注册命令、帮助文本、事件监听和多语言翻译。首次加载时 `prev_module` 是 `None`，重载时可以用它来恢复上次保存的状态。 |
| `on_botqraft_start(server)`    | 启动时 QQ 连接首次就绪后，触发一次                   | 连接已经稳定可用，可以开始主动发消息了。                                                                           |
| `on_botqraft_stop(server)`     | 实例开始关闭时（仅当之前进入过 READY，即连接就绪过） | 收拾收拾准备下班。想发条“再见”？来不及了：实例已经在关闭，发送会抛出 `NotReadyError`。                             |
| `on_unload(server)`            | 插件卸载时、重载时旧版本退出时，以及实例关闭时       | 停止后台任务、关闭连接、释放资源。                                                                                 |

第一遍读，先盯住 `on_load` 和 `on_unload` 这一对：一个开张，一个收摊。要主动发消息时，再回来看 `on_botqraft_start`。

下面这几个地方最容易踩坑：

- **想在 `on_load` 里发消息？** 先用 `server.is_ready()` 检查一下。`on_load` 只代表“你的代码加载成功了”，QQ 连接不一定已经就绪；连接就绪后才会触发 `on_botqraft_start`。
- **热加载时要做的初始化，放进 `on_load`。** `on_botqraft_start` 只在实例真正启动时触发一次，之后热加载或重载插件，它都不会再被调用。
- **自己开的东西，自己收拾。** 框架会自动清理你注册的命令、帮助、事件和翻译；但你创建的后台任务、计时器、网络连接，得在 `on_unload` 里手动关掉。
- **后台任务和连接放进 `on_load`，别放在模块顶层。** 如果插件在导入阶段（模块顶层代码）就出错，或者依赖检查没通过，插件根本进不了可用状态，`on_load` 和 `on_unload` 都不会被调用。这时顶层开出去的任务，就没人收拾了。
- **`on_unload` 要能应付“只初始化了一半”。** `on_load` 抛异常时，框架只记录日志，插件仍然保持加载，抛异常之前注册的内容也会保留。之后卸载时，框架照常调用 `on_unload`。

想看事件和消息怎么处理，读[监听消息与事件](events.md)。后台任务具体怎么优雅地停下来，看[后台任务与卸载](tasks.md)。

## 你能用到的工具和接口

插件要用的东西，都从 `botqraft.api` 下面这几个子模块导入：

```python
from botqraft.api.types import QQPluginServerInterface
from botqraft.api.command import SimpleCommandBuilder, QQCommandSource
```

每个模块里大致有这些：

| 模块                     | 里面有什么                               |
| ------------------------ | ---------------------------------------- |
| `botqraft.api.types`     | 服务接口、QQ 数据类型。                  |
| `botqraft.api.command`   | 命令来源、参数节点、命令构建器。         |
| `botqraft.api.event`     | 插件事件、QQ 消息和交互类型。            |
| `botqraft.api.qtext`     | 纯文本、Markdown、按钮键盘、图片等媒体。 |
| `botqraft.api.exception` | 异常类型。                               |

写插件时，你会天天和两个对象打交道。

**`server`**：生命周期和事件回调里拿到的 `server` 是 `QQPluginServerInterface`，绑定的是你这个插件。注册命令、获取插件数据目录、写日志……凡是和你这个插件有关的事，都找它。

**`source`**：命令回调里拿到的是 `QQCommandSource`。要回复用户？直接用 `source.reply(...)` 最方便。

有个地方很容易搞混：`source.get_server()` 返回的是实例级的 `QQServerInterface`，跟上面那个 `server` 不是一回事。注册功能、访问插件数据目录或打包资源，还是要用生命周期回调传给你的那个 `server`。

完整的 API 列表查[API 索引](api.md)，消息来源和回复的细节在[回复消息](reply.md)里。

## 接下来

想直接抄作业？仓库的 [`example_plugins/`](https://github.com/tanhHeng/BotQraftReforged/tree/main/example_plugins) 里有几个现成的插件示例，复制到你的 `plugins/` 目录就能用。想看功能更完整的？[今日人品插件](jrrp-plugin.md)里命令、Markdown、按钮、多语言翻译和数据存储都有。

准备好了，就去[注册命令](commands.md)，给插件加上属于自己的命令。
