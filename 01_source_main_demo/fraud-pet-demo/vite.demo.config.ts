import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// 镜像配置：用于展示「修正后主题」的最新后端（端口 8011）
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5181,
    host: '::',
    // 禁用 HMR WebSocket，避免 WorkBuddy 内置 Chromium 在连接本地 WS 时崩溃
    hmr: false,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8011',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 5178,
    host: '::',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8011',
        changeOrigin: true,
      },
    },
  },
  build: { emptyOutDir: false },
})
