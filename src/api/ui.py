from fastapi.responses import HTMLResponse

_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>rAIdio</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      font-family: system-ui, -apple-system, sans-serif;
      background: #0f1117;
      color: #e8eaed;
    }
    main {
      width: min(100%, 22rem);
      padding: 2rem;
    }
    h1 {
      margin: 0 0 0.25rem;
      font-size: 1.5rem;
      font-weight: 600;
    }
    p {
      margin: 0 0 1.5rem;
      color: #9aa0a6;
      font-size: 0.9rem;
      line-height: 1.4;
    }
    label {
      display: block;
      margin-bottom: 1rem;
      font-size: 0.85rem;
      color: #bdc1c6;
    }
    input {
      width: 100%;
      margin-top: 0.35rem;
      padding: 0.65rem 0.75rem;
      border: 1px solid #3c4043;
      border-radius: 8px;
      background: #1a1d24;
      color: #e8eaed;
      font-size: 1rem;
    }
    input:focus {
      outline: 2px solid #8ab4f8;
      border-color: transparent;
    }
    button {
      width: 100%;
      margin-top: 0.5rem;
      padding: 0.85rem;
      border: none;
      border-radius: 8px;
      background: #8ab4f8;
      color: #0f1117;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
    }
    button:hover:not(:disabled) { background: #aecbfa; }
    button:disabled {
      opacity: 0.6;
      cursor: wait;
    }
    #status {
      margin-top: 1.25rem;
      padding: 0.75rem;
      border-radius: 8px;
      font-size: 0.9rem;
      line-height: 1.4;
      display: none;
    }
    #status.ok {
      display: block;
      background: #1e3a2f;
      color: #81c995;
    }
    #status.err {
      display: block;
      background: #3c1f1f;
      color: #f28b82;
    }
    #status.busy {
      display: block;
      background: #2a2d35;
      color: #9aa0a6;
    }
  </style>
</head>
<body>
  <main>
    <h1>rAIdio</h1>
    <p>Generate a radio script from newsletters and send it via Telegram.</p>
    <form id="form">
      <label>
        API key
        <input type="password" id="apiKey" autocomplete="current-password" required>
      </label>
      <label>
        Date (optional)
        <input type="date" id="targetDate">
      </label>
      <button type="submit" id="submitBtn">Run process</button>
    </form>
    <div id="status" role="status"></div>
  </main>
  <script>
    const form = document.getElementById("form");
    const apiKeyInput = document.getElementById("apiKey");
    const dateInput = document.getElementById("targetDate");
    const statusEl = document.getElementById("status");
    const submitBtn = document.getElementById("submitBtn");

    const savedKey = sessionStorage.getItem("raidio_api_key");
    if (savedKey) apiKeyInput.value = savedKey;

    dateInput.valueAsDate = new Date();

    function setStatus(kind, message) {
      statusEl.className = kind;
      statusEl.textContent = message;
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const apiKey = apiKeyInput.value.trim();
      if (!apiKey) return;

      sessionStorage.setItem("raidio_api_key", apiKey);
      submitBtn.disabled = true;
      setStatus("busy", "Process running… This may take several minutes.");

      const params = new URLSearchParams();
      if (dateInput.value) params.set("target_date", dateInput.value);

      try {
        const response = await fetch("/run-process?" + params.toString(), {
          method: "POST",
          headers: { "X-API-Key": apiKey },
        });
        const body = await response.json().catch(() => ({}));

        if (!response.ok) {
          setStatus("err", body.detail || "Error " + response.status);
          return;
        }

        const labels = {
          completed: "Done — the result was sent to Telegram.",
          no_newsletters: "No newsletters found for this date.",
          mailbox_fetch_failed: "Failed to fetch newsletters from the mailbox.",
          script_generation_failed: "Failed to generate the radio script.",
          audio_delivery_failed: "Failed to send the audio message.",
        };
        const message = labels[body.status] || ("Status: " + body.status);
        const detail = body.detail ? " " + body.detail : "";
        setStatus(body.status === "completed" ? "ok" : "err", message + detail);
      } catch {
        setStatus("err", "Could not reach the API.");
      } finally {
        submitBtn.disabled = false;
      }
    });
  </script>
</body>
</html>"""


def home_page() -> HTMLResponse:
    return HTMLResponse(content=_UI_HTML)
