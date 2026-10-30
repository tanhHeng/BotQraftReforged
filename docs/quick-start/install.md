# 安装 BotQraft

> [!NOTE]
> 我们假设你已经安装了 Python 3.10 或以上版本，并且已经熟悉基本的命令行操作。如果你还没有安装 Python，请先访问 [Python 官方网站](https://www.python.org/downloads/) 下载并安装适合你操作系统的版本。

## 环境依赖

- Python 3.10 及以上版本
- MCDReforged 2.16.2
- ruamel.yaml 0.17.23 及以上版本

一般来说，你不需要手动安装这些依赖，让我们直接使用 pip ！

## 开始安装

BotQraft 目前尚未发布到 PyPI，因此我们需要从源码安装。请依次执行以下命令：

```bash
# 克隆 BotQraft 仓库
git clone https://github.com/tanhHeng/BotQraftReforged.git
cd BotQraftReforged

# 安装 BotQraft
python -m pip install .

# 验证安装是否成功
botqraft --version
```

如果一切顺利，你应该会看到 BotQraft 的版本信息，比如`BotQraft 0.1.0`。此时，你已经成功安装了 BotQraft！

这次安装会把 BotQraft 装进当前 Python 环境，之后你可以在任意目录创建实例。

要在实例里放插件，可以看[添加插件](./add-plugins.md)。想改 BotQraft 源码本身，请改用可编辑安装，见[本地开发与验证](../botqraft-dev/setup.md)。

## 其他安装方式

如果你希望使用虚拟环境来隔离 BotQraft 的依赖——

~~——那么说明你已经是一位 Python 高手了！相信你可以自己解决的（XD）。~~
