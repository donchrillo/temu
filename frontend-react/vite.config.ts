import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      // TOCI Portal: Manifest mit Cookie abrufen (sonst Login-Weiterleitung statt Icon).
      useCredentials: true,
      includeAssets: ['icon-192.png', 'icon-512.png', 'icon-maskable-512.png'],
      manifest: {
        name: 'Temu Sync',
        short_name: 'Temu Sync',
        description: 'Abgleich JTL ↔ Temu-Marktplatz',
        theme_color: '#007AFF',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
        scope: '/',
        lang: 'de',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // TOCI Portal: Seiten immer übers Netz holen, nie aus dem Service Worker – sonst sieht
        // Caddy den Aufruf nicht und weder Portal noch Cloudflare Access können umleiten.
        // JS/CSS/Icons bleiben gespeichert.
        navigateFallback: null,
        globIgnores: ['**/index.html'],
        runtimeCaching: [
          {
            urlPattern: /^\/api\//,
            handler: 'NetworkOnly',
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 8501,
    strictPort: true,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8401',
        changeOrigin: true,
      },
    },
  },
})
