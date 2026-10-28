# 文档站编写

这一页讲文档站怎么组织、页面怎么写。读完你能自己新增或修改一页文档，并让它在导航里出现。

文档站用 VitePress 构建。页面是 `docs/` 下的 Markdown，站点配置在 `docs/.vitepress/config.mts`。

## 栏目分工

| 目录                 | 写给谁                       |
| -------------------- | ---------------------------- |
| `docs/quick-start/`  | 想部署并跑起一个实例的用户   |
| `docs/plugin-dev/`   | 想写插件的插件开发者         |
| `docs/botqraft-dev/` | 想改框架、示例或文档的贡献者 |

一个内容只写在一个栏目里。用户文档回答「怎么用」，开发文档回答「为什么这样实现、想改该怎么改」。
`docs/index.md` 是首页，用的是 VitePress 的首页布局，里面的 `hero` 与 `features` 直接在 frontmatter 里写。

## 目录与导航

`config.mts` 里有两处决定页面的可见位置：

- `themeConfig.nav` 是顶部导航，`text` 是显示名，`link` 指向栏目首页。
- `themeConfig.sidebar` 是左侧目录，每个栏目一组，组内每项写 `{ text, link }`。页面较多的栏目可以再分小组：小组只写 `{ text, items }`，例如插件开发按“先跑起来”“命令与回复”等任务分组。

新增页面时，除了写 Markdown 文件，还要在对应的 sidebar 分组里加一条。否则页面存在但没人能从导航点进去。
sidebar 里的 `link` 写站点绝对路径，不带 `.md`，例如 `/botqraft-dev/setup`。
页面之间互相引用用相对路径加 `.md`，例如 `./setup.md` 或 `../plugin-dev/index.md`。

改了小标题就顺手改掉引用该锚点的链接，构建时会校验锚点是否存在。

## 插件开发页面的开头

`docs/plugin-dev/` 的每一页（栏目首页除外）在标题下先写一句场景，再写“读完这一页……”。场景用读者的口吻提一个具体需求，用引用块和统一的标签：

```md
> **场景**：我写好了 `/echo`，想让它出现在 QQ 的指令面板里。该怎么做？
```

场景里的需求要能在这一页找到完整做法，不要写本页解决不了的事。

## 本地预览

仓库根目录的 `package.json` 提供三个脚本，依赖用 pnpm 管理：

```bash
pnpm install
pnpm docs:dev
pnpm docs:build
pnpm docs:preview
```

`docs:dev` 起本地预览并热更新，`docs:build` 生成静态站点，`docs:preview` 预览构建产物。
构建产物与缓存写在 `docs/.vitepress/dist` 和 `docs/.vitepress/cache`，两者已被忽略。

## 代码高亮

代码块开头写语言名。在花括号里写行号可以突出某几行，例如 `{4}` 突出第 4 行：

````md
```js{4}
export default {
  data () {
    return {
      msg: 'Highlighted!'
    }
  }
}
```
````

渲染结果如下：

```js{4}
export default {
  data () {
    return {
      msg: 'Highlighted!'
    }
  }
}
```

## 提示容器

用 `:::` 包住一段内容就能创建提示框：

```md
::: tip
把完整插件目录复制到运行实例的 plugins/ 中。
:::
```

按内容选类型，可用的有 `info`、`tip`、`warning`、`danger` 和 `details`。

::: info
这里适合放补充说明。
:::

::: tip
这里适合放操作建议。
:::

::: warning
执行覆盖操作前，请先备份目标文件。
:::

::: danger
这里适合说明可能造成数据丢失的操作。
:::

::: details 查看更多
`details` 可以带标题，适合放可展开的详细步骤。
:::

更多语法见 [VitePress Markdown 扩展](https://vitepress.dev/guide/markdown)。

## 读取页面数据

页面里可以用 `useData()` 读取主题配置、页面信息和 frontmatter。Markdown 页面和 Vue 组件都能用：

```md
<script setup>
import { useData } from 'vitepress'

const { theme, page, frontmatter } = useData()
</script>

## 主题配置

<pre>{{ theme }}</pre>

## 页面信息

<pre>{{ page }}</pre>

## Frontmatter

<pre>{{ frontmatter }}</pre>
```

`theme` 是主题配置，`page` 是当前页面信息，`frontmatter` 是页面头部的 frontmatter。
想要更长的右侧大纲，可以在 frontmatter 里写 `outline: deep`。

更多字段见 [VitePress 运行时 API](https://vitepress.dev/reference/runtime-api#usedata)。

接下来，回到[栏目首页](index.md)挑一个方向，或者读[插件开发](../plugin-dev/index.md)了解插件侧的公开契约。
