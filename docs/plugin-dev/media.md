# 发送图片、视频和文件

> **场景**：用户发 `/chart` 时，我想回一张本地生成的统计图；另一个功能要把一段视频发到群里。该怎么做？

读完这一页，你能让插件回复或主动发送图片、视频、语音和文件。

媒体消息用 `QImage`、`QVideo`、`QVoice`、`QFile` 表示，从 `botqraft.api.qtext` 导入。它们和文字一样，交给[回复](reply.md)的 `source.reply`，或[主动发送](sending.md)的 `server.send`，上传由框架完成。

## 回复一张图片

在命令回调里回复一张本地图片：

```python
from pathlib import Path

from botqraft.api.command import QQCommandSource
from botqraft.api.qtext import QImage

def send_chart(source: QQCommandSource):
    return source.reply(QImage(Path('chart.png')), return_future=True)
```

主动发送的写法相同，只是换成目标。例如发回命令所在的会话：

```python
from pathlib import Path

from botqraft.api.command import QQCommandSource
from botqraft.api.qtext import QVideo
from botqraft.api.types import QQPluginServerInterface

def send_clip(server: QQPluginServerInterface, source: QQCommandSource):
    return server.send(source.target, QVideo(Path('clip.mp4')), return_future=True)
```

## 选择媒体来源

媒体的来源有四种写法：

| 来源               | 写法                                  | 说明                                                                   |
| ------------------ | ------------------------------------- | ---------------------------------------------------------------------- |
| 公网 URL           | `QImage('https://example.com/a.png')` | 平台自己下载。字符串只接受 `http://` 或 `https://` 开头的地址。        |
| 本地文件           | `QImage(Path('a.png'))`               | 本地文件必须用 `pathlib.Path`，普通字符串会被当作错误的 URL 拒绝。     |
| 内存数据           | `QImage(data, name='a.png')`          | `bytes` 会在构造时复制一份，之后改动原数据不影响发送。                 |
| 可 seek 的二进制流 | `QFile(stream, name='report.pdf')`    | 从流的当前位置读到末尾。发送的 Future 完成前请保持流打开且不要改动它。 |

内存数据和流必须提供 `name`，也就是对方看到的文件名；本地文件默认使用文件名。

构造时就会检查来源：文件不存在、为空、超过 200 MiB，或者流不能 seek，都会立刻抛出异常。文件格式由平台判断，框架不做转换，例如语音需要你自己准备平台支持的格式。

## 使用限制

- 一条媒体消息只有媒体本身，不能附带文字或键盘。`QText('说明') + QImage(...)` 会抛出 `TypeError`；需要说明文字时，单独再发一条。
- 每次发送都会重新上传到目标会话。同一个 `QImage` 对象可以多次发送，但每次都会上传。
- 上传需要时间。用 `reply` 回复时，如果上传结束时已经超过被动回复的有效期，框架不会再发出消息，Future 以 `PassiveReplyExpiredError` 结束。大文件建议改用 `send` 主动发送。
- 发送图片和视频需要机器人账号具有对应的富媒体消息权限。
- 上传失败、平台拒绝和网络错误都通过 Future 报告，处理方式与文字消息相同，见[处理发送结果](sending.md#处理发送结果)。

想看一个完整的例子，仓库里的 [Echo 示例](https://github.com/tanhHeng/BotQraftReforged/blob/main/example_plugins/echo.py)会把用户发来的图片逐张回复出去。

接下来，阅读[Markdown 消息与文本交互](markdown.md)，让文字消息更好看。
