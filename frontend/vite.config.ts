import { defineConfig } from 'vite'
import solid from 'vite-plugin-solid'
import Icons from 'unplugin-icons/vite'

export default defineConfig({
  plugins: [solid(), Icons({compiler: 'solid', autoInstall: true}), ],
  server: {
    port: 13913,
    strictPort: true,
  }
})
