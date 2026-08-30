import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Tailwind is part of the setup but all visual styling is done with custom CSS.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5178,
    strictPort: false,
  },
})
