# BotCraft 开发

这一页面向 BotCraft 本身的贡献者。读完你能知道可以从哪些方向参与，以及接下来该读哪一页。

想给框架提交代码、想改造运行流程、想补文档，都在这个栏目里。只想让机器人多一个功能的话，请从[插件开发](../plugin-dev/index.md)开始。

## 这个栏目服务谁

- 要改 `botcraft/` 里框架代码的维护者。
- 要新增或修正示例插件的贡献者。
- 要维护文档站的贡献者。

只写插件不需要动框架代码。插件能看到的公开契约在[插件开发](../plugin-dev/index.md)，那是插件开发者的边界。

## 你可以参与的方向

| 方向           | 从哪里入手                                                |
| -------------- | --------------------------------------------------------- |
| 框架代码       | `botcraft/` 下的各子包，职责见[框架结构](architecture.md) |
| 示例与内置插件 | `example_plugins/`、`botcraft/plugin/builtin/`            |
| 文档           | `docs/` 下的 Markdown 与 `docs/.vitepress/config.mts`     |

仓库根目录的 `LICENSE` 是 LGPL-3.0，框架代码按它分发。`example_plugins/` 里的迁移插件可能带自己的许可，例如 `qq_jrrp` 是 GPL-3.0-only。

## 栏目导航

- [框架结构](architecture.md)：各子包的职责，以及一次启动的完整顺序。
- [本地开发与验证](setup.md)：装开发依赖、跑能力探测与回归测试、构建发行包。
- [代码与文档约定](conventions.md)：代码语言、docstring、示例注释与提交信息。
- [文档站编写](docs.md)：栏目分工、导航配置、Markdown 扩展与页面数据。

接下来，先了解[框架结构](architecture.md)。
