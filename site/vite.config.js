import { defineConfig } from 'vite'

export default defineConfig({
  // Polling keeps reloads working in sandboxed shells without fs events.
  // BB Connect hostnames are allowed so the dev server can be shared.
  server: { watch: { usePolling: true, interval: 300 }, allowedHosts: ['.getbb.app'] },
  build: { chunkSizeWarningLimit: 700 },
})
