import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    allowedHosts: true,
    proxy: {
      '/api/auth'          : { target: 'http://localhost:8001', changeOrigin: true },
      '/api/inscriptions'  : { target: 'http://localhost:8002', changeOrigin: true },
      '/api/paiements'     : { target: 'http://localhost:8002', changeOrigin: true },
      '/api/bibliotheque'  : { target: 'http://localhost:8002', changeOrigin: true },
      '/api/formations'    : { target: 'http://localhost:8003', changeOrigin: true },
      '/api/dossiers'      : { target: 'http://localhost:8003', changeOrigin: true },
      '/api/pieces'        : { target: 'http://localhost:8003', changeOrigin: true },
      '/api/deliberations' : { target: 'http://localhost:8004', changeOrigin: true },
      '/api/resultats'     : { target: 'http://localhost:8004', changeOrigin: true },
      '/api/attestations'  : { target: 'http://localhost:8005', changeOrigin: true },
      '/api/notifications' : { target: 'http://localhost:8006', changeOrigin: true },
      '/api/chatbot'       : { target: 'http://localhost:8006', changeOrigin: true },
      '/api/evaluer'       : { target: 'http://localhost:8007', changeOrigin: true },
      '/api/regles'        : { target: 'http://localhost:8007', changeOrigin: true },
      '/api/audit'         : { target: 'http://localhost:8008', changeOrigin: true },
    }
  }
})
