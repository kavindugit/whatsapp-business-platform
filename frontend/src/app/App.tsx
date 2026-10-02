/**
 * App.tsx
 * Root application component with router setup.
 * Full routing will be wired in Day 5 when all page components exist.
 * For Day 1, this renders a minimal placeholder that confirms the stack is running.
 */
import type { FC } from "react";

const App: FC = () => {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        gap: "1rem",
        fontFamily: "Inter, sans-serif",
        background: "var(--color-surface-0)",
        color: "var(--color-text-primary)",
      }}
    >
      <div
        style={{
          width: 56,
          height: 56,
          background: "linear-gradient(135deg, #22c55e, #16a34a)",
          borderRadius: 16,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 28,
          boxShadow: "0 0 30px rgba(34,197,94,0.3)",
        }}
      >
        💬
      </div>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>
        WhatsApp Business Platform
      </h1>
      <p style={{ color: "var(--color-text-secondary)", fontSize: "0.875rem" }}>
        Week 1 — Day 1 scaffold running ✓
      </p>
      <p style={{ color: "var(--color-text-muted)", fontSize: "0.75rem" }}>
        Full dashboard coming Day 5. Check{" "}
        <code
          style={{
            background: "var(--color-surface-3)",
            padding: "0.1em 0.4em",
            borderRadius: 4,
          }}
        >
          /api/health/live
        </code>{" "}
        for API status.
      </p>
    </div>
  );
};

export default App;
