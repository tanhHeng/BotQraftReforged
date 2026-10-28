# 框架结构

这一页讲 BotQraft 源码分成哪些部分，以及一次启动会依次经过哪些环节。读完这一页，你能判断改一个功能该动哪个子包。

`botqraft/` 是框架本体。它不启动 MCDR 宿主进程，而是复用 MCDR 的插件、命令树、权限和翻译代码，把运行宿主换成 QQ。
`botqraft/__init__.py` 只导出 `__version__`，导入这个包时不会创建任何文件、线程或网络连接。

## 子包职责

| 路径                       | 职责                                                                                                                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `botqraft/api/`            | 插件的公开接口层，按用途分成 `types`、`command`、`event`、`qtext`、`exception`、`decorator`、`utils`，`api.all` 汇总导出。插件只从这一层导入。                         |
| `botqraft/bootstrap.py`    | 部署文件准备：写默认 `config.yml` 与 `permissions.yml`，创建插件、数据与日志目录。它不创建 Runtime，也不连接 QQ。                                                      |
| `botqraft/config.py`       | 配置模型与读写。`Config` 保存 appid、secret、语言、插件目录、收件日志开关、控制台选项、调试开关、网关 intents、HTTP 超时与权限模式，复用 MCDR 的 YAML 合并与保存逻辑。 |
| `botqraft/runtime.py`      | 运行时本体。创建并串联各管理器，驱动启动、运行与停止，对外提供 `is_ready()`、`exit()` 等状态查询。                                                                     |
| `botqraft/runtime_args.py` | `RuntimeArgs` 数据类，携带部署动作与配置文件路径。                                                                                                                     |
| `botqraft/state.py`        | `RuntimeState` 状态枚举。                                                                                                                                              |
| `botqraft/cli/`            | 命令行入口与各子命令的实现。                                                                                                                                           |
| `botqraft/command/`        | 命令注册与执行（`CommandManager`），以及命令来源（`QQCommandSource`、`ConsoleSource`）。                                                                               |
| `botqraft/event/`          | 平台事件解析与调用：`EventParser`、`EventDispatcher`、`QQEvent`、`QQInteraction`。                                                                                     |
| `botqraft/message/`        | 消息数据、用户与场景、收件对象、发送器、发送回执，以及 `qtext/` 下的文本、Markdown 与键盘。                                                                            |
| `botqraft/network/`        | QQ 传输层：访问令牌、HTTP 客户端、网关客户端、独立网络循环，以及传输层异常。                                                                                           |
| `botqraft/panel/`          | 帮助驱动的群聊与 C2C 全局面板同步。                                                                                                                                    |
| `botqraft/permission/`     | 权限列表与最高等级查询，以及默认权限策略。                                                                                                                             |
| `botqraft/plugin/`         | 插件管理：管理器、注册表、工厂、`type/` 插件类型、`meta/` 元数据、`si/` 服务接口、`builtin/` 内置插件，以及生命周期事件定义。                                          |
| `botqraft/executor/`       | 同步与异步任务执行器，以及控制台输入处理。                                                                                                                             |
| `botqraft/logging/`        | 日志器：轮转、凭据脱敏与颜色格式。                                                                                                                                     |
| `botqraft/compatibility/`  | 本地能力探测，以及按版本缓存的能力检查。                                                                                                                               |
| `botqraft/constants/`      | 版本号 `core_constant.VERSION` 与插件文件名常量。                                                                                                                      |
| `botqraft/resources/`      | 打包资源：默认配置、默认权限与内置语言文件。                                                                                                                           |

表格之外还有三个支撑子包：`translation/` 负责翻译查找与延迟文本，`preference/` 保存用户偏好与已见过的 C2C 用户，`utils/` 放序列化、异常与 Future 辅助函数。

`botqraft/plugin/_native.py` 把 MCDR 2.14.4 的函数绑定到 BotQraft 的子类上，不改动 MCDR 自己的类或全局变量。

## 一次启动的完整顺序

### 1. 进程入口

装好之后，你可以用 `botqraft` 命令，也可以用 `python -m botqraft`，两者都会进入 `botqraft/entrypoint.py` 的 `entrypoint()`。
它调用 `botqraft.cli.cli_entry.cli_dispatch()`，再把返回码交给 `SystemExit`。
按下 Ctrl+C 时返回码是 130；遇到其他异常时，会向标准错误打印 `BotQraft: <错误>`，返回码为 1。

### 2. 命令行解析

`cli_dispatch()` 用 `argparse` 解析子命令：

| 子命令            | 作用                                                     |
| ----------------- | -------------------------------------------------------- |
| `init`            | 创建缺失的部署文件与目录，不连接 QQ                      |
| `gen-default`     | 用内置默认值覆盖指定的配置与权限文件                     |
| `version`         | 打印版本号                                               |
| `start`           | 启动运行时，可选 `--auto-init` 与 `--check-capabilities` |
| `pack`            | 按 MCDR 归档约定打包目录插件                             |
| `reformat-config` | 校验并重排配置文件，不启动 QQ                            |

`init`、`gen-default` 与 `start` 都接受 `--config` 与 `--permission`，用来指定配置文件路径，默认是 `config.yml` 与 `permissions.yml`。
不带子命令时，按 `start` 处理。
各子命令的实现都在 `botqraft/cli/`，`start` 最终调用 `Runtime(args).run()`。

### 3. 部署准备

`Runtime.start()` 先做四件事：

1. 调用 `bootstrap.prepare_environment()`。它要求配置文件与权限文件已经存在；如果启动时加了 `--auto-init`，就先补写默认文件与目录。
2. 给日志器挂上 `logs/botqraft.log` 文件输出，并加上凭据脱敏过滤器。
3. 用 `ConfigManager` 读取并校验配置。
4. 确认 appid 与 secret 不为空，再调用 `compatibility.capability_checker.check_capabilities()` 做本地能力检查。

