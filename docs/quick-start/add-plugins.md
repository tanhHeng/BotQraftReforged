# 添加插件

机器人已经启动了，现在让我们给它添加一些功能！

BotQraft 会从 `config.yml` 中的 `plugin_directories` 查找插件。默认目录是运行实例中的 `plugins/`。

## 选择插件

你可以安装以下三种格式的插件：

| 格式                       | 安装方法                                                    |
| -------------------------- | ----------------------------------------------------------- |
| 单文件插件 `.py`           | 将 Python 文件复制到 `plugins/`。                           |
| 目录插件                   | 将包含 `botqraft.plugin.json` 的完整目录复制到 `plugins/`。 |
| 压缩插件 `.mcdr` 或 `.pyz` | 将压缩包直接复制到 `plugins/`，保持压缩格式。               |

安装前，先阅读插件作者提供的说明，确认所需的 BotQraft 版本和 Python 依赖。

如果插件附带 `requirements.txt`，请在运行 BotQraft 的 Python 环境中安装依赖：

```bash
python -m pip install -r 插件目录/requirements.txt
```

每个插件 ID 保留一个可加载副本。更新插件时，用新版本替换原文件或目录即可。

## 试试 Echo 插件

仓库中提供了一个简单的 [Echo 示例](https://github.com/tanhHeng/BotQraftReforged/blob/main/example_plugins/echo.py)。它会复述你发送的文本和图片，很适合检查插件是否正常工作。

将仓库中的 `example_plugins/echo.py` 复制到运行实例的 `plugins/echo.py`。完成后，目录大致是这样的：

```text
botqraft-run/
├── config.yml
├── permissions.yml
└── plugins/
    └── echo.py
```

如果机器人正在运行，请在运维控制台输入：

```text
/botqraft plugin refresh
/botqraft plugin list
```

`refresh` 会刷新插件，`list` 会列出插件的加载状态。看到 Echo 出现在已加载列表中，就可以继续下一步了！

你也可以在复制完成后启动机器人，让它在启动时加载插件：

```bash
botqraft start
```

## 在 QQ 中使用

等到控制台出现 `BotQraft READY`，在机器人所在的群聊中 @机器人，并发送：

```text
/echo Hello world
```

也可以直接在与机器人的私聊中发送这条命令。收到 `Hello world` 的回复，就说明插件已经工作了。

Echo 也能复述图片：

| 发送                    | 机器人回复                                  |
| ----------------------- | ------------------------------------------- |
| `/echo` 并附带图片      | 把图片发回来。                              |
| `/echo 你好` 并附带图片 | 先回复文字 `你好 [image]`，再单独发回图片。 |

`[image]` 只是纯文字占位，标出原消息里有一张图片。BotQraft 的媒体消息不附带文字，所以图片会作为单独的消息发出。发送图片需要机器人账号具有富媒体消息权限。

插件命令请在 QQ 中测试。运维控制台用于执行 `/botqraft` 管理命令。

## 更新与管理

修改 Echo 的代码后，在运维控制台执行以下命令即可重载：

```text
/botqraft plugin reload echo
```

这里的 `echo` 是插件 ID。你可以通过 `/botqraft plugin list` 查询其他插件的 ID。

如果加载失败，先查看控制台或 `logs/botqraft.log` 中的错误。按照提示检查插件元数据、依赖版本和入口模块，再执行 `refresh`。

接下来，你可以安装[今日人品示例插件](../plugin-dev/jrrp-plugin.md)，或前往[插件开发](../plugin-dev/)编写自己的功能。
