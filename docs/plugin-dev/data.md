# 插件数据与打包资源

> **场景**：我的插件要随包带一份默认语录，还要把用户投稿保存下来，重启以后也不丢。这些文件该放在哪里？

插件通常会带两种文件：随插件发布的资源，比如帮助文档和图片；运行后自己产生的数据，比如配置和状态。前者跟着插件走，后者住在实例的数据目录里。分清这两处，收拾文件时就不会迷路。

读完这一页，你能读取打包资源，也能给插件找到一块可写的地方。两类文件都通过绑定到插件的 `QQPluginServerInterface` 来访问。

## 读取打包资源

目录插件和压缩插件用 `server.open_bundled_file(relative_path)` 读取资源。路径相对于插件根目录，返回的是二进制文件对象。请用 `with` 打开，让文件及时关闭：

```python
def read_help(server):
    with server.open_bundled_file('assets/help.txt') as stream:
        return stream.read().decode('utf-8')
```

目录插件会直接读取目录里的文件。打包成 `.mcdr` / `.pyz` 时就要留意了：打包命令只会自动带上元数据、`requirements.txt` 和以插件 ID 命名的源码目录。所以请在插件元数据的 `resources` 里加入 `assets`，资源才会跟着归档一起分发。翻译文件也一样：放在根目录 `lang/`，并把 `lang` 加入 `resources`。具体结构见[插件格式](plugin-format.md)和[多语言与用户偏好](translation.md)。

`open_bundled_file` 只适用于目录插件和压缩插件。单文件插件需要自己定位并读取外部文件。在单文件插件里，或者用没有绑定插件的接口调用这个方法，会抛出 `FileNotFoundError`。如果要读的资源不存在，目录插件会抛出 `FileNotFoundError`，压缩插件则抛出 `KeyError`。

## 保存可写数据

调用 `server.get_data_folder()`，就能拿到实例里的 `config/<plugin_id>` 路径；目录不存在时会自动创建。返回值是一个相对于实例工作目录的路径字符串。请用插件回调传进来的绑定接口来调用：

```python
import json
from pathlib import Path

def save_state(server, state):
    path = Path(server.get_data_folder()) / 'state.json'
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

def load_state(server):
    path = Path(server.get_data_folder()) / 'state.json'
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return {}
```

数据目录由插件 ID 决定，插件 ID 不变，目录就不变。插件归档里放随插件分发的内容，运行中可写的状态放进数据目录。如果接口没有绑定插件记录，调用 `get_data_folder()` 会抛出 `RuntimeError`。

如果有多个任务访问同一份状态，读写要由插件自己协调。文件、连接和其他资源，由创建它们的插件负责关闭。卸载时要做哪些事，见[后台任务与卸载](tasks.md)。

## 使用公开序列化工具

`botqraft.api.utils` 提供了 `Serializable`、`serialize`、`deserialize`，它们就是 MCDR 的序列化工具：

- 继承 `Serializable`，用类型注解声明字段。
- `serialize()` 把对象转换成能写进 JSON 的 dict、list 等数据。
- `deserialize()` 按注解把对象恢复回来，缺少的字段使用默认值。

模块级的 `serialize(obj)` 和 `deserialize(data, cls)` 是对应的函数写法。下面的例子把语录保存成 JSON：

```python
import json
from pathlib import Path
from typing import List

from botqraft.api.utils import Serializable

class Quote(Serializable):
    text: str = ''
    author: str = ''

class QuoteStore(Serializable):
    quotes: List[Quote] = []

def save_quotes(server, store):
    path = Path(server.get_data_folder()) / 'quotes.json'
    path.write_text(json.dumps(store.serialize(), ensure_ascii=False), encoding='utf-8')

def load_quotes(server):
    path = Path(server.get_data_folder()) / 'quotes.json'
    if not path.exists():
        return QuoteStore()
    return QuoteStore.deserialize(json.loads(path.read_text(encoding='utf-8')))
```

公开模块列表见[API 索引](api.md)。

接下来，阅读[后台任务与卸载](tasks.md)，安排插件的后台工作并做好收尾。
