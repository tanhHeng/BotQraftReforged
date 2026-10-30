import { defineConfig } from "vitepress";

const base = process.env.VITEPRESS_BASE || "/";

export default defineConfig({
  base,
  title: "BotQraftReforged",
  description: "适配官方 QQ 机器人的开发框架，基于 MCDReforged 构建。",
  lang: "zh-CN",
  head: [["link", { rel: "icon", href: `${base}favicon.ico` }]],
  themeConfig: {
    logo: "/icon.png",
    nav: [
      { text: "主页", link: "/" },
      { text: "快速上手", link: "/quick-start/" },
      { text: "插件开发", link: "/plugin-dev/" },
      { text: "BotQraft 开发", link: "/botqraft-dev/" },
    ],
    sidebar: [
      {
        text: "快速上手",
        link: "/quick-start/",
        items: [
          { text: "什么是 BotQraft", link: "/quick-start/intro" },
          { text: "安装 BotQraft", link: "/quick-start/install" },
          { text: "配置并启动", link: "/quick-start/start" },
          { text: "添加插件", link: "/quick-start/add-plugins" },
          { text: "实例配置", link: "/quick-start/configuration" },
          { text: "日志与运维", link: "/quick-start/operations" },
        ],
      },
      {
        text: "插件开发",
        link: "/plugin-dev/",
        items: [
          {
            text: "让我们开始吧！",
            items: [
              { text: "第一个插件", link: "/plugin-dev/first-plugin" },
              { text: "插件是怎么运行的", link: "/plugin-dev/basic" },
            ],
          },
          {
            text: "命令与回复",
            items: [
              { text: "注册命令", link: "/plugin-dev/commands" },
              { text: "回复消息", link: "/plugin-dev/reply" },
              { text: "帮助消息与指令面板", link: "/plugin-dev/help" },
              { text: "权限系统", link: "/plugin-dev/permissions" },
              { text: "复杂命令：命令树", link: "/plugin-dev/command-tree" },
            ],
          },
          {
            text: "响应非命令消息",
            items: [
              { text: "监听消息与事件", link: "/plugin-dev/events" },
              { text: "读取消息内容", link: "/plugin-dev/message-format" },
              { text: "主动发送、引用与撤回", link: "/plugin-dev/sending" },
            ],
          },
          {
            text: "不同类型的消息",
            items: [
              { text: "发送图片、视频和文件", link: "/plugin-dev/media" },
              { text: "Markdown 消息与文本交互", link: "/plugin-dev/markdown" },
              { text: "按钮：键盘与点击响应", link: "/plugin-dev/interactions" },
              { text: "多语言与用户偏好", link: "/plugin-dev/translation" },
            ],
          },
          {
            text: "插件工程",
            items: [
              { text: "插件数据与打包资源", link: "/plugin-dev/data" },
              { text: "后台任务与卸载", link: "/plugin-dev/tasks" },
              { text: "元数据", link: "/plugin-dev/metadata" },
              { text: "插件格式、打包与发布", link: "/plugin-dev/plugin-format" },
            ],
          },
          {
            text: "参考与示例",
            items: [
              { text: "API 索引", link: "/plugin-dev/api" },
              { text: "今日人品示例", link: "/plugin-dev/jrrp-plugin" },
              { text: "用 AI Agent 开发插件", link: "/plugin-dev/agents" },
            ],
          },
        ],
      },
      {
        text: "BotQraft 开发",
        link: "/botqraft-dev/",
        items: [
          { text: "框架结构", link: "/botqraft-dev/architecture" },
          { text: "本地开发与验证", link: "/botqraft-dev/setup" },
          { text: "代码与文档约定", link: "/botqraft-dev/conventions" },
          { text: "文档站编写", link: "/botqraft-dev/docs" },
          { text: "用 AI Agent 开发框架", link: "/botqraft-dev/agents" },
        ],
      },
    ],
    socialLinks: [{ icon: "github", link: "https://github.com/tanhHeng/BotQraftReforged" }],
  },
});
