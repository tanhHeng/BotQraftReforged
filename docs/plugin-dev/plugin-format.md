# 插件格式、打包与发布

> **场景**：我的插件从一个文件长成了好几个模块，还带着翻译和图片，想打包成一个文件发给别人，对方直接放进 `plugins/` 就能用。该怎么做？

插件有三种形态：单文件、目录和压缩文件。读完这一页，你能挑出合适的形态，把目录整理好，并打包出可以分发的文件。

刚开始写插件时，单文件就够用了。需要拆分代码、附带翻译或资源时，换成目录插件。要分发时，再把目录打包成压缩插件。

## 选择格式

| 格式                      | 元数据与入口                                                         | 安装方法                                              |
| ------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------- |
| 单文件 `.py`              | 模块级 `PLUGIN_METADATA` 字典，文件本身是入口。                      | 将 Python 文件放入实例插件目录。                      |
| 目录插件                  | 根目录的 `botqraft.plugin.json`，`entrypoint` 指向 Python 模块或包。 | 将完整插件目录放入实例插件目录。                      |
| `.mcdr` / `.pyz` 压缩插件 | 归档根目录的 `botqraft.plugin.json` 和入口模块。                     | 用 `botqraft pack` 生成归档，再直接放入实例插件目录。 |

开始之前，先准备一个已经初始化好的 BotQraft 实例。插件目录默认是实例里的 `plugins/`，也可以用 `plugin_directories` 修改，配置方法见[实例配置](../quick-start/configuration.md)。

`.mcdr` 和 `.pyz` 都可以看成装着插件的压缩包。包里的元数据、入口代码和资源要按 BotQraft 的约定摆放，这套摆放规则就叫"归档约定"。两种后缀用的是同一套归档约定，互换后缀不影响加载。

文件第一行以 `#!` 开头的解释器声明叫 shebang，例如 `#!/usr/bin/env python3`。加了 shebang 的归档，BotQraft 照样能加载。不过打包结果里没有 `__main__.py`，所以它不能当作独立程序直接运行；框架和机器人凭据都由运行实例提供。

