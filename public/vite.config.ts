import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // ✅ 代理后端 API 请求到 http://localhost:5001
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        // ✅ 重写路径: /api/* 直接发送到后端 /api/*（不做路径转换）
        rewrite: (path) => path
      }
    }
  }
})