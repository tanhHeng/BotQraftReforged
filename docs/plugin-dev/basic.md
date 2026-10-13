# 基本知识

插件就是实例插件目录里的一个 Python 入口模块。你在里面声明元数据、定义回调，框架负责发现它、加载它，并在合适的时机调用你的函数。

BotQraft 独立运行，沿用 MCDR 的命令节点、插件元数据和生命周期，运行宿主是 QQ 机器人。

## 框架如何加载插件

框架默认扫描实例的 `plugins/` 目录，也可以用 `plugin_directories` 指定其他目录。
单文件插件、目录插件和压缩插件都放在这里，每个插件 ID 保留一份可加载副本。

启动实例时，框架读取插件元数据、导入入口模块，再依次触发下面的生命周期回调。
实例运行中，你可以用 `/botqraft plugin refresh` 重新扫描插件目录，或用 `/botqraft plugin reload <id>` 重载单个插件。

安装与验证的完整步骤见[第一个插件](first-plugin.md)，三种插件形态见[插件格式](plugin-format.md)。

## 插件的生命周期

框架自动发现入口模块中约定名称的回调：

| 回调                           | 什么时候触发                      | 适合在这里做什么                                                                                   |
| ------------------------------ | --------------------------------- | -------------------------------------------------------------------------------------------------- |
| `on_load(server, prev_module)` | 插件加载或重载时                  | 登记命令、帮助、事件和翻译。首次加载时 `prev_module` 为 `None`，重载时可以从它迁移上次模块的状态。 |
| `on_botqraft_start(server)`    | 本次实例启动并达到 READY 时       | 提交 QQ 操作，此时连接已经可用。                                                                   |
| `on_botqraft_stop(server)`     | 曾达到 READY 的实例开始正常停止时 | 停止对外提交，准备收尾。                                                                           |
| `on_unload(server)`            | 插件卸载时，包括重载时旧模块退出  | 停止后台工作、发出取消信号并关闭外部资源。                                                         |

`on_load` 只表示插件加载完成，QQ 连接状态请用 `server.is_ready()` 查询。
实例启动事件只在本次实例达到 READY 时触发。
热加载走的是插件加载生命周期，所以把热加载需要的初始化放在 `on_load` 里。

注册的命令、帮助、事件和翻译随插件生命周期自动清除。
插件自己创建的任务、计时器和连接需要你在 `on_unload` 中收尾，加载失败时也一样。

消息与交互回调见[插件事件](events.md)，后台工作的退出方式见[后台任务与卸载](tasks.md)。

## 你能用到的公开接口

从 `botqraft.api` 的子模块导入插件需要的接口：

| 入口                     | 用途                                                            |
| ------------------------ | --------------------------------------------------------------- |
| `botqraft.api.types`     | `QQPluginServerInterface`、`QQServerInterface` 和 QQ 数据类型。 |
| `botqraft.api.command`   | 命令来源、参数节点和命令构建器。                                |
| `botqraft.api.event`     | 插件事件和 QQ 入站事件类型。                                    |
| `botqraft.api.qtext`     | 文本、Markdown 和键盘。                                         |
| `botqraft.api.exception` | 公开异常类型。                                                  |

插件回调收到绑定当前插件的 `QQPluginServerInterface`。用它登记命令、帮助、事件和翻译，并获取日志、数据目录和任务调度服务。

命令回调收到 `QQCommandSource`，它带有原消息的用户、场景和会话。
`source.get_server()` 返回 `QQServerInterface`。
需要插件专属服务时，用插件回调传入的 `server`。

消息内容使用 `str`、`QText`、`QMarkdown` 或延迟翻译文本。
通过公开接口访问框架服务，内部实现交给框架维护。
完整模块列表见[API 索引](api.md)，消息来源与回复见[响应事件与回复消息](reply.md)。

## 动手试试

仓库的 [`example_plugins/`](https://github.com/BotQraftReforged/BotQraftReforged/tree/main/example_plugins) 里有可以直接使用的插件示例，复制到实例的插件目录就能加载。

想先跑通一条命令，就从[第一个插件](first-plugin.md)开始。
想看功能更完整的多插件组合，读[今日人品插件](jrrp-plugin.md)。

接下来，先为插件声明[元数据](metadata.md)。
