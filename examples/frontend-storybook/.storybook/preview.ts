import "../tokens.css";
import "../src/styles/auth.css";

import type { Preview } from "@storybook/react";

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: "^on[A-Z].*" },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i
      }
    },
    a11y: {
      element: "#storybook-root",
      config: {},
      options: {}
    }
  }
};

export default preview;
