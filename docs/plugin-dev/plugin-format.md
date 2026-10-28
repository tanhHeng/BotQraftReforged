# 插件格式、打包与发布

> **场景**：我的插件从一个文件长成了好几个模块，还带着翻译和图片，想打包成一个文件发给别人，对方直接放进 `plugins/` 就能用。该怎么做？

插件有三种形态：单文件、目录和压缩文件。读完这一页，你能挑出合适的形态，把目录整理好，并打包出可以分发的文件。

单文件适合开始编写插件。需要拆分代码、附带翻译或资源时，使用目录插件。分发时再把目录打包成压缩插件。

## 选择格式

| 格式                      | 元数据与入口                                                         | 安装方法                                              |
| ------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------- |
| 单文件 `.py`              | 模块级 `PLUGIN_METADATA` 字典，文件本身是入口。                      | 将 Python 文件放入实例插件目录。                      |
| 目录插件                  | 根目录的 `botqraft.plugin.json`，`entrypoint` 指向 Python 模块或包。 | 将完整插件目录放入实例插件目录。                      |
| `.mcdr` / `.pyz` 压缩插件 | 归档根目录的 `botqraft.plugin.json` 和入口模块。                     | 用 `botqraft pack` 生成归档，再直接放入实例插件目录。 |

先准备一个已初始化的 BotQraft 实例。默认插件目录是实例的 `plugins/`，也可以通过 `plugin_directories` 修改。配置方法见[实例配置](../quick-start/configuration.md)。

`.mcdr` 和 `.pyz` 都可以看成装插件的压缩包。包里面要按 BotQraft 约定放好元数据、入口代码和资源；这套摆放规则就是"归档约定"。两者使用同一套归档约定，互换后缀不影响加载。

文件第一行以 `#!` 开头的解释器声明叫 shebang，例如 `#!/usr/bin/env python3`。加上 shebang 后，归档仍由 BotQraft 加载。运行时由实例提供框架和机器人凭据。制作独立机器人发行包时，另外准备这些内容。

单文件写法见[第一个插件](first-plugin.md)，也可以复制 [Echo 示例](https://github.com/tanhHeng/BotQraftReforged/blob/main/example_plugins/echo.py)。

## 整理目录插件

先建立下面的结构：

```text
example/
├── botqraft.plugin.json
├── echo_plugin/
│   └── __init__.py
├── requirements.txt
├── lang/
│   ├── en_us.yml
│   └── zh_cn.yml
└── assets/
    └── help.txt
```

这里的插件 ID 和源码包目录都使用 `echo_plugin`。把插件回调放在 `echo_plugin/__init__.py`，并在元数据中设置 `"entrypoint": "echo_plugin"`。完整字段声明见[元数据](metadata.md)。

从单文件迁入代码时，把元数据统一放入 `botqraft.plugin.json`，并移除 Python 文件中的 `PLUGIN_METADATA`。再按需添加 `requirements.txt` 和资源目录。

### 翻译与资源

把翻译文件放在插件根目录的 `lang/`，与 Python 包目录并列。框架会自动发现并注册其中的 `.json`、`.yml`、`.yaml` 文件。如果翻译原本在 Python 包内或 `resources/lang/` 中，把它们调整到根目录 `lang/`。

翻译键使用插件 ID 作为命名空间。打包时，把 `lang` 加入元数据的 `resources`：

```json
{
  "resources": ["assets", "lang"]
}
```

上面是需要合并到完整元数据中的资源字段。打包器会自动带上 `botqraft.plugin.json`、存在的 `requirements.txt`，以及和插件 ID 同名的源码目录。像图片、帮助文件和翻译目录这样的额外资源，再写进 `resources` 里就好。

运行实例需要能够访问入口模块、Python 依赖和资源。目录及压缩插件用 `server.open_bundled_file('assets/help.txt')` 读取只读资源，例如：

```python
from botqraft.api.types import QQPluginServerInterface

def read_help(server: QQPluginServerInterface) -> str:
    # Bundled resources are opened as binary files.
    with server.open_bundled_file('assets/help.txt') as stream:
        return stream.read().decode('utf-8')
```

需要保存的可写数据放进 `server.get_data_folder()` 返回的 `config/<plugin_id>` 目录，归档只用于保存分发内容。单文件插件自行定位并读取外部资源文件。更多用法见[插件数据](data.md)和[多语言与用户偏好](translation.md)。

## 安装依赖

把 Python 第三方库写在插件根目录的 `requirements.txt`。插件之间的依赖写在元数据的 `dependencies`，两者分别声明。

分发前，先在运行 BotQraft 的 Python 环境中安装依赖。在包含 `example/` 的工作目录执行：

```sh
python -m pip install -r example/requirements.txt
```

框架加载插件时检查这些要求，依赖安装由部署步骤完成。压缩插件也需要在实例环境中安装所声明的 Python 库。把依赖说明随插件一起提供，方便使用者准备运行环境。

## 打包命令

打包其实就是收拾好输入目录、选一个输出位置，再决定文件名和要排除的开发文件。照下面几步走，很快就能得到可以安装的归档。

在包含 `example/` 的工作目录执行：

```sh
botqraft pack -i example -o packed_plugins
```

需要指定文件名和忽略规则时，可以使用：

```sh
botqraft pack -i example -o packed_plugins -n "{id}-{version}.pyz" --ignore-patterns "__pycache__/" "*.pyc"
botqraft pack -i example -o packed_plugins --ignore-file .gitignore --shebang "/usr/bin/env python3"
```

参数说明：

1. **指定要打包的目录。** `-i` 使用带有 `botqraft.plugin.json` 的目录。打包单文件代码时，先按上面的目录结构整理入口和 JSON 元数据。
2. **指定输出位置。** `-o` 指定输出目录，生成的文件放在这里。
3. **决定文件名。** `-n` 覆盖元数据中的默认文件名模板，可以使用 `{id}`、`{version}`。复制前确认实际生成的文件名和扩展名。
4. **决定忽略哪些文件。** 默认读取输入目录的 `.gitignore`，忽略文件是可选的。忽略规则使用 gitignore 风格，相对插件输入目录匹配。`--ignore-patterns` 的优先级高于 `--ignore-file`，同时设置时使用前者。打包后检查归档内容，清理缓存、凭据和开发文件。
5. **需要时设置解释器行。** `--shebang` 设置可选的解释器行。框架沿用 MCDR 2.14.4 的资源、requirements 和归档约定，直接使用当前安装的 MCDR 即可。

## 安装与更新

将实际生成的 `.mcdr` 或 `.pyz` 直接放入实例配置的插件目录，保持压缩格式。启动实例，或在运行中的实例执行：

```text
/botqraft plugin refresh
/botqraft plugin list
```

确认插件已经加载后，在 QQ 中使用插件功能。修改插件后，重新打包并替换归档，再执行：

```text
/botqraft plugin reload echo_plugin
```

如果 Echo 没有加载，先打开日志。优先看看元数据、入口导入和依赖这三类提示，通常很快就能找到是哪一块还没准备好。

每个插件 ID 保留一个可加载副本。切换到压缩插件时，将同 ID 的单文件或目录副本移出插件目录。

BotQraft 与 Minecraft 插件共享部分打包格式，各自使用对应的输入和宿主 API。迁移时先阅读[MCDR 开发者路线](index.md#mcdr-开发者路线)。

接下来，查阅[API 索引](api.md)，看看还有哪些公开接口可用。
