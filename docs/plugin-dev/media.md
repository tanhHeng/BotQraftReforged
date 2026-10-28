# 发送图片、视频和文件

> **场景**：用户发 `/chart` 时，我想回一张本地生成的统计图；另一个功能要把一段视频发到群里。该怎么做？

读完这一页，你能让插件回复或主动发送图片、视频、语音和文件。

媒体消息用 `QImage`、`QVideo`、`QVoice`、`QFile` 表示，从 `botqraft.api.qtext` 导入。用法和文字一样：把它们交给[回复](reply.md)用的 `source.reply`，或[主动发送](sending.md)用的 `server.send` 就行，上传由框架替你完成。

## 回复一张图片

最简单的用法，是在命令回调里回复一张本地图片：

```python
from pathlib import Path

from botqraft.api.command import QQCommandSource
from botqraft.api.qtext import QImage

def send_chart(source: QQCommandSource):
    return source.reply(QImage(Path('chart.png')), return_future=True)
```

主动发送的写法也一样，只是把来源换成目标。下面的例子在 `on_load` 里注册一个 `/clip` 命令，把插件数据目录里的 `clip.mp4` 发回命令所在的会话：

```python
from pathlib import Path

from botqraft.api.command import QQCommandSource, SimpleCommandBuilder
from botqraft.api.qtext import QVideo
from botqraft.api.types import QQPluginServerInterface

def send_clip(server: QQPluginServerInterface, source: QQCommandSource):
    clip = Path(server.get_data_folder()) / 'clip.mp4'
    return server.send(source.target, QVideo(clip), return_future=True)

def on_load(server: QQPluginServerInterface, prev_module):
    builder = SimpleCommandBuilder()
    builder.command('/clip', lambda source: send_clip(server, source))
    builder.register(server)
```

相对路径是相对机器人的工作目录来算的。`server.get_data_folder()` 返回 `config/<plugin_id>`，试之前先把视频放进这个目录。如果文件不存在，`QVideo(...)` 会在命令执行时抛出 `ValueError`。

## 选择媒体来源

媒体来源有四种写法，按你手头的数据选一种就行：

| 来源               | 写法                                  | 说明                                                                                           |
| ------------------ | ------------------------------------- | ---------------------------------------------------------------------------------------------- |
| 公网 URL           | `QImage('https://example.com/a.png')` | 平台自己下载。字符串只接受 `http://` 或 `https://` 开头的地址。                                |
| 本地文件           | `QImage(Path('a.png'))`               | 本地文件必须用 `pathlib.Path` 等 `os.PathLike`，普通字符串会被当作错误的 URL 拒绝。            |
| 内存数据           | `QImage(data, name='a.png')`          | `bytes`、`bytearray` 或 `memoryview` 会在构造时复制一份，之后改动原数据不影响发送。            |
| 可 seek 的二进制流 | `QFile(stream, name='report.pdf')`    | 从流的当前位置读到末尾。发送的 Future 完成前请保持流打开且不要改动它；框架不会替你关闭这个流。 |

内存数据和流必须提供 `name`，也就是对方看到的文件名。本地文件默认用它自己的文件名。

来源在构造时就会检查。文件不存在、为空、超过 200 MiB，或者流不能 seek，都会立刻抛出 `ValueError`；文本流这类不支持的来源类型会抛出 `TypeError`。

URL 的大小由平台判断，文件格式也由平台判断。框架不做格式转换，比如语音，就需要你自己准备成平台支持的格式。

## 使用限制

- 一条媒体消息只有媒体本身，不能附带文字或键盘。`QText('说明') + QImage(...)` 会抛出 `TypeError`；需要说明文字时，单独再发一条。
- 同一个 `QImage` 对象可以多次发送，但每次发送都会重新上传到目标会话。
- 上传需要时间。用 `reply` 回复时，如果上传完成时已经过了被动回复的有效期，框架就不会再发出这条消息，Future 会以 `PassiveReplyExpiredError` 结束。所以大文件建议改用 `send` 主动发送。
- 格式和大小由平台把关。官方文档写的是：视频只支持 mp4，超过 30 MB 会降级为文件上传；图片超过 20 MB 同样降级。
- 上传失败、平台拒绝和网络错误都通过 Future 报告，处理方式与文字消息相同，见[处理发送结果](sending.md#处理发送结果)。

想看完整的例子，可以参考仓库里的 [Echo 示例](https://github.com/tanhHeng/BotQraftReforged/blob/main/example_plugins/echo.py)，它会把用户发来的图片逐张回复出去。

接下来，读一读[Markdown 消息与文本交互](markdown.md)，让文字消息更好看。
