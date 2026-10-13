import { defineConfig } from "vitepress";

export default defineConfig({
  title: "BotCraftReforged",
  description: "适配官方 QQ 机器人的开发框架，基于 MCDReforged 构建。",
  lang: "zh-CN",
  themeConfig: {
    nav: [
      { text: "主页", link: "/" },
      { text: "快速上手", link: "/quick-start/" },
      { text: "插件开发", link: "/plugin-dev/" },
    ],
    sidebar: [
      {
        text: "快速上手",
        link: "/quick-start/",
        items: [
          { text: "什么是 BotCraft", link: "/quick-start/intro" },
          { text: "安装 BotCraft", link: "/quick-start/install" },
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
          { text: "基本知识", link: "/plugin-dev/basic" },
          { text: "元数据", link: "/plugin-dev/metadata" },
          { text: "插件格式", link: "/plugin-dev/plugin-format" },
          { text: "插件事件", link: "/plugin-dev/events" },
          { text: "事件与消息格式", link: "/plugin-dev/message-format" },
          { text: "响应事件与回复消息", link: "/plugin-dev/reply" },
          { text: "命令系统", link: "/plugin-dev/commands" },
          { text: "SimpleCommandBuilder", link: "/plugin-dev/simple-command-builder" },
          { text: "命令树", link: "/plugin-dev/command-tree" },
          { text: "帮助消息与指令面板", link: "/plugin-dev/help" },
          { text: "第一个插件", link: "/plugin-dev/first-plugin" },
          { text: "权限系统", link: "/plugin-dev/permissions" },
          { text: "交互事件与按钮响应", link: "/plugin-dev/interactions" },
          { text: "Markdown、文本交互与键盘", link: "/plugin-dev/markdown" },
          { text: "翻译与用户语言", link: "/plugin-dev/translation" },
          { text: "插件数据与打包资源", link: "/plugin-dev/data" },
          { text: "后台任务与卸载", link: "/plugin-dev/tasks" },
          { text: "主动发送、引用与撤回", link: "/plugin-dev/sending" },
          { text: "API 索引", link: "/plugin-dev/api" },
          { text: "今日人品示例", link: "/plugin-dev/jrrp-plugin" },
        ],
      },
    ],
    socialLinks: [{ icon: "github", link: "https://github.com/BotCraftReforged/BotCraftReforged" }],
  },
});
