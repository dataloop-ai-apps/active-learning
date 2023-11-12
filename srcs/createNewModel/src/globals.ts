import { upperFirst, camelCase } from "lodash";

export default {
  install(app) {
    const components = import.meta.glob(
      "/node_modules/@dataloop-ai/components/src/components/**/*.vue",
      { eager: true }
    );

    for (const [path, module] of Object.entries(components)) {
      const componentName = upperFirst(
        camelCase(
          path
            .split("/")
            .pop()
            .replace(/\.\w+$/, "")
        )
      );
      app.component(`${componentName}`, (module as any).default);
    }
  },
};
