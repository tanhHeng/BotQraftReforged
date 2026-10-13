# 配置并启动

读完这一页，你能用最少的几步把一个 BotCraft 实例跑起来，并看到它连上 QQ 开放平台。

如果你还没安装 BotCraft，请先看[安装 BotCraft](./install.md)。
如果你还没有 QQ 开放平台的 `AppID` 和 `AppSecret`，请先前往 [QQ 开放平台](https://open.qq.com/) 创建一个机器人，并取得相应凭据。

## 初始化

随便找一个空目录，执行下面的命令初始化 BotCraft 实例：

```bash
botcraft init
```

在源码目录里，`python -m botcraft init` 与它完全等价。

这个命令会在当前目录生成你的配置文件和插件目录。之后你就在这个目录里做开发和管理。

## 填入凭据

还记得你的 `AppID` 和 `AppSecret` 吗？打开 `config.yml`，把它们填进去：

```yaml
appid: "YOUR_APPID"
secret: "YOUR_APP_SECRET"
```

配置项不止这两个。自定义文件路径、启动检查和完整的常用配置表见[实例配置](./configuration.md)。

## 启动 BotCraft

执行下面的命令启动 BotCraft：

```bash
botcraft start
```

在源码目录里，`python -m botcraft` 与它完全等价。

稍等一会，如果你看到了 `BotCraft READY` 的日志输出，那么恭喜你，你已经成功启动 BotCraft 了！

接下来，[添加插件](./add-plugins.md)介绍怎么给实例装上第一个插件。
