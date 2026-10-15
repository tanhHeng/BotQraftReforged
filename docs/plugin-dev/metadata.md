# 元数据

读完这一页，你能为插件选出 ID，写出版本和入口，并声明依赖与资源。

元数据就是插件的身份证。框架会用它认出你的插件、确认它依赖哪些东西，也会根据这些信息准备可分发的压缩包。

写元数据时先选 ID，再写其他字段。ID 是插件在框架里的唯一名字，它决定 `config/<id>` 数据目录的位置，也是其他插件声明依赖时使用的名字。ID 会同时出现在数据目录和依赖声明里，所以最好一开始就选一个稳定、好认的名字。选好之后，后面的目录结构会轻松很多。

## 选择声明位置

三种插件形态的元数据位置不同：

| 插件格式                  | 声明位置                                   |
| ------------------------- | ------------------------------------------ |
| 单文件 `.py`              | Python 模块顶层的 `PLUGIN_METADATA` 字典。 |
| 目录插件                  | 插件根目录的 `botqraft.plugin.json`。      |
| `.mcdr` / `.pyz` 压缩插件 | 归档根目录的 `botqraft.plugin.json`。      |

JSON 元数据沿用 MCDR Metadata 格式，文件名使用 BotQraft 的约定。把单文件插件整理为目录插件时，把元数据统一放入 JSON，并移除入口 Python 文件中的 `PLUGIN_METADATA`。

## 声明单文件元数据

在插件文件中加入下面的字典：

```python
PLUGIN_METADATA = {
    'id': 'echo_plugin',
    'version': '1.0.0',
    'name': 'Echo',
    'description': 'Reply with the supplied text',
    'author': ['Your Name'],
    'dependencies': {'botqraft': '>=0.1.0'},
}
```

单文件插件的入口就是这个 Python 文件。目录与压缩插件通过下面的 JSON 指定入口。

## 声明目录与压缩插件元数据

在插件根目录创建 `botqraft.plugin.json`：

```json
{
  "id": "echo_plugin",
  "version": "1.0.0",
  "name": "Echo",
  "description": {
    "en_us": "Reply with the supplied text",
    "zh_cn": "复述提供的文本"
  },
  "author": ["Your Name"],
  "link": "https://botqraft.tanh.moe/plugin-dev/",
  "entrypoint": "echo_plugin",
  "dependencies": {
    "botqraft": ">=0.1.0"
  },
  "resources": ["assets", "lang"],
  "archive_name": "{id}-v{version}"
}
```

把 `link` 换成插件实际的项目地址。按需保留作者、链接和资源字段。上例的入口代码放在 `echo_plugin/__init__.py`，完整目录见[插件格式](plugin-format.md)。

## 完整字段

下面是元数据解析和打包用到的全部字段。第二列说明字段类型，以及省略这个字段后会发生什么：

| 字段           | 类型与省略后的行为                                             | 用途                                                                                     |
| -------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `id`           | 字符串；发布时必须填写，且要符合 ID 规则。                     | 插件唯一标识。插件依赖、运维命令和 `config/<id>` 数据目录都用它。                        |
| `version`      | 版本字符串；缺失或无法解析时回退为原生默认值 `0.0.0`。         | 框架按这个版本检查插件依赖约束。发布时填写明确版本，如 `1.0.0`。                         |
| `name`         | 字符串；省略时等于 `id`。                                      | 插件展示名称，也参与省略归档模板时的默认文件名。                                         |
| `description`  | 字符串，或语言代码到字符串的字典；省略时没有描述。             | 展示描述。普通硬编码文本使用英文，多语言描述使用语言字典。运行时用户反馈通过翻译键提供。 |
| `author`       | 作者字符串或字符串列表；省略时没有作者，单个字符串会转成列表。 | 声明插件作者，推荐统一使用列表。                                                         |
| `link`         | 字符串；省略时没有链接。                                       | 插件主页、仓库或发布页地址。                                                             |
| `entrypoint`   | Python 模块名字符串；省略时等于 `id`。                         | 目录及压缩插件的入口模块，使用点分模块路径。                                             |
| `dependencies` | 插件 ID 到版本约束字符串的映射；省略时为空 `{}`。              | 声明框架及其他插件的依赖。                                                               |
| `resources`    | 相对插件根目录的资源路径列表；省略时为空 `[]`。                | 打包时加入归档的资源目录或文件。                                                         |
| `archive_name` | 文件名模板字符串；省略时由打包命令生成名称。                   | 设置默认归档文件名，可使用 `{id}`、`{version}`，由 `-n` 覆盖。                           |

### ID 与入口

ID 使用 `[a-z][a-z0-9_]{0,63}` 格式。它以小写英文字母开头，总长 1–64 字符，后续字符使用小写英文字母、数字或下划线。挑一个和其他插件区分得开的 ID，并且长期保持稳定。

目录及压缩插件的 `entrypoint` 使用 `id` 本身，或 `id` 下的子模块。例如 ID 为 `echo_plugin` 时，可以使用 `echo_plugin` 或 `echo_plugin.main`。对应代码分别放在 `echo_plugin/__init__.py` 或 `echo_plugin/main.py`。

保持源码包目录与插件 ID 一致。打包命令自动收集根目录下以 ID 命名的源码目录。

### 依赖

框架自身的插件 ID 写作 `botqraft`。`mcdr` 表示另一个依赖 ID，声明 BotQraft 版本要求时使用 `botqraft`。

```json
{
  "dependencies": {
    "botqraft": ">=0.1.0",
    "another_plugin": ">=1.0.0"
  }
}
```

依赖后面的版本写法沿用 MCDR 的规则，例如 `>=1.0.0`。它的意思是：运行实例里要有不低于这个版本的插件。把要求写清楚，框架就能在加载前帮你检查。

版本字符串使用具体版本，通配要求留给依赖约束。

Python 第三方库写在 `requirements.txt` 中，与插件依赖分别声明。先在运行实例使用的 Python 环境中安装这些库，框架加载插件时负责检查要求。安装步骤见[插件格式](plugin-format.md#安装依赖)。

### 资源与归档名称

把翻译目录 `lang` 和其他只读资源列入 `resources`，它们就会随插件归档一起分发。运行时用 `server.open_bundled_file('assets/help.txt')` 读取这些资源。需要保存的可写数据放进 `server.get_data_folder()` 返回的目录。

`archive_name` 使用 `{id}`、`{version}` 替换插件 ID 和版本。省略模板时，打包命令使用去掉空格的展示名称和版本生成 `<name>-v<version>`。展示名称为空时改用 ID。名称缺少受支持的后缀时，命令会追加 `.mcdr`。使用 `.pyz` 时，在模板或 `-n` 中显式填写后缀。

接下来，按[插件格式](plugin-format.md)整理目录并打包分发。
