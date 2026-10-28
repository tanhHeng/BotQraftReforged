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

在插件元数据的 `resources` 中加入 `assets`，让资源随归档分发。翻译文件使用根目录 `lang/`，并将 `lang` 加入 `resources`。具体结构见[插件格式](plugin-format.md)和[多语言与用户偏好](translation.md)。

`open_bundled_file` 用于目录或压缩插件。单文件插件自行定位并读取外部文件。使用单文件插件或未绑定插件的接口调用该方法，会抛出 `FileNotFoundError`。目标资源也需要实际存在。

## 保存可写数据

调用 `server.get_data_folder()` 创建并获取实例的 `config/<plugin_id>` 路径。返回值是相对路径字符串。请使用插件回调传入的绑定接口：

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

从 `botqraft.api.utils` 导入 `Serializable`、`serialize`、`deserialize`，沿用 MCDR 的序列化接口。请选择与数据类型匹配的格式，在读取后恢复业务对象。公开模块列表见[API 索引](api.md)。

接下来，阅读[后台任务与卸载](tasks.md)，安排插件的后台工作并做好收尾。
