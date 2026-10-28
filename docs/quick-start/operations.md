# 日志与运维

读完这一页，你能看懂 BotQraft 的收件日志和诊断日志。
你还会用运维命令管理实例，也知道停机前该备份哪些文件。

本页的命令分成两类：QQ 消息和控制台里用带 `/` 的 `/botqraft` 命令，命令行工具用 `botqraft start` 这样的形式。两者中的 `botqraft` 都可以写成 `python -m botqraft`。

## 检查消息时间偏差

在运维控制台或由超级管理员在 QQ 中执行 `/botqraft diagnose time`，可以查看最近一次合法消息时间戳的观测：平台时间减本机接收时间、观测时间，以及 `normal`、`warning` 或 `error` 等级。没有观测时会显示提示。

平台时间领先本机不超过 5 秒时为 `normal`，超过 5 秒且不超过 15 秒时为 `warning`，超过 15 秒时为 `error`，并拒绝该消息的被动回复。平台时间落后本机归为 `normal`，其中可能包含消息投递延迟；等级仅表示未来时间容差，不代表系统时钟已校准。

每条消息都独立计算偏差。首次获取或刷新 access token 成功后，第一条落入警告区间的消息会记录一行 warning；同一 token 周期内的后续消息继续接受。刷新保留最近观测，非法时间戳也保留上一条合法观测。被动回复有效期仍独立检查，最多为接收后 600 秒，已有投递延迟会扣除。

如果看到 `Platform time ahead` 警告，请先同步运行机器的系统时间，再发送新消息检查结果。这个命令读取 QQ 消息观测，不查询 NTP，也不修改系统时间。

## 收件与诊断日志

日志同时输出到控制台和 `logs/botqraft.log`。
运行提示、异常说明和诊断日志里的硬编码文本使用英文。
帮助和命令反馈等翻译键内容按语言配置输出，也可以是中文。
收到的消息正文保持原文。

### 正常收件日志

`log_received_messages: true` 时，消息部分会呈现为：

```text
[Group:ABCDEF] [User:896C5A] Hello world
[C2C:UVWXYZ] [User:896C5A] Hello|Markdown text|[attachments] {"url":"https://example.org/file"}
```

正文按实际收到的内容拼接。
附件、ARK 和嵌套消息元素用带字段名的 JSON 展示。
记录发生在命令和插件回调之前。
群 AT 消息会去掉前导 ASCII 空格，其他消息保留原正文。

正常收件日志的身份字段按下面的规则生成：

| 字段     | 来源与显示方式                       |
| -------- | ------------------------------------ |
| 群会话   | 原始 `group_openid` 的前六位。       |
| C2C 会话 | 原始 `author.user_openid` 的前六位。 |
| 用户身份 | 原始 `author.id` 的前六位。          |

这些缩写直接显示前六位。字段缺失时显示 `-`，用户身份始终以 `author.id` 为准。
正常收件日志展示会话、用户身份和正文。想查看消息 ID，请用下面的原始响应日志。
换行和控制字符会转义为单行，凭据继续脱敏。

希望关闭正常收件记录，可以设置 `log_received_messages: false`，然后执行：

```text
/botqraft reload config
```

消息处理、异常报告和网关阶段日志继续运行。
网关阶段日志聚焦这几件事：连接地址已取得、READY、停止，以及必要的重连与失败。
每次断线只记一行：断线原因、几秒后重连、这是 READY 之后的第几次尝试。重新 READY 后计数从头开始。
WebSocket 连接完成（含心跳间隔）属于调试级别日志；想查看心跳和详细载荷，请用原始响应日志。Token、Secret、完整网关地址和会话 ID 继续按脱敏规则处理。

### 原始响应日志

排障时，可以显式设置 `debug.raw_response: true`。
英文标记示例：

```text
Raw response [Gateway] {"op":11}
Raw response [HTTP] [send message] [http_code:200] {"id":"message-id"}
```

原始响应日志的记录范围和处理方式如下：

- 网关在解析前记录入站 JSON，覆盖 Hello、READY、消息和 ACK。
- HTTP 在业务校验前记录入站响应体、状态码和操作名。
- JSON 紧凑显示为单行，消息正文的前后空格保持原样。普通文本响应使用转义文本展示。请按这种格式化后的副本阅读排障信息。
- Token、Secret、鉴权字段、`session_id` 和网关地址会脱敏。脱敏只作用于日志展示，业务数据保持原样。
- **原始日志包含完整消息 ID、用户 ID、群 ID 和聊天内容**。这里使用完整身份字段。正常收件日志则使用前六位缩写。
- 这个选项需要独立开启。即使 `debug.all` 已经开启，也请显式设置 `debug.raw_response: true`。

正常正文和富消息也可能包含个人信息。
排障结束后，请关闭原始日志。
分享前逐项审查隐私，再决定哪些内容可以公开。自动脱敏只是审查的辅助。

## 运维命令

群聊、C2C 和运维控制台统一使用带 `/` 的 `/botqraft` 根命令。
发行包的命令行工具则使用 `botqraft start` 这样的形式。

```text
/botqraft
/botqraft help
/botqraft pref
/botqraft pref language set en_us
/botqraft permission list
/botqraft plugin list
/botqraft plugin reload echo
/botqraft reload config
/botqraft reload permission
/botqraft reload preference
/botqraft exit
```

### 查看帮助与插件

`/botqraft` 会输出 BotQraft 版本，以及已登记帮助项的输入框标签。
`/botqraft help` 会输出 BotQraft 自身的这些指令帮助：

- `help`
- `perm/permission`
- `plugin`
- `pref/preference`
- `reload`
- `exit`

两者都使用当前来源的语言。内置面板登记的命令是 `/botqraft`。
权限管理、插件操作、reload 和退出面向超级管理员及运维控制台开放。
超级管理员身份通过 `permission.super_admins` 配置。普通权限等级用于普通权限判定。

`/botqraft plugin list` 使用 MCDR 风格的纯文本分组。
已加载项显示名称和 `id@version`，随后列出已禁用项、待加载插件文件名及数量。
你可以通过名称、插件 ID 和状态找到需要管理的插件。

QQ 来源会收到一条被动回复，语言按用户偏好选择。
控制台也使用自己的偏好语言。

### 操作权限

权限命令可以操作当前消息场景里的用户。
从控制台执行时，请明确指定 `--group`、`--c2c` 或 `-g/--global` 作用域。

C2C 操作的前提是框架已经记录过该用户的真实私聊会话地址。这个地址就是用来定位会话的 OpenID。
请从实际消息取得身份和会话地址，并在对应场景里使用。
权限身份使用真实的 `User.id`，私聊会话地址使用框架记录的真实 OpenID。
昵称只用于展示，身份配置以实际取得的字段为准。

## 备份与停止

维护前，请备份：

- `config.yml`
- `permissions.yml`
- `config/`
- 插件文件

`config/` 保存插件数据、用户语言等实例状态。
尤其在执行 `/botqraft reload preference` 前，请先备份偏好文件。
这个命令对损坏 JSON 使用恢复语义，恢复时可能清空并重写偏好文件。

执行 `/botqraft exit` 可以正常停止实例。
插件自己的后台任务请按[后台任务与卸载](../plugin-dev/tasks.md)完成收尾。

接下来，你可以回到[添加插件](./add-plugins.md)安装第一个插件，或直接进入[插件开发](../plugin-dev/index.md)编写自己的插件。
