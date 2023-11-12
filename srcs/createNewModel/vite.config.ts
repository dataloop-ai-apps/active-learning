import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import Components from "unplugin-vue-components/vite";
import {
  AntDesignVueResolver,
  ElementPlusResolver,
  VantResolver,
} from "unplugin-vue-components/resolvers";
import viteBasicSslPlugin from "@vitejs/plugin-basic-ssl"

// https://vitejs.dev/config/
export default defineConfig({
  base: "",
  server: {
  host:"0.0.0.0",
    port: 3004,
    https: true
  },
  plugins: [
    viteBasicSslPlugin(),
    vue(),
    Components({
      dirs: [
        'src/components',
        'node_modules/@dataloop-ai/components/src/components'
      ],
      include: 'node_modules/@dataloop-ai/components/src/components',
      resolvers: [
        AntDesignVueResolver(),
        ElementPlusResolver(),
        VantResolver(),
      ],
    }),
  ],
});
