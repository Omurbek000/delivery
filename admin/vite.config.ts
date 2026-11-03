import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// В проде сборка раздаётся Django по /panel/ — ассеты должны жить там же.
// В дев-режиме Vite работает на своём порту, база обычная '/'.
export default defineConfig(({ mode }) => ({
  base: mode === 'production' ? '/panel/' : '/',
  plugins: [react()],
  server: {
    port: 5173,
  },
}))
