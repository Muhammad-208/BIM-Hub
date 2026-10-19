import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// dev: npm run dev  (UI on :5173, API proxied to `bimhub studio` on :8800)
// build: npm run build → ../mcp-layer/src/bimhub/studio/ui (served by the API, and loaded by the Tauri shell)
export default defineConfig({
  plugins: [react()],
  base: './',
  server: { port: 5173, proxy: { '/api': 'http://127.0.0.1:8800' } },
  build: { outDir: 'dist', emptyOutDir: true, chunkSizeWarningLimit: 1500 }
})
