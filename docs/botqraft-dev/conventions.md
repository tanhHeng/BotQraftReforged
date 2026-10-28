# 代码与文档约定

这一页列出写 BotQraft 代码时要遵守的几条约定。读完你能让自己的改动和现有代码保持一致。

这些约定都能在仓库里找到现成例子，照着最近的提交写就不会跑偏。

## 用英文写代码，用翻译键写用户文字

日志、异常信息和注释一律用英文，源码里不出现中文字面量。
面向用户的文字不硬编码，写成翻译键，由翻译文件提供各语言版本。

翻译键以插件 ID 作为命名空间。插件 ID 为 `greet` 时，键写作 `greet.hello`，`lang/en_us.yml` 与 `lang/zh_cn.yml` 里都放这个键。
框架自己的键放在 `botqraft/resources/lang/`。完整写法见[多语言与用户偏好](../plugin-dev/translation.md)。

## 公开 API 用英文 Sphinx 字段式 docstring

公开接口的 docstring 用英文，字段语法固定为：

- 首段描述行为。
- `:param name:` 说明实际输入参数。
- `:return:` 说明返回结果。
- `:raises ExceptionType:` 记录明确的异常条件。

类型以函数签名为准，docstring 里省略 `:type:` 与 `:rtype:`。
零参数函数省略参数区块。只会以异常结束的拒绝操作，只记录异常条件。

```python
def escape_markdown(text: str) -> str:
    """Escape literal text for use in a QQ Markdown message.

    :param text: Literal text; HTML and Markdown special characters are escaped.
    :return: The escaped literal Markdown text.
    """
```

这段就是 `botqraft/message/qtext/text.py` 里的写法。带异常条件的例子可以看 `botqraft/plugin/si/qq_server_interface_mixin.py`。

## 类型注解

需要延迟注解求值时，在模块顶部写 `from __future__ import annotations`。
实例方法的第一个参数标注 `self: Self`，`Self` 从 `typing_extensions` 导入。

只在类型检查时需要的导入放进 `if TYPE_CHECKING:` 块，避免运行期循环导入。
包根目录的 `py.typed` 声明本包自带类型信息，别删掉它。

## 示例插件用解释性注释

`example_plugins/` 里的示例保留类型声明、模块来源、许可说明和必要的英文解释性注释。
示例函数以解释性注释为主，不写 API 式的参数与返回值 docstring。

拿不准注释写什么时，看 `example_plugins/echo.py`：它用注释说明命令路径与参数节点为什么这样写。

## 提交信息

`git log --oneline` 里的 29 条提交中，28 条是单行的 `<类型>: <英文祈使短句>`，没有正文。唯一的例外是早期加入许可证的那条。沿用这个格式：

| 类型       | 用于                 |
| ---------- | -------------------- |
| `feat`     | 新功能               |
| `fix`      | 修缺陷               |
| `refactor` | 不改变行为的重构     |
| `docs`     | 文档                 |
| `chore`    | 构建、依赖与仓库配置 |

例如 `feat: show built-in BotQraft command help`。摘要用英文祈使句，描述「做了什么」，不要写「修改了某某文件」。

仓库用 Vite Plus 管理提交前检查，配置在根目录的 `vite.config.ts`，钩子脚本 `.vite-hooks/pre-commit` 会对暂存文件执行 `vp check --fix`。
执行 `pnpm install` 时 `prepare` 脚本会通过 `vp config` 装好这些钩子。

接下来，如果你要改文档，读[文档站编写](docs.md)。
