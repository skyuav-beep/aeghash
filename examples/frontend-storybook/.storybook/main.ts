import type { StorybookConfig } from "@storybook/react-vite";

const config: StorybookConfig = {
  stories: ["../src/stories/**/*.stories.@(ts|tsx)"],
  addons: [
    "@storybook/addon-links",
    "@storybook/addon-essentials",
    "@storybook/addon-a11y",
    "@storybook/addon-interactions",
    "@storybook/addon-viewport"
  ],
  framework: {
    name: "@storybook/react-vite",
    options: {}
  },
  async viteFinal(viteConfig) {
    if (process.env.STORYBOOK_COVERAGE) {
      const { default: istanbul } = await import("vite-plugin-istanbul");
      const plugins = Array.isArray(viteConfig.plugins) ? viteConfig.plugins : [];
      plugins.push(
        istanbul({
          include: ["src/components/**/*", "src/stories/**/*"],
          extension: [".ts", ".tsx"],
          cypress: false,
          requireEnv: false,
          forceBuildInstrument: true
        })
      );
      viteConfig.plugins = plugins;
    }
    return viteConfig;
  },
  docs: {
    autodocs: "tag"
  }
};

export default config;
