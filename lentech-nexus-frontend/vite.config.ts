import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Proxy API calls through the dev server so the browser only ever talks to
    // one origin. This keeps the session/CSRF cookies same-site (no CORS or
    // SameSite=Lax issues during development).
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
    },
  },
})
