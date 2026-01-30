import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Parse VITE_ALLOWED_HOSTS env var for remote access
// Example: VITE_ALLOWED_HOSTS="myhost.example.edu,192.168.1.100"
const parseAllowedHosts = (): string[] => {
  const envHosts = process.env.VITE_ALLOWED_HOSTS
  if (envHosts) {
    const hosts = envHosts.split(',').map(s => s.trim()).filter(Boolean)
    if (hosts.length > 0) {
      return hosts
    }
  }
  // Default: local development only
  return ['localhost', '127.0.0.1']
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // allowedHosts controls which Host header values are accepted
    // Set VITE_ALLOWED_HOSTS for remote access
    allowedHosts: parseAllowedHosts(),
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
