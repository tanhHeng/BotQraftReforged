import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "BotCraftReforged",
  description: "A framework for developing official QQ bots, built on MCDReforged",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: "主页", link: "/" },
      { text: "快速上手", link: "/quick-start" },
      { text: "API Examples", link: "/api-examples" },
    ],

    sidebar: [
      {
        text: "快速上手",
        items: [
          { text: "什么是 BotCraft", link: "/quick-start/intro" },
          { text: "安装", link: "/quick-start/install" },
          { text: "配置并启动", link: "/quick-start/start" },
          { text: "添加插件", link: "/quick-start/add-plugins" },
        ],
      },
    ],

    socialLinks: [{ icon: "github", link: "https://github.com/vuejs/vitepress" }],
  },
});
