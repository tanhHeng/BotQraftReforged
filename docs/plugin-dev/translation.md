# 多语言与用户偏好

> **场景**：我的插件既有中文用户也有英文用户，想让他们各自看到自己语言的提示，还想让用户自己切换语言。该怎么做？

这一页讲怎么让插件的提示文字跟随用户的语言。读完这一页，你能准备翻译文件、注册翻译、选对翻译接口，并保存用户自己选的语言。

做法是：把面向用户的文字写成翻译键，再用 `server.rtr` 创建延迟文本。延迟文本就像一张提货单：现在先记下“要说什么”和“填什么参数”，等到真正发送或展示时，才决定用哪种语言把它变成实际文字。

插件里写死的日志、异常和注释用英文；给中文用户看的文字，通过翻译键提供。

## 准备翻译文件

目录插件和压缩插件把翻译文件放在根目录的 `lang/` 里，格式可以是 `.json`、`.yml` 或 `.yaml`。文件名去掉后缀，就是语言代码。`lang/` 和 Python 包放在同一层。多文件插件里唯一的 Python 包必须以插件 ID 命名。下面的插件 ID 是 `greet`，所以源码包目录也叫 `greet`：

```text
greet/
├── botqraft.plugin.json
├── greet/
│   └── __init__.py
└── lang/
    ├── en_us.yml
    └── zh_cn.yml
```

插件加载时，框架会自动找到并注册根目录 `lang/` 里的翻译。放在 Python 包内或 `resources/lang/` 里的翻译不会被找到，请把它们挪到根目录的 `lang/`。打包时，记得把 `lang` 加进元数据的 `resources`，参见[元数据](metadata.md)和[插件格式](plugin-format.md)。

翻译键请用插件 ID 作为命名空间。框架不会强制这一点，但所有插件共用一张翻译表，遇到同名的键时框架自带的优先，所以请务必加上前缀。插件 ID 为 `greet` 时，`lang/en_us.yml` 这样写：

```yaml
greet:
  hello: "Hello, {name}!"
  help: "Send a greeting"
```

`lang/zh_cn.yml` 用同样的键：

```yaml
greet:
  hello: "你好，{name}！"
  help: "发送问候"
```

## 注册动态翻译

单文件插件，或者需要动态注册翻译时，在 `on_load` 里调用 `register_translation(language, mapping)`，传入按命名空间组织的映射：

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

这些翻译登记会随插件的生命周期自动清除。重载时，由新模块重新登记。

## 保留延迟文本

可以写一个小封装来补全命名空间，它返回 `QQTranslationText`：

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

`server.rtr(key, ...)` 构造时只记下键和参数，到真正发送或展示的那一刻才求值。`source.reply` 会按当前用户的偏好选择语言。帮助查询使用当前来源的语言，平台的帮助面板则使用实例语言。

延迟文本支持 `append`、加法、复制和附加键盘，组合之后仍然是延迟的。嵌套的延迟文本会用同一种语言求值。每条结果最多只能有一个键盘，多个参数都带着键盘时会抛出 `ValueError`。

请把延迟对象原样交给接受它的接口。`str()`、`to_plain_text()`、`to_payload()` 和 `get_keyboard()` 都会立刻求值，提前调用它们，就会把这一次结果的语言固定下来。

## 使用 Markdown 模板

翻译模板本身是 Markdown 时，构造时加上 `markdown=True`：

```python
message = server.rtr('greet.hello', markdown=True, name=name)
source.reply(message)
```

`markdown=True` 会保留模板里的 Markdown。参数则各按各的规则处理：

- 普通字符串和 `QText` 按纯文本转义。
- `QMarkdown` 保留自己的 Markdown。
- 交互对象保留交互标签。
- 嵌套的延迟文本按同一种语言解析。

消息组合方式见[Markdown 消息与文本交互](markdown.md)。

## 获取即时文本

有些地方需要立刻拿到文字，比如键盘标签、按钮数据、异常文本，以及明确的同步查询。这时用 `server.tr`。参数全是字符串、数字、布尔值或 `None` 时，它返回字符串；参数里有 QQ 文本时，结果可能是 `QText` 或 `QMarkdown`。

如果构造器参数只接受字符串，就用普通文本翻译，并明确指定来源的语言：

```python
label = server.tr('greet.help', language=source.get_preference().language)
```

在同步代码里，也可以借用来源的语言上下文：

```python
with source.preferred_language_context():
    label = server.tr('greet.help')
```

退出上下文时，会恢复原来的语言。请只在同步调用里使用它，并在 `await` 之前退出；如果上下文跨越了 `await`，会抛出 `RuntimeError`。需要跨越异步边界的消息，请用延迟文本。

`botqraft.api.qtext` 也导出了 `tr` 和 `rtr`。这两个模块级函数需要一个正在运行的 BotQraft 接口，否则会抛出 `RuntimeError`。在插件回调里，优先用传入的 `server`。

## 保存用户语言

用户的语言保存在偏好里；如果用户还没保存过偏好，就使用实例当前的 `language`。用 `source.get_preference()` 或 `server.get_preference(source)` 取得一份偏好副本。先改这份副本，再调用 `server.set_preference(source, preference)`，设置才会真正留下来。可以把它想成：取出表单、修改表单、提交表单。

```python
def set_english(server, source):
    preference = server.get_preference(source)
    preference.language = 'en_us'
    server.set_preference(source, preference)
```

`language` 必须是框架已加载的语言（例如 `en_us`、`zh_cn`），否则 `set_preference` 会抛出 `ValueError`。注意，插件在 `lang/` 里新增的语言不会加进这个列表。保存之后，`source.reply` 发送的延迟文本和 `preferred_language_context()` 都会改用新语言。

## 处理翻译失败

找不到翻译键时，默认会记录一条英文错误日志，并直接把键本身当作文本返回（不做格式化）。如果设置了 `allow_failure=False`，缺键时会抛出 `KeyError`。

另外，参数类型不受支持时抛出 `TypeError`；格式化失败（例如缺少 `{name}` 对应的参数）时抛出 `ValueError`。

这些错误什么时候出现，取决于你用的接口：即时的 `tr` 在调用时就会报错，延迟的 `rtr` 要等到真正发送或展示时才会报错。

接下来，阅读[插件数据与打包资源](data.md)，把资源与运行状态放到正确的位置。
