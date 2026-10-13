# 框架结构

这一页讲 BotCraft 源码分成哪些部分，以及一次启动会依次经过哪些环节。读完你能判断改一个功能该动哪个子包。

`botcraft/` 是框架本体。它不启动 MCDR 宿主进程，而是复用 MCDR 的插件、命令树、权限和翻译代码，把运行宿主换成 QQ。
`botcraft/__init__.py` 只导出 `__version__`，导入这个包不会创建文件、线程或网络连接。

## 子包职责

| 路径                       | 职责                                                                                                                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `botcraft/api/`            | 插件的公开接口层，按用途分成 `types`、`command`、`event`、`qtext`、`exception`、`decorator`、`utils`，`api.all` 汇总导出。插件只从这一层导入。                         |
| `botcraft/bootstrap.py`    | 部署文件准备：写默认 `config.yml` 与 `permissions.yml`，创建插件、数据与日志目录。它不创建 Runtime，也不连接 QQ。                                                      |
| `botcraft/config.py`       | 配置模型与读写。`Config` 保存 appid、secret、语言、插件目录、收件日志开关、控制台选项、调试开关、网关 intents、HTTP 超时与权限模式，复用 MCDR 的 YAML 合并与保存逻辑。 |
| `botcraft/runtime.py`      | 运行时本体。创建并串联各管理器，驱动启动、运行与停止，对外提供 `is_ready()`、`exit()` 等状态查询。                                                                     |
| `botcraft/runtime_args.py` | `RuntimeArgs` 数据类，携带部署动作与配置文件路径。                                                                                                                     |
| `botcraft/state.py`        | `RuntimeState` 状态枚举。                                                                                                                                              |
| `botcraft/cli/`            | 命令行入口与各子命令的实现。                                                                                                                                           |
| `botcraft/command/`        | 命令注册与执行（`CommandManager`），以及命令来源（`QQCommandSource`、`ConsoleSource`）。                                                                               |
| `botcraft/event/`          | 平台事件解析与调用：`EventParser`、`EventDispatcher`、`QQEvent`、`QQInteraction`。                                                                                     |
| `botcraft/message/`        | 消息数据、用户与场景、收件对象、发送器、发送回执，以及 `qtext/` 下的文本、Markdown 与键盘。                                                                            |
| `botcraft/network/`        | QQ 传输层：访问令牌、HTTP 客户端、网关客户端、独立网络循环，以及传输层异常。                                                                                           |
| `botcraft/panel/`          | 帮助驱动的群聊与 C2C 全局面板同步。                                                                                                                                    |
| `botcraft/permission/`     | 权限列表与最高等级查询，以及默认权限策略。                                                                                                                             |
| `botcraft/plugin/`         | 插件管理：管理器、注册表、工厂、`type/` 插件类型、`meta/` 元数据、`si/` 服务接口、`builtin/` 内置插件，以及生命周期事件定义。                                          |
| `botcraft/executor/`       | 同步与异步任务执行器，以及控制台输入处理。                                                                                                                             |
| `botcraft/logging/`        | 日志器：轮转、凭据脱敏与颜色格式。                                                                                                                                     |
| `botcraft/compatibility/`  | 本地能力探测，以及按版本缓存的能力检查。                                                                                                                               |
| `botcraft/constants/`      | 版本号 `core_constant.VERSION` 与插件文件名常量。                                                                                                                      |
| `botcraft/resources/`      | 打包资源：默认配置、默认权限与内置语言文件。                                                                                                                           |

另有三个支撑子包。`translation/` 负责翻译查找与延迟文本，`preference/` 保存用户偏好与已见过的 C2C 用户，`utils/` 放序列化、异常与 Future 辅助函数。

`botcraft/plugin/_native.py` 把 MCDR 2.14.4 的函数绑定到 BotCraft 的子类上，不改动 MCDR 自己的类或全局变量。

## 一次启动的完整顺序

### 1. 进程入口

装好后可以用 `botcraft` 命令，也可以用 `python -m botcraft`，两者都进入 `botcraft/entrypoint.py` 的 `entrypoint()`。
它调用 `botcraft.cli.cli_entry.cli_dispatch()`，把返回码交给 `SystemExit`。
按下 Ctrl+C 时返回码是 130。其他异常会向标准错误打印 `BotCraft: <错误>`，返回码为 1。

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
不带子命令时也按 `start` 处理。
各子命令的实现都在 `botcraft/cli/`，`start` 最终调用 `Runtime(args).run()`。