单文件的写法见[第一个插件](first-plugin.md)，也可以直接复制 [Echo 示例](https://github.com/tanhHeng/BotQraftReforged/blob/main/example_plugins/echo.py)。

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

这里的插件 ID 和源码包目录都叫 `echo_plugin`。把插件回调写在 `echo_plugin/__init__.py` 里，再在元数据中设置 `"entrypoint": "echo_plugin"`。注意，插件根目录本身不要放 `__init__.py`，否则框架不会把这个目录当成插件；根目录下也不能有其他 Python 包。完整的字段说明见[元数据](metadata.md)。

如果代码是从单文件插件搬过来的，把元数据全部搬进 `botqraft.plugin.json`，并删掉 Python 文件里的 `PLUGIN_METADATA`。然后按需添加 `requirements.txt` 和资源目录。

### 翻译与资源

把翻译文件放在插件根目录的 `lang/` 里，和 Python 包目录并列。框架会自动找到并注册其中的 `.json`、`.yml`、`.yaml` 文件。如果翻译原本放在 Python 包里或 `resources/lang/` 下，把它们挪到根目录的 `lang/`。

翻译键是所有插件共用的，建议用插件 ID 作前缀，免得和其他插件冲突。打包时，记得把 `lang` 加进元数据的 `resources`：

```json
{
  "resources": ["assets", "lang"]
}
```

上面只是资源这一个字段，把它合并进完整的元数据即可。打包器会自动带上 `botqraft.plugin.json`、`requirements.txt`（如果有），以及和插件 ID 同名的源码目录。图片、帮助文件、翻译目录这类额外资源，再写进 `resources` 就好。

运行实例要能访问到入口模块、Python 依赖和资源。目录插件和压缩插件用 `server.open_bundled_file('assets/help.txt')` 读取只读资源，例如：

```python
from botqraft.api.types import QQPluginServerInterface

def read_help(server: QQPluginServerInterface) -> str:
    # Bundled resources are opened as binary files.
    with server.open_bundled_file('assets/help.txt') as stream:
        return stream.read().decode('utf-8')
```

需要保存的可写数据，放进 `server.get_data_folder()` 返回的 `config/<plugin_id>` 目录；归档只用来装分发的内容。单文件插件需要自己定位并读取外部资源文件。更多用法见[插件数据](data.md)和[多语言与用户偏好](translation.md)。

## 安装依赖

Python 第三方库写在插件根目录的 `requirements.txt` 里；插件之间的依赖则写在元数据的 `dependencies` 里，两者分开声明。

分发前，先在运行 BotQraft 的 Python 环境里装好依赖。在包含 `example/` 的工作目录下执行：

```sh
python -m pip install -r example/requirements.txt
```

框架加载插件时会检查这些要求，但安装依赖是部署这一步的事。压缩插件也一样，声明的 Python 库需要装进实例环境。把依赖说明和插件一起提供，使用者准备运行环境时会方便很多。

## 打包命令

打包其实就是收拾好输入目录、选一个输出位置，再决定文件名和要排除的开发文件。照下面几步走，很快就能得到可以安装的归档。

在包含 `example/` 的工作目录执行：

```sh
botqraft pack -i example -o packed_plugins
```

需要指定文件名和忽略规则时，可以这样写：

```sh
botqraft pack -i example -o packed_plugins -n "{id}-{version}.pyz" --ignore-patterns "__pycache__/" "*.pyc"
botqraft pack -i example -o packed_plugins --ignore-file .gitignore --shebang "/usr/bin/env python3"
```

各参数的作用如下：

1. **指定要打包的目录。** `-i` 指向带有 `botqraft.plugin.json` 的目录，省略时使用当前目录。如果你手上只有单文件代码，先按上面的目录结构整理好入口和 JSON 元数据。
2. **指定输出位置。** `-o` 指定输出目录，省略时使用当前目录；目录不存在会自动创建。
3. **决定文件名。** `-n` 会覆盖元数据里的默认文件名模板，同样可以使用 `{id}`、`{version}`。复制之前，先确认实际生成的文件名和扩展名。
4. **决定忽略哪些文件。** 默认读取输入目录里的 `.gitignore`；文件不存在也没关系，命令只会提示一行，然后照常打包。忽略规则是 gitignore 风格，相对插件输入目录匹配。`--ignore-patterns` 的优先级高于 `--ignore-file`，两个都设置时以前者为准。打包后检查一遍归档内容，把缓存、凭据和开发文件清理干净。
5. **需要时设置解释器行。** `--shebang` 设置可选的解释器行，只写 `#!` 后面的部分。打包功能直接复用了 BotQraft 所依赖的 MCDReforged 2.16.2 的实现，资源、requirements 和归档约定都和它一致，不需要另装 MCDR 命令行工具。

## 安装与更新

把实际生成的 `.mcdr` 或 `.pyz` 直接放进实例配置的插件目录，不要解压。然后启动实例；如果实例已经在运行，就执行下面的命令（控制台或超级管理员可用）：

```text
/botqraft plugin refresh
/botqraft plugin list
```

确认插件已经加载，就可以去 QQ 里试试它的功能了。之后修改了插件，就重新打包并替换旧归档。如果新归档的文件名和旧的相同，执行：

```text
/botqraft plugin reload echo_plugin
```

`reload` 会从原来的文件路径重新加载。不过默认文件名带着版本号，版本一变，文件名也会跟着变。这时先删除旧归档，再执行 `/botqraft plugin refresh`：它会卸载文件已经消失的插件，并加载新出现的文件。

如果 Echo 没有加载，别着急，先打开日志。优先看元数据、入口导入和依赖这三类提示，通常很快就能找到是哪一块还没准备好。

每个插件 ID 只保留一个可加载的副本。如果插件目录里有多个同 ID 的副本，只有先加载的那个生效，其余的会加载失败，并在日志里报告重复。所以切换到压缩插件时，记得把同 ID 的单文件或目录副本移出插件目录。

BotQraft 插件和 Minecraft 插件共用一部分打包格式，但各自面对的输入和宿主 API 不同。迁移之前，先读一读[MCDR 开发者路线](index.md#mcdr-开发者路线)。

接下来，翻翻[API 索引](api.md)，看看还有哪些公开接口可以用。
