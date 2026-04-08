import path from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/vite'

const rootEnvDir = path.resolve(__dirname, '../../..')

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, rootEnvDir, '')
  const gatewayPort = env.GATEWAY_PORT || '8080'
  const devProxyTarget = env.VITE_DEV_PROXY_TARGET || `http://localhost:${gatewayPort}`

  return {
    envDir: rootEnvDir,
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/api': {
          target: devProxyTarget,
          changeOrigin: true,
        },
        '/actuator': {
          target: devProxyTarget,
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: '0.0.0.0',
      port: 4173,
    },
  }
})
