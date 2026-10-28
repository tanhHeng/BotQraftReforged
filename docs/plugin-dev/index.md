# 插件开发

这一节会带你从零开始写出一个能跑的插件，然后按需要学会命令、回复、按钮、翻译、数据存储和后台任务。

BotQraft 独立运行在 QQ 机器人上，并沿用了 MCDReforged（MCDR）那套久经考验的插件系统。没用过 MCDR 也没关系，按下面的新手路线从头读就行。用 AI agent 写插件的话，先看 [agent 路线](#agent-路线)；用过 MCDR 的话，可以直接走 [MCDR 开发者路线](#mcdr-开发者路线)。

## agent 路线

想让 Codex、Claude Code 这类 AI agent 替你写插件？三步就够：

1. 按[第一个插件](./first-plugin.md)装好实例，确认 Echo 能在 QQ 里回话。agent 改完代码后，要靠这个实例来验证。
2. 把[用 AI agent 开发插件](./agents.md)里的模板存成插件项目根目录的 `AGENTS.md`，填上插件 ID。
3. 像文档各页开头的“场景”那样把需求讲具体：什么命令、在群聊还是私聊、回复长什么样。agent 写完后，你在 QQ 里亲自试一遍。

## 新手路线

不用一次读完所有页面。先读完前两组，你就能写出带命令、会回复的插件。后面的内容等用到时再来翻；每一页都能单独读，读完就能动手。

### 一、先跑起来

1. [第一个插件](./first-plugin.md) — 复制一段代码，装进实例，在 QQ 里发条消息看到回复。
2. [插件是怎么运行的](./basic.md) — 跑通之后，看看框架在什么时候调用你的代码。

### 二、命令与回复

3. [注册命令](./commands.md) — 用 `SimpleCommandBuilder` 注册带参数的命令。
4. [回复消息](./reply.md) — 回复触发命令的消息，并拿到发送结果。
5. [帮助消息与指令面板](./help.md) — 让命令出现在帮助列表和 QQ 指令面板里。
6. [权限系统](./permissions.md) — 决定谁能执行命令。
7. [复杂命令：命令树](./command-tree.md) — `SimpleCommandBuilder` 不够用时，再用节点搭更细致的结构。

### 三、不用命令也能响应

8. [监听消息与事件](./events.md) — 接住群聊、私聊消息和按钮交互。
9. [读取消息内容](./message-format.md) — 从事件里取出正文、用户身份和会话信息。
10. [主动发送、引用与撤回](./sending.md) — 不等用户开口，主动发出消息，引用或撤回已有消息。
11. [发送图片、视频和文件](./media.md) — 回复或主动发送媒体消息。

### 四、让消息更好看

12. [Markdown 消息与文本交互](./markdown.md) — 用 Markdown 排版，点一下就提及用户或填入输入框。
13. [按钮：键盘与点击响应](./interactions.md) — 在消息下面挂按钮，并处理用户的点击。
14. [多语言与用户偏好](./translation.md) — 让插件文案跟随用户语言切换。

### 五、插件工程

15. [插件数据与打包资源](./data.md) — 读写插件自己的数据目录，并读取打包资源。
16. [后台任务与卸载](./tasks.md) — 启动后台任务，并在卸载时干净退出。
17. [元数据](./metadata.md) — 给插件起个稳定的 ID，声明版本和依赖。
18. [插件格式、打包与发布](./plugin-format.md) — 把单文件插件改成目录或压缩包，打包分发。

### 六、参考与示例

19. [API 索引](./api.md) — 按模块查找公开接口。
20. [今日人品示例](./jrrp-plugin.md) — 读一个完整插件的实现，照着自己的需求改。
21. [用 AI agent 开发插件](./agents.md) — 给 Codex、Claude Code 这类 agent 准备一份 `AGENTS.md`，让它按 BotQraft 的规矩写插件。

## MCDR 开发者路线

命令节点、插件元数据、生命周期和打包格式都沿用 MCDR，你熟悉的写法大多能直接用。需要重新学的是 QQ 这一侧：消息怎么进来、身份怎么表示、回复怎么发出去。建议按这个顺序读：

1. [第一个插件](./first-plugin.md) — 确认一个最小插件在 BotQraft 里跑起来。
2. [插件是怎么运行的](./basic.md) — 对照 MCDR 的生命周期，留意 `on_botqraft_start` / `on_botqraft_stop` 和两种 `server` 接口的区别。
3. [注册命令](./commands.md) — `SimpleCommandBuilder` 和命令树与 MCDR 一致，重点看 `QQCommandSource` 和 `scope`。
4. [回复消息](./reply.md)、[主动发送、引用与撤回](./sending.md) — QQ 的被动回复有有效期，主动发送要指定群或私聊目标。
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
