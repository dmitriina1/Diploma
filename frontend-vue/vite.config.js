import { fileURLToPath, URL } from 'node:url'
import {defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8000'
const wsTarget = process.env.VITE_WS_PROXY_TARGET || 'ws://localhost:8000'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true
      },
      '/ws': {
        target: wsTarget,
        ws: true
      }
    }
  }
})
