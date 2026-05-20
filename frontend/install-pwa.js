/**
 * Add to Home Screen prompt (iOS/Android) when browser supports it.
 */
(function () {
  "use strict";

  let deferredPrompt = null;

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    const btn = document.getElementById("install-pwa-btn");
    if (btn) btn.style.display = "inline-flex";
  });

  document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("install-pwa-btn");
    if (!btn) return;
    btn.addEventListener("click", async () => {
      if (!deferredPrompt) {
        alert(
          "To install: use Share → Add to Home Screen (iPhone) or browser menu → Install app (Android/Chrome)."
        );
        return;
      }
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      deferredPrompt = null;
      btn.style.display = "none";
    });
  });
})();
