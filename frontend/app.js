/**
 * PWA UI — calls Railway FastAPI backend.
 * BACKEND_URL: set via meta tag, window config, or localStorage (non-secret).
 */

(function () {
  "use strict";

  // Resolve backend URL (Vercel injects via build or user sets once)
  function getBackendUrl() {
    const meta = document.querySelector('meta[name="backend-url"]');
    if (meta?.content) return meta.content.replace(/\/$/, "");
    if (window.__BACKEND_URL__) return window.__BACKEND_URL__.replace(/\/$/, "");
    const stored = localStorage.getItem("backend_url");
    if (stored) return stored.replace(/\/$/, "");
    // Default: same host in dev proxy, or localhost
    if (location.hostname === "localhost" || location.hostname === "127.0.0.1") {
      return "http://localhost:8000";
    }
    return prompt("Enter your Railway backend URL:", "https://your-app.up.railway.app") || "";
  }

  let BACKEND = getBackendUrl();
  if (BACKEND) localStorage.setItem("backend_url", BACKEND);

  let selectedNiche = "football";
  let selectedMode = "faceless";
  let selectedFile = null;
  let lastTweet = "";

  const $ = (id) => document.getElementById(id);

  function postTikTokEnabled() {
    const el = $("post-tiktok");
    return el ? el.checked : false;
  }

  // --- UI state ---
  function setProgress(on, pct = 0, label = "Agent working…") {
    const wrap = $("progress-wrap");
    const fill = $("progress-fill");
    wrap.classList.toggle("visible", on);
    fill.style.width = on ? `${Math.min(pct, 100)}%` : "0%";
    $("progress-label").textContent = label;
    $("generate-btn").disabled = on;
    const steps = $("steps");
    if (steps) steps.classList.toggle("visible", on);
  }

  function setActiveStep(step) {
    document.querySelectorAll(".step-pill").forEach((pill) => {
      const s = pill.dataset.step;
      pill.classList.remove("active", "done");
      const order = ["research", "write", "video", "post"];
      const ci = order.indexOf(step);
      const pi = order.indexOf(s);
      if (pi < ci) pill.classList.add("done");
      if (s === step) pill.classList.add("active");
    });
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function showResults(content, rich = false) {
    const el = $("results");
    if (rich) {
      el.innerHTML = content;
      el.classList.add("has-rich");
    } else {
      el.textContent = content;
      el.classList.remove("has-rich");
    }
    el.classList.add("visible");
  }

  // --- Niche / mode ---
  document.querySelectorAll(".btn-niche").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".btn-niche").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      selectedNiche = btn.dataset.niche;
    });
  });

  document.querySelectorAll(".btn-mode").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".btn-mode").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      selectedMode = btn.dataset.mode;
      $("drop-zone").classList.toggle("visible", selectedMode === "upload");
    });
  });

  // --- File drop ---
  const dropZone = $("drop-zone");
  const videoInput = $("video-input");

  dropZone.addEventListener("click", () => videoInput.click());
  const dropLabel = $("drop-zone-label");
  function setDropLabel(name) {
    if (dropLabel) dropLabel.textContent = name || "Tap to upload your video";
  }
  videoInput.addEventListener("change", (e) => {
    if (e.target.files[0]) selectedFile = e.target.files[0];
    setDropLabel(selectedFile?.name || "Video selected");
  });
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files[0]) {
      selectedFile = e.dataTransfer.files[0];
      setDropLabel(selectedFile.name);
    }
  });

  // --- API helpers ---
  async function api(path, options = {}) {
    if (!BACKEND) throw new Error("Backend URL not configured");
    const url = `${BACKEND}${path}`;
    const res = await fetch(url, {
      ...options,
      headers: { Accept: "application/json", ...options.headers },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || data.message || res.statusText);
    return data;
  }

  async function loadStatus() {
    try {
      const data = await api("/status");
      const ytOn = data.youtube?.connected;
      $("yt-dot").className = `dot ${ytOn ? "on" : "off"}`;
      $("connect-yt").textContent = ytOn ? "Connected" : "Connect";
      if ($("disconnect-yt")) $("disconnect-yt").style.display = ytOn ? "inline" : "none";
      const ttOn = data.tiktok?.connected;
      $("tt-dot").className = `dot ${ttOn ? "on" : "off"}`;
      $("tt-status").textContent = ttOn ? "Connected" : "Set token in Railway";
    } catch (e) {
      console.warn("Status:", e.message);
    }
  }

  async function loadHistory() {
    try {
      const data = await api("/history");
      const list = $("history-list");
      const items = data.history || [];
      if (!items.length) {
        list.innerHTML = '<p class="empty-state">No posts yet — generate your first one above</p>';
        return;
      }
      list.innerHTML = items
        .map(
          (h) => `
        <div class="history-item">
          <strong>${h.title || h.niche || "Post"}</strong>
          <span class="meta"> · ${h.niche} · ${h.mode || ""}</span>
          ${h.youtube_url ? `<br><a href="${h.youtube_url}" target="_blank" rel="noopener">${h.youtube_url}</a>` : ""}
          <time>${h.created_at ? new Date(h.created_at).toLocaleString() : ""}</time>
        </div>`
        )
        .join("");
    } catch (e) {
      console.warn("History:", e.message);
    }
  }

  // --- Generate ---
  $("generate-btn").addEventListener("click", async () => {
    const topic = $("topic-input").value.trim() || null;
    setProgress(true, 15, "Researching trends…");
    setActiveStep("research");

    try {
      if (selectedMode === "upload" && selectedFile) {
        setProgress(true, 40, "Uploading your video…");
        setActiveStep("write");
        const form = new FormData();
        form.append("file", selectedFile);
        form.append("niche", selectedNiche);
        if (topic) form.append("topic", topic);
        form.append("post_youtube", "true");
        form.append("post_tiktok", postTikTokEnabled() ? "true" : "false");

        const res = await fetch(`${BACKEND}/upload`, { method: "POST", body: form, signal: AbortSignal.timeout(600000) });
        const json = await res.json();
        if (!res.ok) throw new Error(json.message || json.detail || "Upload failed");
        handleGenerateResult(json);
      } else {
        setProgress(true, 35, "Writing script…");
        setActiveStep("write");
        if (selectedMode === "faceless") {
          setTimeout(() => setActiveStep("video"), 8000);
        }
        const json = await api("/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            niche: selectedNiche,
            mode: selectedMode,
            topic,
            post_youtube: selectedMode === "faceless",
            post_tiktok: postTikTokEnabled(),
          }),
          signal: AbortSignal.timeout(600000),
        });
        handleGenerateResult(json);
      }
    } catch (err) {
      showResults(`Error: ${err.message}`);
    } finally {
      setProgress(false);
      loadHistory();
      loadStatus();
    }
  });

  function handleGenerateResult(json) {
    const d = json.data || json;
    const content = d.content || {};
    setActiveStep("post");

    if (d.status === "error" || json.status === "error") {
      showResults(`Error: ${d.message || json.message || "Unknown error"}`);
      return;
    }

    let html = "";

    if (d.message) {
      html += `<div class="result-block"><span class="result-badge ok">${escapeHtml(d.message)}</span></div>`;
    }

    if (content.title) {
      html += `<div class="result-block"><div class="result-label">Title</div><div class="result-title">${escapeHtml(content.title)}</div></div>`;
    }

    if (content.script) {
      const script = escapeHtml(content.script);
      html += `<div class="result-block"><div class="result-label">Script</div><div class="result-script">${script}</div></div>`;
    }

    const yt = d.youtube || {};
    if (yt.url) {
      html += `<div class="result-block"><div class="result-label">YouTube</div><a class="result-link" href="${escapeHtml(yt.url)}" target="_blank" rel="noopener">${escapeHtml(yt.url)}</a></div>`;
    } else if (yt.status === "skipped") {
      html += `<div class="result-block"><div class="result-label">YouTube</div><span class="result-badge warn">${escapeHtml(yt.message || "Skipped")}</span></div>`;
    }

    if (d.twitter?.tweet) {
      lastTweet = d.twitter.tweet;
      html += `<div class="result-block"><div class="result-label">X / Twitter</div><div class="result-tweet">${escapeHtml(lastTweet)}</div></div>`;
      $("copy-tweet-btn").style.display = "block";
    } else {
      $("copy-tweet-btn").style.display = "none";
    }

    if (!html) {
      showResults(JSON.stringify(d, null, 2));
    } else {
      showResults(html, true);
    }

    setProgress(true, 100, "Done!");
    setTimeout(() => setProgress(false), 800);
  }

  $("copy-tweet-btn").addEventListener("click", async () => {
    if (!lastTweet) return;
    try {
      await navigator.clipboard.writeText(lastTweet);
      $("copy-tweet-btn").textContent = "Copied!";
      setTimeout(() => { $("copy-tweet-btn").textContent = "Copy Tweet"; }, 2000);
    } catch {
      showResults(lastTweet);
    }
  });

  $("connect-yt").addEventListener("click", () => {
    window.open(`${BACKEND}/auth/login`, "_blank");
  });

  $("disconnect-yt")?.addEventListener("click", async () => {
    try {
      await api("/auth/disconnect", { method: "POST" });
      loadStatus();
    } catch (e) {
      showResults(`Disconnect failed: ${e.message}`);
    }
  });

  // Offline banner
  function updateOnline() {
    $("offline-banner").classList.toggle("visible", !navigator.onLine);
  }
  window.addEventListener("online", updateOnline);
  window.addEventListener("offline", updateOnline);
  updateOnline();

  // YouTube connected query param
  if (new URLSearchParams(location.search).get("youtube") === "connected") {
    loadStatus();
  }

  loadStatus();
  loadHistory();
})();
