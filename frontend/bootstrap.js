/**
 * Pre-flight: warn if FastAPI backend is not reachable.
 */
(function () {
  "use strict";

  function backendUrl() {
    const meta = document.querySelector('meta[name="backend-url"]');
    if (meta?.content) return meta.content.replace(/\/$/, "");
    if (window.__BACKEND_URL__) return window.__BACKEND_URL__.replace(/\/$/, "");
    return "https://social-media-agent-production-b566.up.railway.app";
  }

  async function check() {
    const base = backendUrl();
    if (!base) return;
    try {
      const r = await fetch(`${base}/ping`, { signal: AbortSignal.timeout(4000) });
      if (!r.ok) throw new Error("bad status");
    } catch {
      document.addEventListener("DOMContentLoaded", () => {
        const el = document.getElementById("offline-banner");
        if (!el) return;
        el.textContent = "Backend connecting... please wait.";
        el.classList.add("visible");
        el.style.background = "linear-gradient(90deg, #f87171, #ef4444)";
        el.style.color = "#fff";
      });
    }
  }

  check();
})();