# BotQraftReforged

**中文** | [English](README_en.md)

> 一个基于 [MCDReforged](https://github.com/MCDReforged/MCDReforged) 的、适配官方 QQ 机器人的开发框架。

BotQraftReforged 继承了 MCDR 的插件开发、指令管理、权限管理等方便的功能。你可以像开发 MCDR 插件一样开发 BotQraft 插件，同时使用面向 QQ 的消息与事件接口。

“Reforged” 既指 BotQraft 是 MCDR 的“重铸”，也是感谢与赞美 MCDR 的优秀设计。发行包名、Python import 命名空间和命令行入口均为 `botqraft`。

## 特点

- 独立运行，使用官方 QQ 机器人网关与 HTTP API，支持群聊和 C2C。
- 复用 MCDR 的插件生命周期、命令树、权限与翻译能力。
- 提供被动回复、文本、Markdown、键盘及帮助面板等 QQ 接口。
- 支持单文件、目录和压缩插件，便于开发与分发。

需要 **Python 3.10 或以上**。MCDR 2.14.4 是代码依赖，不是宿主；无需 Minecraft 服务端。

## 文档

访问 [https://botqraft.tanh.moe/](https://botqraft.tanh.moe/) 查看完整文档。