能力检查在独立子进程里运行 `python -m botqraft.compatibility.probes`，结果按 BotQraft 与 MCDR 版本缓存在 `config/botqraft/capabilities.json`。
命中缓存的版本会直接跳过检查；加上 `--check-capabilities` 则会忽略缓存，强制重跑。

### 4. 本地初始化与插件加载

`Runtime.start_local()` 负责不涉及网络的那一半启动：

1. `initialize_local()` 依次创建 `ConfigManager`、`TranslationManager`、`PermissionManager`、`PreferenceManager`、`KnownUserStore`、`QQServerInterface`、`PluginManager`、`CommandManager`、两个任务执行器、`NetworkLoop`、`ApiClient`、`GatewayClient`、`MessageSender`、`PanelSynchronizer` 与 `EventDispatcher`。
2. 状态置为 `STARTING`，并确认进程内只有这一个运行时；第二个实例会抛出 `RuntimeError`。
3. 启动同步与异步任务执行器。
4. 状态置为 `PLUGIN_LOADING`，`register_builtin_plugins()` 载入 `CorePlugin` 与 `PythonPlugin` 两个内置插件。
5. `load_all_plugins()` 按依赖顺序刷新全部启用的插件。插件发现、依赖解析与批量加载用的都是 MCDR 的算法。

### 5. 网络阶段

`NetworkLoop.start()` 起一个名为 `Network` 的线程，里面跑独立的 asyncio 事件循环。之后所有 HTTP 与网关协程都提交到这个循环执行。

接着按顺序推进：

1. `api_client.start()` 建立 HTTP 会话，状态置为 `PANEL_REBUILDING`。
2. `panel_synchronizer.rebuild()` 重建帮助面板。
3. 状态置为 `CONNECTING`，`gateway.start()` 连接 QQ 网关并等待首次 READY，最长等 60 秒（`GatewayClient.READY_TIMEOUT`）。

### 6. 达到 READY

网关收到 `READY` 后，`GatewayClient` 把自身状态置为 `READY`，并结束启动等待。
`Runtime` 随即把状态置为 `READY`，调用一次 `PluginEvents.BOTQRAFT_START`，再记录一行 `BotQraft READY`。
从这时起，`server.is_ready()` 才为真。

### 7. 运行与停止

启动成功后，`run()` 会创建控制台处理器。只要配置里没有把 `disable_console_thread` 设为 `true`，它还会启动控制台线程。
主线程每 0.2 秒检查一次退出请求，同时监视网关是否进入不可恢复的 `FAILED` 状态。

`stop()` 按下面的顺序收尾：

1. 停止控制台，关闭发送器。
2. 若本次曾达到 READY，调用一次 `PluginEvents.BOTQRAFT_STOP`。
3. 逐个卸载常规插件。
4. 停止同步执行器并等待线程结束。正常情况下最多等 600 秒，中断时最多等 10 秒。
5. 停止异步执行器。
6. 关闭网关、面板与 HTTP 客户端。
7. 释放单运行时标记，状态置为 `STOPPED`。如果此前失败过，则置为 `FAILED`。

插件不要直接调用 `stop()`，因为 `stop()` 无法等待它自己所在的执行器线程。在插件回调里，请用 `server.exit()` 请求退出。

## 运行时状态

`RuntimeState` 的取值按出现顺序是：

| 状态               | 含义               |
| ------------------ | ------------------ |
| `CREATED`          | 已创建，尚未启动   |
| `STARTING`         | 正在初始化本地服务 |
| `PLUGIN_LOADING`   | 正在加载插件       |
| `PANEL_REBUILDING` | 正在重建帮助面板   |
| `CONNECTING`       | 正在连接 QQ 网关   |
| `READY`            | 网关与运行时都就绪 |
| `STOPPING`         | 正在停止           |
| `STOPPED`          | 已停止             |
| `FAILED`           | 启动或运行失败     |

## 事件从平台到插件

平台推来的每条数据都走同一条路：

```text
网关读取消息
  → EventDispatcher.submit_payload()
  → EventParser.parse()
  → QQEvent / QQMessageReceived / QQInteraction
  → 同步任务执行器
  → EventDispatcher.process()
  → 插件监听器
```

`EventParser` 认识三类收件事件（群 @、群消息、C2C 消息）和交互事件，其余类型作为通用事件，保留原始数据。
模型解析失败时也不会丢弃数据，而是标记 `model_parse_failed` 并记录一条警告。

`process()` 依次做四件事：

1. 按 `log_received_messages` 决定是否打印收件日志。
2. 记录 C2C 用户。
3. 由 `MessageReactor` 执行匹配的命令。
4. 依次调用 `QQ_EVENT`、`MESSAGE`、`GROUP_MESSAGE`，以及事件类型 id 对应的监听器。

## 线程模型

| 线程           | 运行什么                                              |
| -------------- | ----------------------------------------------------- |
| 主线程         | 启动、状态推进与退出监视                              |
| `Network` 线程 | 网络循环自己的 asyncio 事件循环，所有 HTTP 与网关协程 |
| 同步执行器线程 | 事件处理、命令执行与多数插件回调                      |
| 异步执行器线程 | 插件提交的异步任务                                    |
| 控制台线程     | 交互式控制台输入与补全，可用配置关闭                  |

插件回调大多运行在同步执行器线程上，所以在回调里长时间阻塞会拖慢事件处理。需要等待的活儿交给异步执行器，具体做法见[后台任务与卸载](../plugin-dev/tasks.md)。

接下来，按[本地开发与验证](setup.md)把源码跑起来。
