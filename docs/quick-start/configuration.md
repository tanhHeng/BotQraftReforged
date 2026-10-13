# 实例配置

读完这一页，你能初始化一个 BotCraft 实例、填好常用配置，并在运维控制台里操作它。

如果你还没装好 BotCraft，请先看[安装 BotCraft](./install.md)。想先跑通最短路径，看[配置并启动](./start.md)。

## 安装与初始化

BotCraft 目前从源码安装。在源码根目录执行：

```bash
python -m pip install .
```

安装渠道目前就是源码仓库，PyPI 发布可用后再改用包名安装。

查询版本时，下面任意一条命令都可以。它们只输出版本信息：

```bash
botcraft --version
python -m botcraft --version
botcraft version
```

本页把命令统一写成 `botcraft init`、`botcraft start`、`botcraft pack` 这种形式。在源码目录里，`python -m botcraft <子命令>` 和它完全等价。

接下来，把运行实例和源码分开存放。在你选定的位置创建一个空目录：

```bash
mkdir botcraft-run
cd botcraft-run
botcraft init
```

`init` 会补齐下面这些文件和目录：

- `config.yml` 和 `permissions.yml`。
- 配置中指定的插件目录。
- `config/botcraft` 和 `logs`。

已有文件保持原样。所有相对路径都以当前工作目录为基准。

打开本实例的 `config.yml`，填入真实的 `appid` 和 `secret`，然后启动：

```bash
botcraft start
```

`python -m botcraft` 和直接运行 `botcraft` 都等价于普通启动。
普通启动的前提是配置文件、权限文件和有效凭据都齐备。
希望启动时先补齐文件，可以显式使用 `botcraft start --auto-init`。连接 QQ 前仍然要填好凭据。

### 自定义文件路径

初始化和启动要用同一组路径参数：

```bash
botcraft init --config settings/config.yml --permission settings/permissions.yml
botcraft start --config settings/config.yml --permission settings/permissions.yml
```

### 启动检查

首次启动会做一次本地兼容性检查。希望强制重新检查，可以执行：

```bash
botcraft start --check-capabilities
```

通过检查后，启动流程才会继续。
检查范围只是本地兼容性。QQ 连接和平台验收属于实际运行阶段。

正式启动会加载插件，重建群聊/C2C 帮助面板，并等待网关进入 READY 状态。
随后，请在 QQ 里实际验证账号权限和平台接口。本地检查通过只说明本机环境可用。

## 常用配置

打开 `config.yml`，按实例需要调整下表字段：

| 字段                      | 默认值与含义                                                                   |
| ------------------------- | ------------------------------------------------------------------------------ |
| `appid` / `secret`        | 空；QQ 开放平台凭据。修改后启动新进程生效。                                    |
| `language`                | `zh_cn`；默认语言，也可使用 `en_us`。用户可以单独设置语言。                    |
| `plugin_directories`      | `[plugins]`；插件搜索目录，相对路径基于实例工作目录。                          |
| `log_received_messages`   | `true`；记录群聊/C2C 收件正文，以及会话与用户 ID 的前六位。支持 reload。       |
| `gateway.intents`         | `[GROUP_AND_C2C_EVENT, INTERACTION]`；可增加 `MESSAGE_AUDIT`。                 |
| `http.timeout`            | `10.0` 秒；填写有限正数。                                                      |
| `permission.mode`         | `mixed`；也支持 `native`、`role`。见[权限说明](../plugin-dev/permissions.md)。 |
| `permission.super_admins` | `[]`；填写真实的 `User.id` 列表。身份以当前场景实际取得的用户 ID 为准。        |
| `advanced_console`        | `true`；MCDR 风格高级输入、Tab 补全、多列候选菜单和参数提示。修改后重启生效。  |
| `disable_console_thread`  | `false`；设为 `true` 时关闭控制台线程。修改后重启生效。                        |
| `disable_console_color`   | `false`；设为 `true` 时关闭控制台颜色。                                        |
| `debug.raw_response`      | `false`；脱敏原始网关 JSON 和 HTTP 响应日志。支持 reload，独立于 `debug.all`。 |

旧配置缺少选项时，BotCraft 会用默认值补齐，首次加载可能写回文件。
已有的有效配置值保持原样。
改过凭据或控制台启动选项后，请重启实例。改过支持 reload 的选项后，可以执行 `/botcraft reload config`。

## 控制台输入与补全

开启 `advanced_console` 后，输入 `/botcraft`，再按 Tab 选择子命令。
继续输入时，可以看到多列候选和参数提示。

- 语言设置会补全当前可用语言。
- 插件 reload/unload 参数会补全已加载插件 ID。
- 多行粘贴会按行提交。
- 日志输出时，正在编辑的命令保持完整。

控制台的补全和执行范围都是内置的 `/botcraft` 运维命令树。
`/echo`、`/jrrp` 等插件命令请从真实的 QQ 消息来源执行。
插件加载、卸载或语言变更后，下一次补全会读取当前状态。

希望使用基本标准输入，可以设置 `advanced_console: false`。
高级菜单由高级输入提供。基本输入使用逐行命令方式。
高级输入初始化失败时，BotCraft 会记录英文错误，并回退到基本输入。

执行 `/botcraft exit`、发送 EOF 或按 Ctrl-C，可以请求停止。
退出流程会唤醒高级输入，并恢复控制台日志输出。

## 覆盖与重排

需要重新生成默认文件，或者整理配置格式时，可以使用：

```bash
botcraft gen-default --config config.yml --permission permissions.yml
botcraft reformat-config -i config.yml -o formatted/config.yml
```

先备份，再根据目的选择命令：

- `gen-default` 会**覆盖两个目标文件**，把已有凭据和权限替换为默认值。
- `reformat-config` 先校验，再按默认模板重排，保留已知配置值。通过校验后才会写入输出。
- 重排输出只保留默认模板认可的字段。遇到未知字段时，会给出英文 warning。需要保留的自定义字段请另行保存。
- 指定 `-o` 可以先输出到新文件，核对后再替换原文件。省略 `-o` 时，输出会覆盖输入文件。

这两个命令只做本地文件操作。插件加载和网关连接由启动流程负责。
选择 `init` 可以补缺并保留已有文件。选择 `gen-default` 可以把文件覆盖为默认内容。

接下来，[日志与运维](./operations.md)介绍怎么查看日志、执行运维命令，以及停机前要备份什么。
