import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist-app',
  },
  server: {
    port: 5173,
    proxy: {
      '/upload': 'http://localhost:8000',
      '/mapping': 'http://localhost:8000',
      '/clean': 'http://localhost:8000',
      '/segment': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
    watch: {
      // Only watch src — avoids Vite scanning node_modules and the rest of the repo
      ignored: ['!**/src/**'],
    },
  },
  optimizeDeps: {
    // Pre-bundle heavy deps once so the dev server doesn't re-process them
    include: ['react', 'react-dom', 'recharts', 'zustand', 'axios'],
  },
})
