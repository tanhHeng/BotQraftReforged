# 权限系统

读完这一页，你能给命令加上权限检查，并为用户设置或移除授权。

## 查询权限时传入真实用户对象

查询权限时传入真实用户对象。它要么是真实的 `User`，要么是命令回调里的 `QQCommandSource`。

先记住两个用途：`User.id` 用来认出"是谁"，OpenID 用来认出"在哪个会话"。查询权限时，把框架从真实消息里拿到的用户对象直接传进去最稳妥。每次执行受保护操作时都重新查询一次，权限变更才能及时生效。

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

`source.has_permission(level)` 检查最低等级。`source.get_permission_level()` 和 `server.get_permission_level(subject)` 返回当前有效等级。这里的 `subject` 就是查询权限时传入的那个用户对象。

帮助项的 `permission` 过滤帮助显示，执行权限由命令节点检查。平台面板的 `only_admin=True` 决定谁有管理员点击和操作资格，面板项是否可见由平台决定。具体用法见[命令树](command-tree.md)和[帮助消息与指令面板](help.md)。

## 了解权限优先级

有效权限按下面的顺序决定：

1. `permission.super_admins` 里列出的真实 `User.id` 是超级管理员。
2. 然后看当前会话上的显式权限。
3. 再看全局的显式权限。
4. 最后看当前模式的默认权限。

| 模式             | 默认权限                               |
| ---------------- | -------------------------------------- |
| `native`         | 0。                                    |
| `role` / `mixed` | 群成员 0、管理员 2、群主 4。C2C 为 0。 |

角色识别结果缺失时按 0 处理。显式授权优先于模式默认值。用 `server.is_super_admin(subject)` 查询超级管理员身份，`subject` 同样是查询权限时传入的用户对象。配置方法见[实例配置](../quick-start/configuration.md)。

## 设置与移除授权

传入当前消息的来源，操作当前会话：

```python
server.set_permission_level(source, 2)
server.remove_permission(source)
```

设置 `global_scope=True`，操作跨会话的全局授权：

```python
server.set_permission_level(source, 2, global_scope=True)
server.remove_permission(source, global_scope=True)
```

等级可以传有效的整数、等级名称或 `botqraft.api.types.PermissionLevelItem`。`global_scope` 使用 bool。

等级传 bool 会抛出 `TypeError`，非法等级会被拒绝。请传入带真实身份和会话地址的对象。给 C2C 私聊授权时，请使用框架从真实私聊消息里记录过的地址。这样框架能确认这个会话确实存在；如果地址还没验证，会用 `ValueError` 提醒你。

传入的对象类型不对会抛出 `TypeError`，缺少身份或会话地址也会拒绝操作。直接把实际 `source` 传进去，这些事实就都保留了。

## 保存用户语言

用户语言保存在偏好里，默认跟随实例的 `language`。用 `source.get_preference()` 或 `server.get_preference(source)` 取得一份偏好副本。偏好是拿出来的一份副本。先改这份副本，再调用 `set_preference`，设置才会真正留下来。可以把它想成：取出表单、修改表单、提交表单。

```python
def set_english(server, source):
    preference = server.get_preference(source)
    preference.language = 'en_us'
    server.set_preference(source, preference)
```

接下来阅读[翻译与用户语言](translation.md)，让反馈在真正发送或展示的时刻按用户语言生成。
