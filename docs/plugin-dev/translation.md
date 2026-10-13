# 翻译与用户语言

这一页讲怎么让插件的提示文字跟随用户的语言。读完你能准备翻译文件、注册翻译，并选对翻译接口。

把面向用户的文字写成翻译键。用 `server.rtr` 可以创建延迟文本。延迟文本只保存翻译键和参数，等到真正发送或展示时才决定用哪种语言。插件里硬编码的日志、异常和注释使用英文，中文用户反馈通过翻译键提供。

## 准备翻译文件

目录和压缩插件在根目录 `lang/` 放置 `.json`、`.yml` 或 `.yaml` 文件。目录与 Python 包并列：

```text
greet/
├── botqraft.plugin.json
├── greet_plugin/
│   └── __init__.py
└── lang/
    ├── en_us.yml
    └── zh_cn.yml
```

框架自动发现并注册根目录 `lang/` 中的翻译。把 Python 包内或 `resources/lang/` 中的翻译挪到这个位置。打包时将 `lang` 加入元数据的 `resources`，参见[元数据](metadata.md)和[插件格式](plugin-format.md)。

翻译键使用插件 ID 作为命名空间。插件 ID 为 `greet` 时，`lang/en_us.yml` 写为：

```yaml
greet:
  hello: "Hello, {name}!"
  help: "Send a greeting"
```

`lang/zh_cn.yml` 使用相同的键：

```yaml
greet:
  hello: "你好，{name}！"
  help: "发送问候"
```

## 注册动态翻译

单文件插件和动态翻译在 `on_load` 中调用 `register_translation(language, mapping)`。传入按命名空间组织的映射：

```python
def on_load(server, prev_module):
    server.register_translation('en_us', {
        'greet': {'hello': 'Hello, {name}!', 'help': 'Send a greeting'},
    })
    server.register_translation('zh_cn', {
        'greet': {'hello': '你好，{name}！', 'help': '发送问候'},
    })
    server.register_help_message('/greet', server.rtr('greet.help'))
```

翻译登记随插件生命周期清除。重载时由新模块重新登记。

## 保留延迟文本

使用轻量封装补全命名空间，返回 `QQTranslationText`：

```python
from typing import Any
from botqraft.api.command import QQCommandSource
from botqraft.api.qtext import QQTranslationText
from botqraft.api.types import QQPluginServerInterface

PLUGIN_ID = 'greet'

def rtr(server: QQPluginServerInterface, key: str, *args: Any, **kwargs: Any) -> QQTranslationText:
    return server.rtr(f'{PLUGIN_ID}.{key}', *args, **kwargs)

def greet(server: QQPluginServerInterface, source: QQCommandSource, name: str) -> None:
    source.reply(rtr(server, 'hello', name=name))
```

`server.rtr(key, ...)` 在构造时只保存键和参数，等到真正发送或展示的那一刻才求值。`source.reply` 按当前用户偏好选择语言。帮助查询使用当前来源语言，平台帮助面板使用实例语言。

延迟文本支持 `append`、加法、复制和附加键盘，组合时仍保持延迟。嵌套的延迟文本在同一语言下求值，每条结果最多包含一个键盘。多个参数携带键盘时会抛出 `ValueError`。

请把延迟对象保留到接受它的接口。`str()`、`to_plain_text()`、`to_payload()` 和 `get_keyboard()` 会在当前时刻求值。提前转换会把这一次结果的语言固定下来。

## 使用 Markdown 模板

将模板标记为 Markdown：

```python
message = server.rtr('greet.hello', markdown=True, name=name)
source.reply(message)
```

`markdown=True` 保留模板的 Markdown。普通字符串和 `QText` 参数按纯文本转义，`QMarkdown` 参数保留自己的 Markdown，交互对象保留交互标签。嵌套的延迟文本按同一语言解析。消息组合方式见[Markdown、文本交互与键盘](markdown.md)。

## 获取即时文本

键盘标签、按钮数据、异常文本和明确的同步查询需要即时值，使用 `server.tr`。纯字符串参数的翻译返回字符串，QQ 文本参数可能使结果成为 `QText` 或 `QMarkdown`。

只接受字符串的构造器参数使用普通文本翻译，并明确选择来源语言：

```python
label = server.tr('greet.help', language=source.get_preference().language)
```

同步代码也可以使用来源的语言上下文：

```python
with source.preferred_language_context():
    label = server.tr('greet.help')
```

上下文在退出时恢复原语言。请把作用范围留在同步调用内，在 `await` 前退出。跨异步边界的消息使用延迟文本。

`botqraft.api.qtext` 同时导出 `tr`、`rtr`。这些模块级函数需要运行中的 BotQraft 接口。插件回调优先使用传入的 `server`。

## 处理翻译失败

缺少键时，默认记录英文错误并显示键。设置 `allow_failure=False`，缺键会抛出 `KeyError`。参数类型错误会抛出 `TypeError`，格式化失败会抛出 `ValueError`。即时 `tr` 在调用时暴露这些错误，延迟 `rtr` 在真正发送或展示时暴露它们。

用户语言的读取和保存见[权限系统](permissions.md)。

接下来，阅读[插件数据与打包资源](data.md)，把资源与运行状态放到正确的位置。
