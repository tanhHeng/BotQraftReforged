# 权限系统

> **场景**：我有一条清空数据的 `/reset` 命令，只想让管理员能用，还想单独给某位用户开放权限。该怎么做？

读完这一页，你能给命令加上权限检查，并为用户设置或移除授权。

## 查询权限时传入真实用户对象

查询权限时，要传入真实的用户对象：可以是真实的 `User`，也可以是命令回调里的 `QQCommandSource`。

先记住这两个标识的用途：`User.id` 用来认出"是谁"，OpenID 用来认出"在哪个会话"。最稳妥的做法，是把框架从真实消息里拿到的用户对象直接传进去。另外，每次执行受保护的操作时都重新查询一次，权限变更才能及时生效。

## 检查执行权限

把权限条件放在命令节点上：

```python
from botqraft.api.command import Literal

def show_status(source):
    source.reply('Ready')

def on_load(server, prev_module):
    server.register_command(
        Literal('/status')
        .requires(lambda source: source.has_permission(2))
        .runs(show_status)
    )
    server.register_help_message('/status', 'Show status', permission=2)
```

`source.has_permission(level)` 检查用户是否达到某个最低等级。`source.get_permission_level()` 和 `server.get_permission_level(subject)` 返回当前有效等级。这里的 `subject` 就是查询权限时传入的那个用户对象。

帮助项的 `permission` 只决定帮助显不显示，执行权限由命令节点检查。平台面板的 `only_admin=True` 只让群管理员能点击这个面板项。这一点由 QQ 平台判断，和 BotQraft 的权限等级无关，也不能代替执行检查。具体用法见[命令树](command-tree.md)和[帮助消息与指令面板](help.md)。

## 了解权限优先级

有效权限按下面的顺序决定：

1. `permission.super_admins` 里列出的真实 `User.id` 是超级管理员，直接按等级 4 处理。
2. 然后看当前会话上的显式权限。
3. 再看全局的显式权限。
4. 最后看当前模式的默认权限。

| 模式                             | 默认权限                               |
| -------------------------------- | -------------------------------------- |
| `native`                         | 0。                                    |
| `role` / `mixed`（默认 `mixed`） | 群成员 0、管理员 2、群主 4。C2C 为 0。 |

没拿到角色识别结果时，按 0 处理。显式授权优先于模式默认值。想查询超级管理员身份，用 `server.is_super_admin(subject)`，这里的 `subject` 同样是查询权限时传入的用户对象。配置方法见[实例配置](../quick-start/configuration.md)。

## 设置与移除授权

传入当前消息的来源，就能操作当前会话的授权：

```python
server.set_permission_level(source, 2)
server.remove_permission(source)
```

加上 `global_scope=True`，操作的就是跨会话的全局授权：

```python
server.set_permission_level(source, 2, global_scope=True)
server.remove_permission(source, global_scope=True)
```

等级可以传有效的整数、等级名称或 `botqraft.api.types.PermissionLevelItem`。`global_scope` 传 bool。

注意，等级传 bool 会抛出 `TypeError`，非法等级会被拒绝。传入的对象要带真实身份和会话地址。

操作 C2C 私聊的会话授权（不加 `global_scope=True`）时，还有一个要求：框架必须已经从真实私聊消息里记录过这个用户，而且私聊地址一致，否则会抛出 `ValueError`。别担心，私聊命令回调里的 `source` 来自刚收到的私聊消息，通常都满足这一点。全局授权不做这项检查。

传入的对象类型不对，会抛出 `TypeError`；缺少身份（`User.id`）会抛出 `ValueError`；操作会话授权时缺少会话地址，同样抛出 `ValueError`。最省心的做法是直接把实际的 `source` 传进去，身份和会话地址就都带上了。

接下来，命令需要更复杂的结构时，阅读[命令树](command-tree.md)。
