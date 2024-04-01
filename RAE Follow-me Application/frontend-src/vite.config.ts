import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    sourcemap: true,
    outDir: './frontend',
    rollupOptions: {
      output: {
        manualChunks: {
          mui: ['@mui/material']
        }
      },
      input: {
        main: './index.html',
      },
    },
  },
});