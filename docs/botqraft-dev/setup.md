# 本地开发与验证

这一页讲怎么在本机装好开发环境、跑通本地检查，并把改动验证到可以提交。读完你能独立复现一次完整的本地验证。

需要 Python 3.10 或以上版本，下面的命令都在源码根目录执行。

## 安装开发依赖

```bash
python -m pip install -e .
python -m pip install -r requirements.dev.txt
```

这里用可编辑安装（`-e`）。装好后 Python 导入的是你正在改的源码目录，改完不用重装就生效。

`requirements.txt` 里是运行时依赖：MCDReforged 2.14.4、aiohttp 与 ruamel.yaml。`requirements.dev.txt` 在此基础上加上 `build`。

依赖没有写版本上界，`ruamel.yaml` 会装到当前最新版。如果你在验证兼容区间，请显式钉版本。

BotQraft 独立运行，MCDR 只作为 Python 依赖安装。你不需要另外搭一个 MCDR 服务端。

## 运行能力探测

```bash
python -m botqraft.compatibility.probes
```

探测在临时目录里运行，只使用本地环境和探测用插件，成功时退出码为 0。
它回答的是「本机运行时是否可用」，不验证账号权限，也不验证 QQ 平台接口。

`botqraft start` 会在启动前自动做同一次检查，结果按 BotQraft 与 MCDR 版本缓存在 `config/botqraft/capabilities.json`。
加 `--check-capabilities` 可以忽略缓存强制重跑。

## 运行本地回归测试

`tests/` 被仓库的 `.gitignore` 忽略，所以它只存在于带着这份目录的本地副本里。先确认根目录下确实有 `tests/`，再执行：

```bash
python -m unittest discover -s tests -v
```

这套测试覆盖控制台补全、网关日志、示例插件、延迟翻译、消息命令和面板分页等本地行为。
收件日志与原始响应日志也有对应用例。
发行包和其他源码副本可能没有这个目录，请按实际情况记录验证范围。

只有真的跑过，才能在记录里写「回归验证已完成」。

## 构建发行包

```bash
python -m build
```

构建完成后 `dist/` 里会生成源码包和 wheel。wheel 会带上 `py.typed`、`resources/*.yml` 与 `resources/lang/*.yml`。

版本的唯一来源是 `botqraft/constants/core_constant.py` 里的 `VERSION`，`pyproject.toml` 从它读取。不要在别处再写一遍版本号。

## 验证文档示例

改完源码后，用下面三个示例确认公开接口还能用。

### Echo 插件

把[第一个插件](../plugin-dev/first-plugin.md)里的 Echo 保存成实例的 `plugins/echo.py`，也可以直接用仓库里的 [`example_plugins/echo.py`](https://github.com/BotQraftReforged/BotQraftReforged/blob/main/example_plugins/echo.py)。

启动实例后，在群聊或 C2C 发送 `/echo Hello world`，检查实际回复。同一个插件 ID 只保留一份加载入口，两种方式选一种即可。

### 消息烟测

[Markdown、文本交互与键盘](../plugin-dev/markdown.md)里的代码是离线消息构造烟测。把它保存为 `message_smoke.py` 后执行：

```bash
python message_smoke.py
```

示例只验证编码字段，最后打印英文完成提示。这一步不需要 QQ 凭据。

### 压缩插件

按[插件格式](../plugin-dev/plugin-format.md)生成压缩插件，把产物放进实例的插件目录，再启动实例。
然后执行：

```text
/botqraft plugin list
```

看到实例识别到实际打包产物，就说明打包流程可用。

## 记录验证范围

上面的命令和示例给出的是验证方法，不是验证结果。执行后请记下实际跑过的步骤与输出，再把它列为已验证。

本地通过只代表本地通过。账号权限、平台接口和群聊、C2C 的实际表现要在真实 QQ 环境里另行确认，部署步骤见[快速上手](../quick-start/index.md)。

接下来，读[代码与文档约定](conventions.md)，让你的改动和现有代码保持一致。
