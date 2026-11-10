import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// В проде сборку раздаёт Django с корня сайта, в дев-режиме — на 5174.
export default defineConfig({
  base: '/',
  plugins: [react()],
  server: {
    port: 5174,
  },
})
