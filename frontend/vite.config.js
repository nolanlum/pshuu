import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, '../static/js'),
    emptyOutDir: false,
    rollupOptions: {
      input: resolve(__dirname, 'src/frontend.jsx'),
      output: {
        format: 'iife',
        name: 'PshuuApp',
        entryFileNames: 'frontend.js',
        inlineDynamicImports: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
  },
})
