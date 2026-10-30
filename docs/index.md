---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: "BotQraftReforged"
  text: "适配官方 QQ 机器人的插件开发框架"
  tagline: 直连 QQ 官方接口，内置消息、事件、命令、权限和多语言支持。
  image:
    src: /icon.png
    alt: BotQraft
  actions:
    - theme: brand
      text: 快速上手
      link: /quick-start/
    - theme: alt
      text: 插件开发
      link: /plugin-dev/
    - theme: alt
      text: BotQraft 开发
      link: /botqraft-dev/
    - theme: alt
      text: GitHub
      link: "https://github.com/tanhHeng/BotQraftReforged"

features:
  - icon:
      src: /icons/zap.svg
    title: 直连官方 QQ 机器人
    details: 消息直接走 QQ 官方的网关和接口，中间没有第三方转发。群聊、私聊都能用。
    link: /quick-start/intro
    linkText: 什么是 BotQraft
  - icon:
      src: /icons/package.svg
    title: 文件即插件
    details: .py或.pyz，放进 plugins/ 目录就加载。
    link: /plugin-dev/basic
    linkText: 插件是怎么运行的
  - icon:
      src: /icons/bot.svg
    title: 交给 AI Agent
    details: 复制一份 AGENTS.md 模板给 Agent，然后燃烧你的 token！
    link: /plugin-dev/agents
    linkText: 用 AI Agent 开发插件
---

### 注册命令

注册命令，自动解析——

```python
from botqraft.api.command import GreedyText, SimpleCommandBuilder

PLUGIN_METADATA = {...}

def on_load(server, prev_module):
    builder = SimpleCommandBuilder()
    builder.command('/echo <text>', lambda source, context: source.reply(context['text']))
    builder.arg('text', GreedyText)
    builder.register(server)
```

详细用法见[注册命令](/plugin-dev/commands)。

### Markdown 和 @

适配官方 QQ 的 Markdown 消息格式，以及 @用户——

```python
from botqraft.api.command import QQCommandSource
from botqraft.api.qtext import QMarkdown, QTextAt

def handler(source: QQCommandSource, _):
    source.reply(QMarkdown('**任务完成** ').append(QTextAt(source.user)))
```

详细用法见[Markdown 消息与文本交互](/plugin-dev/markdown)。

### 按钮

官方 QQ 机器人特有的“按钮”功能，点击触发命令——

```python
from botqraft.api.command import QQCommandSource
from botqraft.api.qtext import (
    QKeyboardActionCommand, QKeyboardButton, QKeyboardCustom,
    QKeyboardPermission, QKeyboardRenderData, QMarkdown,
)

def handler(source: QQCommandSource, _):
    button = QKeyboardButton(
        id='again',
        render_data=QKeyboardRenderData(label='再来一次', style=1),
        action=QKeyboardActionCommand(data='/echo Hello BotQraft', permission=QKeyboardPermission()),
    )
    source.reply(QMarkdown('点下面的按钮试试').set_keyboard(QKeyboardCustom([[button]])))
```

详细用法见[按钮：键盘与点击响应](/plugin-dev/interactions)。

### 媒体文件

发送本地文件，轻轻松松——

```python
from pathlib import Path

from botqraft.api.command import QQCommandSource
from botqraft.api.qtext import QImage, QVideo

def handler(source: QQCommandSource, _):
    source.reply(QImage(Path('chart.png')))
    source.reply(QVideo(Path('clip.mp4')))
```

详细用法见[发送图片、视频和文件](/plugin-dev/media)。

### 多语言

国际友人也想用？语言切换，不在话下——

```python
from botqraft.api.command import SimpleCommandBuilder

def on_load(server, prev_module):
    server.register_translation('zh_cn', {'greet': {'hello': '你好，{name}！'}})
    server.register_translation('en_us', {'greet': {'hello': 'Hello, {name}!'}})

    builder = SimpleCommandBuilder()
    builder.command('/hello', lambda source: source.reply(server.rtr('greet.hello', name='BotQraft')))
    builder.register(server)
```

详细用法见[多语言与用户偏好](/plugin-dev/translation)。
