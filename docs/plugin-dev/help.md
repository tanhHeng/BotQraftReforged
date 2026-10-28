# 帮助消息与指令面板

> **场景**：我写好了 `/echo`，想让用户发 `/botqraft` 时能在帮助列表里看到它，还想让 `/echo` 出现在 QQ 的指令面板里。该怎么做？

读完这一页，你能给命令登记帮助文字，让用户在 QQ 里查到它的用法。

在 `on_load` 里调用 `server.register_help_message(...)`，就能为命令登记帮助文字和 QQ 指令面板项。命令树和帮助是分开注册的，互不影响。

帮助有两种入口。**普通帮助列表**是用户发送 `/botqraft` 后看到的文字清单；**指令面板项**则是 QQ 客户端里的按钮入口。插件可以同时登记这两种，它们各有各的用处。

## 登记命令帮助

给 Echo 添加帮助：

```python
server.register_help_message(
    '/echo',
    {'zh_cn': '复述提供的文本', 'en_us': 'Echo the supplied text'},
    scope=('group', 'c2c'),
)
```

把这段代码放在命令注册之后。完整的接口是这样的：

```python
server.register_help_message(
    prefix, message, permission=0,
    scope=('group', 'c2c'), only_admin=False,
)
```

| 参数         | 填写方式                                                              |
| ------------ | --------------------------------------------------------------------- |
| `prefix`     | 命令前缀，用于帮助显示和面板项名称，例如 `/echo`。                    |
| `message`    | 普通字符串（原样显示）、语言字典，或 `server.rtr(...)` 延迟翻译文本。 |
| `permission` | 普通帮助列表所需的最低权限，默认 0。                                  |
| `scope`      | 帮助适用的场景，和命令注册保持一致。                                  |
| `only_admin` | 平台指令面板的管理员点击和操作限制，默认 `False`。                    |

注意，`scope` 和 `only_admin` 只能用关键字参数传入。

在 QQ 里发送 `/botqraft`，就能看到当前来源可见的插件帮助，也就是前面说的普通帮助列表。而 `/botqraft help` 展示的是内置运维命令的目录。

普通帮助按发起查询的用户的语言解析；QQ 指令面板则在同步时按实例配置的语言解析。需要用翻译文件的话，读[多语言与用户偏好](translation.md)。

## 区分显示权限和执行权限

给群聊管理命令登记帮助时，可以这样写：

```python
server.register_help_message(
    '/admin',
    {'zh_cn': '管理命令', 'en_us': 'Administration commands'},
    permission=2,
    scope=('group',),
    only_admin=True,
)
```

这三个设置分别守着三扇门：

- `permission=2` 控制谁能在普通帮助列表里看到这一项。
- `only_admin=True` 控制面板操作资格。
- 命令节点上的 `requires(...)` 才负责真正执行时的权限检查。

按[命令树](command-tree.md#用-requires-检查条件)给管理命令加上执行检查。权限等级和授权方式见[权限](permissions.md)。

## 按平台要求编写面板文字

QQ 指令面板把 `prefix` 当作名称，把翻译后的 `message` 当作描述：

| 字段 | 平台约束                                              |
| ---- | ----------------------------------------------------- |
| 名称 | 1–14 字符。                                           |
| 描述 | 1–30 字符。                                           |
| 字符 | 使用非控制字符。                                      |
| 项数 | 每个场景最多展示 20 项，内置的 `/botqraft` 也占一项。 |

为每种语言准备简短描述。详细用法放进命令回复里，面板只留入口说明。

超出 20 项的前缀，命令注册仍然保留，只是不在面板上展示。你可以通过面板状态查到哪些项目没被展示。同一场景里，如果同名前缀的描述或 `only_admin` 不一致，就算作冲突。

面板文字不合规或者有冲突时，后果取决于发生在什么时候：

- 实例启动时：启动会直接失败。
- 运行中（比如重载插件后）：只有对应场景的面板状态变成 `failed`，命令和普通帮助照常可用。

面板同步和命令执行是两条独立的路径。

## 查看面板状态

在插件回调里可以读取面板的状态快照：

```python
status = server.get_panel_status('group')
server.logger.info('Panel state: %s', status.state)
server.logger.info('Undisplayed prefixes: %s', status.undisplayed_prefixes)
```

查询私聊面板时改用 `server.get_panel_status('c2c')`。状态快照还提供 `reason`、`err_code`、`code`、`http_code` 和 `trace_id`，方便你查同步失败的原因。

接下来，阅读[权限系统](permissions.md)，决定谁能执行命令。
