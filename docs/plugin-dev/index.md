# 插件开发

此部分将引导你从零开始学会开发一个完善的 BotQraft 插件。

BotQraft 独立运行在 QQ 机器人上，并沿用了 MCDReforged（MCDR）久经考验的插件系统。从来没用过 MCDR ？没关系，让我们一起从零开始。

**选择一条开发路线：**

- **Agent 路线**：如果你希望直接让你的 AI Agent 帮你完成插件开发，那么直接阅读 [Agent 路线](#agent-路线) 即可。复制 AGENTS.md 模板，然后燃烧你的 token ！
- **MCDR 开发者路线**：如果你有 MCDR 开发经验，那么可以直接读 [MCDR 开发者路线](#mcdr-开发者路线) ，快速上手 BotQraft 插件开发。
- **新手路线**：如果你是新手小白，也不想用 AI ，那么按顺序阅读 [新手路线](#新手路线) 即可，我们将从最基础的插件开发知识开始，逐步深入。

## Agent 路线

想让 Codex、Claude Code 这类 AI Agent 替你写插件？只要三步：

1. 按[第一个插件](./first-plugin.md)装好实例，确认 Echo 能在 QQ 里回复消息，用来测试框架、 API 连接是否一切正常。
2. 把[用 AI agent 开发插件](./agents.md)里的模板存成插件项目根目录的 `AGENTS.md`，填上你的插件 ID。
3. 像文档各页开头的“场景”那样，写清需求：有什么命令、在群聊还是私聊触发、回复长什么样…… Agent 写完后，让 Agent Computer Use 你的 QQ ，或者你亲自打开 QQ ，测试你的 Bot 。

## 新手路线

### 一、让我们开始吧！

先来了解一下基本概念和环境搭建：

1. [第一个插件](./first-plugin.md) — 复制一段代码，装进实例，在 QQ 里发条消息看到回复。
2. [插件是怎么运行的](./basic.md) — 跑通之后，看看框架在什么时候调用你的代码。

### 二、命令与回复

~~注册一个命令，回复一条消息，加入一个面板~~

注册一条命令，让插件回复消息，还能验证用户权限，并且把命令加入帮助列表和 QQ 指令面板中：

3. [注册命令](./commands.md) — 用 `SimpleCommandBuilder` 注册带参数的命令。
4. [回复消息](./reply.md) — 回复触发命令的消息，并拿到发送结果。
5. [帮助消息与指令面板](./help.md) — 让命令出现在帮助列表和 QQ 指令面板里。
6. [权限系统](./permissions.md) — 决定谁能执行命令。
7. [复杂命令：命令树](./command-tree.md) — `SimpleCommandBuilder` 不够用时，再用节点搭更细致的结构。

### 三、响应非命令消息

响应除了命令以外的消息、处理消息内容、用户身份、监听指定的事件并回复：

8. [监听消息与事件](./events.md) — 响应群聊、私聊消息和按钮交互。
9. [读取消息内容](./message-format.md) — 从消息事件里读取消息正文、用户身份和会话信息。
10. [主动发送、引用与撤回](./sending.md) — 不等用户开口，主动发出消息，引用或撤回已有消息。

### 四、不同类型的消息

纯文本消息太单调了？想做中英文自动适配？来看看这些：

11. [发送图片、视频和文件](./media.md) — 回复或主动发送媒体消息。
12. [Markdown 消息与文本交互](./markdown.md) — 使用强大的 Markdown 格式，并嵌入可交互文本。
13. [按钮：键盘与点击响应](./interactions.md) — 在消息下面加上“按钮”，并处理用户点击事件。
14. [多语言与用户偏好](./translation.md) — 让插件消息随用户语言偏好切换。

### 五、插件工程

让你的插件更“正规”！

15. [插件数据与打包资源](./data.md) — 读写插件自己的数据目录，并读取打包资源。
16. [后台任务与卸载](./tasks.md) — 启动后台任务，并在卸载时退出。
17. [元数据](./metadata.md) — 给插件定个独一无二的 ID，并标记插件版本，声明依赖项。
18. [插件格式、打包与发布](./plugin-format.md) — 使用更正式的插件格式，并打包分发。

### 六、参考与示例

找不到想要的接口？想看看完整插件的实现？想寻求 AI 的帮助？来这里：

19. [API 索引](./api.md) — 按模块查找公开接口。
20. [今日人品示例](./jrrp-plugin.md) — 读一个完整插件的实现，照着自己的需求改。
21. [用 AI agent 开发插件](./agents.md) — 给 Codex、Claude Code 这类 agent 准备一份 `AGENTS.md`，让它按 BotQraft 的规矩写插件。

## MCDR 开发者路线

BotQraft 的命令节点、元数据、插件周期、打包格式都沿用了 MCDR 的设计，但针对 QQ 机器人进行了适配和优化。只不过`Info`变成了`MessageReceived`，`player`变成了`User`，`reply`的一些参数不同，`tell` `say` `broadcast`变成了`send`。

你需要重新了解消息的接收方式、用户身份的表示方法、会话场景区分和消息的发送机制，建议按如下顺序阅读：

1. [第一个插件](./first-plugin.md) — 确认一个最小插件在 BotQraft 里跑起来。
2. [插件是怎么运行的](./basic.md) — 对照 MCDR 的生命周期，留意 `on_botqraft_start` / `on_botqraft_stop` 和两种 `server` 接口的区别。
3. [注册命令](./commands.md) — `SimpleCommandBuilder` 和命令树与 MCDR 一致，重点看 `QQCommandSource` 和 `scope`。
4. [回复消息](./reply.md)、[主动发送、引用与撤回](./sending.md) — QQ 的被动回复有时间限制，主动发送要指定群或私聊目标。
5. [监听消息与事件](./events.md)、[读取消息内容](./message-format.md) — 用 QQ 事件替代 MCDR 的 `Info` 和服务端输出。
6. [权限系统](./permissions.md)、[多语言与用户偏好](./translation.md) — 权限等级和翻译的结构与原生一致，只是身份换成了 QQ 用户。

迁移时，请逐条对照下面这些差异：

- 以下能力都属于 Minecraft 宿主：Minecraft 服务端进程的启停与执行命令、RCON、服务端信息、服务端处理器与 Info 过滤器注册、MCDR 配置读写。在 BotQraft 里调用它们会抛出 `UnsupportedOperationError`。请把这部分业务改写成 QQ 事件和接口能完成的动作。
- QQ 发送接口接受 `str`、`QText`、`QMarkdown` 等 `QTextBase` 文本，以及媒体消息和延迟翻译文本。原生 `RText` 不在其中，传入会抛出 `TypeError`。请先把它转换成这些公开格式。
- 公共的 `execute_command(command, source)` 只接收本实例真实的 `QQCommandSource`，传入其他来源会抛出 `TypeError`。来源可以从命令回调里拿，也可以从入站消息的 `event.get_command_source()` 取。另外，`get_plugin_command_source()` 会抛出 `UnsupportedOperationError`。
- `QQServerInterface.si()` 需要 BotQraft 正在运行，实例没跑起来时调用会抛出 `RuntimeError`。如果拿不到接口时不想报错，就用 `si_opt()`：没有接口时它返回 `None`。在插件回调里，优先用传进来的 `server`。
- `.mcdr`（以及 `.pyz`）沿用 MCDR 的压缩包格式。不过包里的元数据文件是 `botqraft.plugin.json`，不是 `mcdreforged.plugin.json`，所以原样的 MCDR 插件包会因为找不到元数据而加载失败。迁到 QQ 时，把元数据、输入事件、身份、消息和宿主操作一起改掉。格式与入口见[插件格式、打包与发布](./plugin-format.md)。

---

写完插件后，按[添加插件](../quick-start/add-plugins.md)把它装进运行实例，再到 QQ 里分别在群聊和私聊中看看实际效果。
