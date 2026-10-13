# 今日人品插件

读完这一页，你能把一个完整的示例插件装进实例，跑通查询、投稿和撤回的每一步。

这个插件把原来的 LazyBot/NoneBot 今日人品插件迁移到了 BotQraft，用 QQ Markdown、命令键盘和被动回复组合出完整功能。你可以从 [qq_jrrp 示例](https://github.com/BotQraftReforged/BotQraftReforged/blob/main/example_plugins/qq_jrrp/botqraft.plugin.json)开始看。

迁移后的插件独立运行。原 LazyBot 代码与语录数据保持原样。要沿用已有语录，先备份，再按本文的数据格式整理好，放进运行实例。

## 安装

按下面三步操作：

1. 把整个 `example_plugins/qq_jrrp` 目录复制到实例配置的插件目录。`botqraft.plugin.json`、入口包 `qq_jrrp/`、`lang/`、`LICENSE` 和 `NOTICE` 都要完整保留。
2. 启动实例。BotQraft 会自动注册插件根目录 `lang/` 里的翻译文件。

   如果你就在仓库根目录，已经初始化的测试实例在 `test/`，可以这样安装：

   ```powershell
   Copy-Item -Recurse .\example_plugins\qq_jrrp .\test\plugins\qq_jrrp
   Set-Location .\test
   python -m botqraft start
   ```

3. 实例已经在运行时，在运维控制台执行 `/botqraft plugin refresh` 加载新插件。

插件只登记一个 `/jrrp` 帮助/面板项，远端面板由框架统一管理。ID 为 `qq_jrrp` 的目录插件与压缩插件只保留一个可加载副本。

## 查询与文字触发

按下面三步查询：

1. 确认接收设置。普通群消息需要 QQ 平台推送 `GROUP_MESSAGE_CREATE`，先给账号和群开启接收所有消息，插件才能收到这些正文。C2C 不用设置，直接发送查询文本即可。
2. 发送下面任意一种消息：

| 输入               | 支持的消息场景                                     |
| ------------------ | -------------------------------------------------- |
| `/jrrp`            | 群聊和 C2C；群 AT 消息会按框架规则去掉正文前导空格 |
| `@机器人 今日人品` | 群 AT 消息，平台去掉提及后匹配正文                 |
| `今日人品`         | 普通群消息、群 AT 和 C2C                           |
| `#今日人品`        | 普通群消息、群 AT 和 C2C                           |

3. 读取回复。插件用原消息 ID 发送被动回复，展示为普通回复。这条路径只用消息 ID，会省略 `msg_idx`、`refer_msg` 和 `message_reference`。发送仍然受平台被动回复的时效、次数和 Markdown/键盘权限约束。

中文触发会先去掉真实正文两端的空白，再匹配完整的「今日人品」或「#今日人品」。匹配只看独立正文，「看看今日人品」、附加参数、卡片、附件和引用里的词语都不算。`/jrrp` 由命令回调处理一次，消息监听会把这条命令交回命令路径。

## 评分、语录与按钮

- 每日评分沿用原算法。真实 `User.id` 和运行机器的本地日期共同决定结果。数字 ID 保留原数值种子，非数字 OpenID 使用 SHA-256。幸运指数为 0–100%，同一天、同一身份的结果固定。
- 群聊与 C2C 用各自收到的真实 ID 计算身份。相同 ID 对应相同身份，不同 ID 分别处理。更换运行机器的时区，可能改变日期切换时间。
- 初始语录池为空。语录池保持相同时，旧算法最多选择三种每日候选语录。
- 投稿成功消息显示四个按钮，撤回按钮携带本条投稿的 UUID。所有人都可点击，执行权限由服务端检查。其他场景只显示一行「今日人品」「投稿」「帮助」。
- 群聊按钮负责把命令填入输入框。C2C 的今日人品和帮助按钮允许自动发送。投稿模板和撤回按钮填入输入框后，由用户确认发送。
- 用 `/botqraft pref language set en_us` 可以切换输出语言。中文和英文内容来自根目录 `lang/`。正文通过带插件命名空间的 `rtr` 封装延迟求值。键盘标签和模板在发送前生成字符串。代码注释、异常与硬编码日志使用英文。

## 投稿与撤回

可用的命令：

```text
/jrrp help
/jrrp post
/jrrp withdraw <id>
```

投稿按下面两步：

1. 先发送 `/jrrp post` 查看投稿方法。
2. 点投稿按钮填入模板，或者直接发送下面的多行消息：

   ```text
   /jrrp post '''
   在此填写语录，可以换行
   '''
   作者或出处
   ```

写法要求：`post` 后面保留一个空格，再写起始标记 `'''`。结束标记 `'''` 独占一行，作者或出处写在下一行。

正文内部的空格和换行会原样保留，普通引号和反斜杠可以直接输入。独占一行的 `'''` 专门作为结束标记，所以正文里出现同类文字时，请把它放在含其他内容的行上。还在用旧 `!文本` / `!出处` 模板的话，请改用上面的三引号格式。

命令树分别注册 `jrrp_handler`、`help_handler`、`post_handler` 和 `withdraw_handler`。`GreedyText` 只收集 `post` 的投稿内容。投稿解析函数负责检查标记及非空字段，其他命令各自由命令树调用。

文本与出处都需要填写。

撤回按下面两步：

1. 取得要撤回的 UUID。投稿成功消息里的撤回按钮已经带上它。
2. 发送 `/jrrp withdraw <id>`，把 `<id>` 换成该 UUID。

执行者需要是投稿者本人，或拥有至少 2 级权限。权限检查失败时，数据保持原样。

投稿成功消息里的按钮自动携带 UUID。旧按钮指向已撤回的投稿时，插件会提示该 UUID 对应的记录已缺失，并保留其他记录。相同的官方 `User.id` 就是同一个身份，与 appid 和场景无关。不同 ID 分别处理。

语录保存在运行实例的 `config/qq_jrrp/luck_sentence.json` 中。每条记录包含 `id`（持久化 UUID）、`sender`、`sentence`、`from`。新投稿的 `sender` 只保存通用官方 `User.id`。

加载已有文件时，插件会为缺少 UUID 的记录补齐 UUID。符合 `appid:group|c2c:id` 格式的 `sender` 会去掉 appid 和场景前缀，各个旧 appid 用同一迁移规则。其他旧身份值原样保留，身份归属以现有值为准。

所有记录验证通过后，迁移结果才会原子保存。UUID 在重启后保持稳定，重复投稿各自拥有独立 UUID。数据文件损坏时，插件会报告错误并保留原文件。

维护前先备份数据。沿用其他实例的数据时，请手动整理并复制到当前实例的数据路径。

## 分发许可

迁移插件保留原来源与 **GPL-3.0-only** 许可。具体内容见插件目录中的 [LICENSE](https://github.com/BotQraftReforged/BotQraftReforged/blob/main/example_plugins/qq_jrrp/LICENSE) 和 [NOTICE](https://github.com/BotQraftReforged/BotQraftReforged/blob/main/example_plugins/qq_jrrp/NOTICE)。这份许可适用于迁移插件，BotQraft 框架的许可证单独确定。

分发前先确认归档包含许可、来源说明和翻译资源，然后执行：

```sh
botqraft pack -i example_plugins/qq_jrrp -o packed_plugins
```

打包选项见[插件元数据与打包](plugin-format.md)。

接下来，回到[插件开发](index.md)，照着这套结构写你自己的插件。
