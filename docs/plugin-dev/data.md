# 插件数据与打包资源

> **场景**：我的插件要随包带一份默认语录，还要把用户投稿保存下来，重启以后也不丢。这些文件该放在哪里？

插件通常会带两种文件：随插件发布的资源，比如帮助文档和图片；运行后自己产生的数据，比如配置和状态。前者跟着插件走，后者住在实例的数据目录里。分清这两处，收拾文件时就不会迷路。

读完这一页，你能读打包资源，也能给插件找到一块可写的地方。两类文件都通过绑定插件的 `QQPluginServerInterface` 访问。

## 读取打包资源

目录和压缩插件使用 `server.open_bundled_file(relative_path)`。路径相对于插件根目录，返回二进制文件对象。请用 `with` 及时关闭文件：

```python
def read_help(server):
    with server.open_bundled_file('assets/help.txt') as stream:
        return stream.read().decode('utf-8')
```

目录插件直接读取目录中的文件。打包成 `.mcdr` / `.pyz` 时，打包命令只会自动带上元数据、`requirements.txt` 和以插件 ID 命名的源码目录，所以要在插件元数据的 `resources` 中加入 `assets`，让资源随归档分发。翻译文件使用根目录 `lang/`，并将 `lang` 加入 `resources`。具体结构见[插件格式](plugin-format.md)和[多语言与用户偏好](translation.md)。

`open_bundled_file` 用于目录或压缩插件。单文件插件自行定位并读取外部文件。使用单文件插件或未绑定插件的接口调用该方法，会抛出 `FileNotFoundError`。目标资源不存在时，目录插件抛出 `FileNotFoundError`，压缩插件抛出 `KeyError`。

## 保存可写数据

调用 `server.get_data_folder()` 获取实例的 `config/<plugin_id>` 路径，目录不存在时会自动创建。返回值是相对实例工作目录的路径字符串。请使用插件回调传入的绑定接口：

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

数据目录由稳定的插件 ID 决定。插件归档保存分发内容，可写状态存入数据目录。未绑定插件记录的接口调用 `get_data_folder()` 会抛出 `RuntimeError`。

同一状态由多个任务访问时，请在插件中协调读写。文件、连接和其他资源由创建它们的插件关闭。卸载职责见[后台任务与卸载](tasks.md)。

## 使用公开序列化工具

从 `botqraft.api.utils` 导入 `Serializable`、`serialize`、`deserialize`，它们就是 MCDR 的序列化工具。`Serializable` 子类用类型注解声明字段；`serialize()` 把对象转换成可以写入 JSON 的 dict、list 等数据，`deserialize()` 按注解恢复对象，缺少的字段使用默认值。模块级的 `serialize(obj)` 和 `deserialize(data, cls)` 是对应的函数写法：

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
