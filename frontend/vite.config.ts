import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  server: {
    host: "0.0.0.0", // Required for Docker container access
    port: 5173,
    strictPort: true,

    proxy: {
      // Proxy all /api requests to the FastAPI backend.
      // This means browser requests never need to know the backend URL.
      // In Docker: api container is reachable as "api:8000"
      "/api": {
        target: "http://api:8000",
        changeOrigin: true,
        // Pass cookies through the proxy
        configure: (proxy) => {
          proxy.on("error", (err) => {
            console.error("[vite-proxy] error:", err.message);
          });
        },
      },
    },
  },

  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/tests/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/tests/**",
        "src/**/*.test.{ts,tsx}",
        "src/**/*.spec.{ts,tsx}",
        "src/main.tsx",
      ],
    },
  },

  build: {
    outDir: "dist",
    sourcemap: false, // No source maps in production builds
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          router: ["react-router-dom"],
          query: ["@tanstack/react-query"],
        },
      },
    },
  },
});
