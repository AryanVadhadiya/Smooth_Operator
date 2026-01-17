import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@services': path.resolve(__dirname, './src/services'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@mock': path.resolve(__dirname, './src/mock'),
      '@utils': path.resolve(__dirname, './src/utils'),
    },
  },
  server: {
    port: 5173,
    host: true,
  },
})