### 3. 部署准备

`Runtime.start()` 先做四件事：

1. 调用 `bootstrap.prepare_environment()`。它要求配置文件与权限文件已存在，除非启动时选了 `--auto-init`，此时先补写默认文件与目录。
2. 给日志器挂上 `logs/botcraft.log` 文件输出，并加上凭据脱敏过滤器。
3. 用 `ConfigManager` 读取并校验配置。
4. 检查 appid 与 secret 非空，再调用 `compatibility.capability_checker.check_capabilities()` 做本地能力检查。

能力检查在独立子进程里运行 `python -m botcraft.compatibility.probes`，结果按 BotCraft 与 MCDR 版本缓存在 `config/botcraft/capabilities.json`。
缓存命中的版本会直接跳过检查，`--check-capabilities` 则忽略缓存强制重跑。

### 4. 本地初始化与插件加载

`Runtime.start_local()` 负责不涉及网络的那一半启动：

1. `initialize_local()` 依次创建 `ConfigManager`、`TranslationManager`、`PermissionManager`、`PreferenceManager`、`KnownUserStore`、`QQServerInterface`、`PluginManager`、`CommandManager`、两个任务执行器、`NetworkLoop`、`ApiClient`、`GatewayClient`、`MessageSender`、`PanelSynchronizer` 与 `EventDispatcher`。
2. 状态置为 `STARTING`，并检查进程内只存在一个运行时。第二个实例会抛出 `RuntimeError`。
3. 启动同步与异步任务执行器。
4. 状态置为 `PLUGIN_LOADING`，`register_builtin_plugins()` 载入 `CorePlugin` 与 `PythonPlugin` 两个内置插件。
5. `load_all_plugins()` 按依赖顺序刷新全部启用的插件。插件发现、依赖解析与批量加载沿用 MCDR 的算法。

### 5. 网络阶段

`NetworkLoop.start()` 起一个名为 `Network` 的线程，里面跑独立的 asyncio 事件循环。之后所有 HTTP 与网关协程都提交到这个循环执行。

接着按顺序推进：

1. `api_client.start()` 建立 HTTP 会话，状态置为 `PANEL_REBUILDING`。
2. `panel_synchronizer.rebuild()` 重建帮助面板。
3. 状态置为 `CONNECTING`，`gateway.start()` 连接 QQ 网关并等待首次 READY，最长等 60 秒（`GatewayClient.READY_TIMEOUT`）。

### 6. 达到 READY

网关收到 `READY` 后，`GatewayClient` 把自身状态置为 `READY`，并结束启动等待。
`Runtime` 随即把状态置为 `READY`，调用一次 `PluginEvents.BOTCRAFT_START`，再记录一行 `BotCraft READY`。
从这时起 `server.is_ready()` 才为真。

### 7. 运行与停止

启动成功后 `run()` 创建控制台处理器并启动控制台线程，除非配置里关掉了 `disable_console_thread`。
主线程每 0.2 秒检查一次退出请求，同时监视网关是否进入不可恢复的 `FAILED` 状态。

`stop()` 按下面的顺序收尾：

1. 停止控制台，关闭发送器。
2. 若本次曾达到 READY，调用一次 `PluginEvents.BOTCRAFT_STOP`。
3. 逐个卸载常规插件。
4. 停止同步执行器并等待线程结束。中断时最多等 10 秒，正常最多等 600 秒。
5. 停止异步执行器。
6. 关闭网关、面板与 HTTP 客户端。
7. 释放单运行时标记，状态置为 `STOPPED`。此前失败过则置为 `FAILED`。

插件不要直接调用 `stop()`。在插件回调里请用 `server.exit()` 请求退出，`stop()` 无法等待自己所在的执行器线程。

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

`EventParser` 认识三类收件事件（群 @、群消息、C2C 消息）和交互事件，其余类型按通用事件保留原始数据。
模型解析失败时不会丢弃数据，而是标记 `model_parse_failed` 并记录警告。

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

插件回调多数运行在同步执行器线程上，所以在回调里做长时间阻塞会拖慢事件处理。需要等待的活儿交给异步执行器，具体做法见[后台任务与卸载](../plugin-dev/tasks.md)。

接下来，按[本地开发与验证](setup.md)把源码跑起来。
