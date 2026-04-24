import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    historyApiFallback: true,
    port: 5173,
    proxy: {
      '/ask': 'http://localhost:8000',
      '/priority': 'http://localhost:8000',
      '/store': 'http://localhost:8000',
      '/search': 'http://localhost:8000',
      '/ingest': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
