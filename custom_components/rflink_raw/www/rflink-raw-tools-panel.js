const APP_BUILD_ID = "software-cleanup-final-20260511";

class RFLinkRawToolsPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._timer = null;
    this._autoClearedUnknown = false;
    this._state = {
      tab: localStorage.getItem("rflink_raw_tools.tab") || "send",
      busy: false,
      message: "",
      error: "",
      rawCommand: this._migrateOldSavedCommand(),
      repeat: Number(localStorage.getItem("rflink_raw_tools.repeat") || 1),
      delayMs: Number(localStorage.getItem("rflink_raw_tools.delayMs") || 250),
      status: {
        readiness: "checking",
        readiness_label: "Checking status",
        readiness_detail: "Loading RFLink Raw Tools status…",
        rflink_configured: false,
        rflink_loaded: false,
        rflink_connected: false,
        last_result: "",
        last_error: "",
        last_command: "",
        last_updated: "",
        rfdebug: false,
        qrfdebug: false,
      },
    };
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) {
      this._render();
      this._rendered = true;
    }
    this._loadStatus();
  }

  connectedCallback() {
    if (this._timer) return;
    this._timer = window.setInterval(() => this._loadStatus(), 10000);
  }

  disconnectedCallback() {
    if (this._timer) window.clearInterval(this._timer);
    this._timer = null;
  }

  _formatError(err) {
    if (!err) return "Unknown error";
    if (typeof err === "string") return err;
    return err.message || err.error || JSON.stringify(err);
  }

  _isUnknownCommandText(value) {
    const text = String(value || "").trim();
    return text === "Unknown command." || text === "Unknown command";
  }

  _sanitizeStatus(status) {
    const clean = { ...(status || {}) };
    if (this._isUnknownCommandText(clean.last_error)) clean.last_error = "";
    if (this._isUnknownCommandText(clean.last_result)) clean.last_result = "";
    return clean;
  }

  async _autoClearStaleUnknown(status) {
    if (!status || this._autoClearedUnknown) return;
    if (this._isUnknownCommandText(status.last_error) || this._isUnknownCommandText(status.last_result)) {
      this._autoClearedUnknown = true;
      try {
        await this._hass.callService("rflink_raw", "clear_status", {});
      } catch (err) {
        // Do not show cleanup failures.
      }
    }
  }

  _normalizeRawCommand(raw) {
    return String(raw || "").trim().replace(/;+$/g, "").toUpperCase();
  }

  _rawCommandKind(raw) {
    const normalized = this._normalizeRawCommand(raw);
    if (normalized === "10;PING" || normalized === "PING") return "status";
    if (normalized === "10;VERSION" || normalized === "VERSION") return "version";
    return "device";
  }

  _migrateOldSavedCommand() {
    const saved = localStorage.getItem("rflink_raw_tools.rawCommand");
    const kind = this._rawCommandKind(saved);
    if (kind === "status" || kind === "version") {
      localStorage.removeItem("rflink_raw_tools.rawCommand");
      return "";
    }
    return saved || "";
  }

  _debugLocalKey(debugType) {
    return `rflink_raw_tools.${debugType}`;
  }

  _debugEnabled(debugType) {
    const local = localStorage.getItem(this._debugLocalKey(debugType));
    if (local === "true") return true;
    if (local === "false") return false;
    return Boolean(this._state.status && this._state.status[debugType]);
  }

  async _loadStatus() {
    if (!this._hass) return;
    try {
      const rawStatus = await this._hass.callApi("GET", "rflink_raw/status");
      await this._autoClearStaleUnknown(rawStatus);
      const status = this._sanitizeStatus(rawStatus);
      this._state.status = status;
      if (!this._state.busy) this._state.error = "";
      this._update();
    } catch (err) {
      const message = this._formatError(err);
      this._state.status = {
        readiness: "status_api_unavailable",
        readiness_label: "Status API unavailable",
        readiness_detail: this._isUnknownCommandText(message)
          ? "The status API was not available. Restart Home Assistant Core and hard refresh."
          : `The status API was not available: ${message}`,
        rflink_configured: false,
        rflink_loaded: false,
        rflink_connected: false,
        last_error: "",
        last_result: "",
        last_command: "",
        last_updated: "",
        rfdebug: this._debugEnabled("rfdebug"),
        qrfdebug: this._debugEnabled("qrfdebug"),
      };
      this._state.error = "";
      this._update();
    }
  }

  async _callService(domain, service, data = {}, success = "Done.") {
    this._state.busy = true;
    this._state.error = "";
    this._state.message = "";
    this._update();

    try {
      await this._hass.callService(domain, service, data);
      this._state.message = success;
      await this._loadStatus();
    } catch (err) {
      this._state.message = "";
      this._state.error = this._formatError(err);
      if (this._isUnknownCommandText(this._state.error)) {
        this._state.error = "RFLink rejected that command. Use a real learned command, not an example.";
      }
      this._update();
    } finally {
      this._state.busy = false;
      this._update();
    }
  }

  _saveInputs() {
    localStorage.setItem("rflink_raw_tools.rawCommand", this._state.rawCommand || "");
    localStorage.setItem("rflink_raw_tools.repeat", String(this._state.repeat || 1));
    localStorage.setItem("rflink_raw_tools.delayMs", String(this._state.delayMs || 250));
  }

  async _sendRaw() {
    const raw = String(this._state.rawCommand || "").trim();
    if (!raw) {
      this._state.error = "Paste a learned RFLink device command first. Use Debug for status/version checks.";
      this._state.message = "";
      this._update();
      return;
    }

    const kind = this._rawCommandKind(raw);
    if (kind === "status") return this._statusCheck();
    if (kind === "version") return this._versionCheck();

    this._saveInputs();
    await this._callService("rflink_raw", "send_raw", {
      raw_command: raw,
      repeat: Number(this._state.repeat || 1),
      delay_ms: Number(this._state.delayMs || 250),
    }, "Raw command sent.");
  }

  _statusCheck() {
    return this._callService("rflink_raw", "ping_gateway", {}, "RFLink status check complete.");
  }

  _versionCheck() {
    return this._callService("rflink_raw", "version_gateway", {}, "RFLink version check complete.");
  }

  async _setDebug(debugType, enabled) {
    this._state.status = this._state.status || {};
    this._state.status[debugType] = Boolean(enabled);
    localStorage.setItem(this._debugLocalKey(debugType), String(Boolean(enabled)));

    const label = debugType === "rfdebug" ? "Decoded RFLink logging" : "Raw RF capture logging";
    this._state.message = `${label} ${enabled ? "enabled" : "disabled"}.`;
    this._state.error = "";
    this._update();

    await this._callService("rflink_raw", "set_debug", {
      debug_type: debugType,
      enabled: Boolean(enabled),
    }, `${label} ${enabled ? "enabled" : "disabled"}.`);
  }

  _clearRawCommand() {
    this._state.rawCommand = "";
    localStorage.removeItem("rflink_raw_tools.rawCommand");
    this._state.message = "Raw command cleared.";
    this._state.error = "";
    this._update();
  }

  async _clearStatus() {
    this._state.message = "";
    this._state.error = "";
    await this._callService("rflink_raw", "clear_status", {}, "Status cleared.");
  }

  _input(field, value) {
    this._state[field] = value;
    this._update();
  }

  _setTab(tab) {
    this._state.tab = tab;
    localStorage.setItem("rflink_raw_tools.tab", tab);
    this._state.error = "";
    this._state.message = "";
    this._update();
  }

  _copyExample(command) {
    this._state.rawCommand = command;
    this._state.message = "Example copied. Replace the device id with a real learned RFLink command.";
    this._state.error = "";
    this._update();
  }

  _feedback() {
    return `
      ${this._state.message ? `<div class="message">${this._state.message}</div>` : ""}
      ${this._state.error ? `<div class="error">${this._state.error}</div>` : ""}
    `;
  }

  _statusBadge() {
    const status = this._state.status || {};
    const readiness = status.readiness || "checking";
    if (readiness === "ready") return `<span class="badge ok">● RFLink ready</span>`;
    if (readiness === "configured_unconfirmed") return `<span class="badge warn">● RFLink configured</span>`;
    if (readiness === "not_configured") return `<span class="badge bad">● RFLink config not found</span>`;
    if (readiness === "status_api_unavailable") return `<span class="badge warn">● Status check unavailable</span>`;
    return `<span class="badge warn">● Checking RFLink…</span>`;
  }

  _sendView() {
    return `
      <div class="grid">
        <div class="card">
          <h2>Send learned RFLink command</h2>
          <p class="help">Paste a real command learned from your RFLink/Home Assistant logs. Do not use Ping or Version here; those live on Debug.</p>
          <label>Raw command</label>
          <textarea data-field="rawCommand" placeholder="Example format: 10;NewKaku;01a2b3;1;ON;">${this._state.rawCommand || ""}</textarea>

          <div class="row">
            <div>
              <label>Repeat</label>
              <input data-field="repeat" type="number" min="1" value="${this._state.repeat || 1}">
            </div>
            <div>
              <label>Delay between repeats (ms)</label>
              <input data-field="delayMs" type="number" min="0" value="${this._state.delayMs || 250}">
            </div>
          </div>

          <div class="actions">
            <button data-action="_sendRaw" ${this._state.busy ? "disabled" : ""}>Send raw command</button>
            <button class="secondary" data-action="_clearRawCommand">Clear command</button>
            <button class="secondary" data-tablink="debug">Open debug</button>
          </div>
          ${this._feedback()}
        </div>

        <div class="card">
          <h2>Examples</h2>
          <p class="help">Format examples only. These will not control your outlets until the device id matches your RFLink logs.</p>
          <div class="example" data-example="10;NewKaku;01a2b3;1;ON;">10;NewKaku;01a2b3;1;ON;</div>
          <div class="example" data-example="10;NewKaku;01a2b3;1;OFF;">10;NewKaku;01a2b3;1;OFF;</div>
        </div>
      </div>
    `;
  }

  _captureView() {
    return `
      <div class="grid">
        <div class="card">
          <h2>Capture a remote command</h2>
          <p class="help">Purpose: use this page to discover the real RFLink command from a physical 433 MHz remote. This page does not send commands.</p>
          <div class="checklist">
            <div class="check"><span class="dot"></span><div>Go to <b>Debug</b> and turn on <b>Raw RF capture logging</b>.</div></div>
            <div class="check"><span class="dot"></span><div>Press one physical remote button once, for example outlet ON.</div></div>
            <div class="check"><span class="dot"></span><div>Open Home Assistant logs and copy the RFLink command/device line.</div></div>
            <div class="check"><span class="dot"></span><div>Paste it into <b>Send</b> and test.</div></div>
            <div class="check"><span class="dot"></span><div>Repeat for OFF. Your AC/heater flow needs separate ON and OFF commands.</div></div>
          </div>
        </div>
        <div class="card">
          <h2>Capture sheet</h2>
          <p class="help">Write these down for each outlet:</p>
          <div class="example">Room/device name</div>
          <div class="example">Learned ON command</div>
          <div class="example">Learned OFF command</div>
          <div class="example">Run duration, for example 3 seconds</div>
        </div>
      </div>
    `;
  }

  _debugView() {
    return `
      <div class="grid">
        <div class="card">
          <h2>Status checks</h2>
          <p class="help">These are app diagnostics. They should not be used as device commands.</p>
          <div class="actions">
            <button data-action="_statusCheck">Check HA RFLink status</button>
            <button class="secondary" data-action="_versionCheck">Check version support</button>
          </div>
          ${this._feedback()}
        </div>

        <div class="card">
          <h2>Logging switches</h2>
          <p class="help">Use one at a time while capturing a remote. Switches update immediately and keep their visual state while you move between tabs.</p>

          <div class="toggle-row">
            <div class="toggle-text">
              <div class="toggle-title">Decoded RFLink logging</div>
              <div class="toggle-help">${this._debugEnabled("rfdebug") ? "Enabled" : "Disabled"} — decoded protocol messages in Home Assistant logs.</div>
            </div>
            <label class="switch">
              <input type="checkbox" data-toggle-debug="rfdebug" ${this._debugEnabled("rfdebug") ? "checked" : ""}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="toggle-row">
            <div class="toggle-text">
              <div class="toggle-title">Raw RF capture logging</div>
              <div class="toggle-help">${this._debugEnabled("qrfdebug") ? "Enabled" : "Disabled"} — raw 433 MHz capture output used to learn remotes.</div>
            </div>
            <label class="switch">
              <input type="checkbox" data-toggle-debug="qrfdebug" ${this._debugEnabled("qrfdebug") ? "checked" : ""}>
              <span class="slider"></span>
            </label>
          </div>
        </div>
      </div>
    `;
  }

  _setupView() {
    const status = this._state.status || {};
    return `
      <div class="grid">
        <div class="card">
          <h2>Setup status</h2>
          <p><b>Integration version:</b> ${status.version || "0.0.1"}</p>
          <p><b>App build:</b> ${APP_BUILD_ID}</p>
          <p><b>RFLink configuration scan:</b> ${status.rflink_configured ? "Found" : "Not found"} ${status.rflink_config_source ? `(${status.rflink_config_source})` : ""}</p>
          <p><b>Home Assistant RFLink loaded:</b> ${status.rflink_loaded ? "Yes" : "No / not confirmed"}</p>
          <p><b>RFLink live bridge:</b> ${status.rflink_connected ? "Connected" : "Not confirmed yet"}</p>
          <p class="help">${status.readiness_detail || "Use Debug → Check HA RFLink status."}</p>
          <p><b>Last command:</b> ${status.last_command || "None yet"}</p>
          <p><b>Last result:</b> ${status.last_result || "None yet"}</p>
          <p><b>Last backend error:</b> ${status.last_error || "None"}</p>
          <p><b>Last updated:</b> ${status.last_updated || "Never"}</p>
          <div class="actions">
            <button data-action="_loadStatus">Refresh status</button>
            <button class="secondary" data-action="_clearStatus">Clear status</button>
          </div>
          ${this._feedback()}
        </div>
      </div>
    `;
  }

  _body() {
    if (this._state.tab === "capture") return this._captureView();
    if (this._state.tab === "debug") return this._debugView();
    if (this._state.tab === "setup") return this._setupView();
    return this._sendView();
  }

  _render() {
    this.innerHTML = `
      <style>
        :host {
          display: block;
          padding: 24px;
          color: var(--primary-text-color);
          background: var(--primary-background-color);
          min-height: 100vh;
          box-sizing: border-box;
          font-family: var(--primary-font-family, sans-serif);
        }
        .header { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-bottom: 18px; }
        .brand { display: flex; align-items: center; gap: 16px; }
        .logo { width: 74px; height: 74px; border-radius: 14px; object-fit: contain; }
        h1 { margin: 0; font-size: 34px; line-height: 1.1; }
        h2 { margin: 0 0 14px; font-size: 24px; }
        p { color: var(--secondary-text-color); line-height: 1.45; }
        .badge { border: 1px solid var(--divider-color); border-radius: 999px; padding: 8px 12px; font-weight: 800; white-space: nowrap; }
        .ok { color: #4caf50; }
        .warn { color: #ff9800; }
        .bad { color: #ff6b6b; }
        .tabs { display: flex; gap: 10px; margin: 14px 0 22px; flex-wrap: wrap; }
        .tab, button {
          border: 0;
          border-radius: 999px;
          padding: 12px 18px;
          font-weight: 800;
          cursor: pointer;
          background: var(--primary-color);
          color: var(--text-primary-color, #fff);
        }
        .tab:not(.active), .secondary {
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
          border: 1px solid var(--divider-color);
        }
        button:disabled { opacity: .6; cursor: not-allowed; }
        .grid { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(280px, .8fr); gap: 18px; align-items: start; }
        .card {
          border: 1px solid var(--divider-color);
          background: var(--card-background-color);
          border-radius: 18px;
          padding: 22px;
          box-sizing: border-box;
        }
        label { display: block; font-weight: 800; margin: 14px 0 8px; }
        textarea, input {
          width: 100%;
          box-sizing: border-box;
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
          border: 1px solid var(--divider-color);
          border-radius: 12px;
          padding: 14px;
          font: inherit;
        }
        textarea { min-height: 108px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
        .row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
        .actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; align-items: center; }
        .message, .error {
          border-radius: 14px;
          padding: 14px 16px;
          margin-top: 16px;
          font-weight: 800;
        }
        .message { background: rgba(76, 175, 80, .16); color: #81c784; }
        .error { background: rgba(244, 67, 54, .18); color: #ff8a80; }
        .example {
          border: 1px solid var(--divider-color);
          border-radius: 12px;
          padding: 12px;
          margin: 10px 0;
          background: var(--secondary-background-color);
          font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
          cursor: pointer;
        }
        .help { color: var(--secondary-text-color); }
        .check { display: grid; grid-template-columns: 18px 1fr; gap: 10px; margin: 13px 0; align-items: start; }
        .dot { width: 10px; height: 10px; border-radius: 50%; background: var(--primary-color); margin-top: 6px; }
        .toggle-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; border: 1px solid var(--divider-color); background: var(--secondary-background-color); border-radius: 16px; padding: 16px; margin: 12px 0; }
        .toggle-title { font-weight: 900; }
        .toggle-help { color: var(--secondary-text-color); font-size: 13px; margin-top: 4px; }
        .switch { position: relative; display: inline-block; width: 54px; height: 30px; margin: 0; flex: 0 0 auto; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; inset: 0; background: var(--divider-color); transition: .2s; border-radius: 999px; }
        .slider:before { position: absolute; content: ""; height: 22px; width: 22px; left: 4px; bottom: 4px; background: white; transition: .2s; border-radius: 50%; }
        .switch input:checked + .slider { background: var(--primary-color); }
        .switch input:checked + .slider:before { transform: translateX(24px); }
        @media (max-width: 900px) {
          :host { padding: 16px; }
          .grid, .row { grid-template-columns: 1fr; }
          .header { align-items: flex-start; flex-direction: column; }
          h1 { font-size: 28px; }
        }
      </style>

      <div class="header">
        <div class="brand">
          <img class="logo" src="/api/rflink_raw/static/logo.png" alt="RFLink Raw Tools">
          <div>
            <h1>RFLink Raw Tools</h1>
            <p class="help">Send learned RFLink commands and capture remote codes cleanly.</p>
          </div>
        </div>
        <div id="status-badge">${this._statusBadge()}</div>
      </div>

      <div class="tabs">
        <button class="tab ${this._state.tab === "send" ? "active" : ""}" data-tab="send">Send</button>
        <button class="tab ${this._state.tab === "capture" ? "active" : ""}" data-tab="capture">Capture</button>
        <button class="tab ${this._state.tab === "debug" ? "active" : ""}" data-tab="debug">Debug</button>
        <button class="tab ${this._state.tab === "setup" ? "active" : ""}" data-tab="setup">Setup</button>
      </div>

      <main id="body"></main>
    `;
    this._bindShell();
    this._update();
  }

  _bindShell() {
    this.querySelectorAll("[data-tab]").forEach(btn => {
      btn.addEventListener("click", () => this._setTab(btn.dataset.tab));
    });
  }

  _update() {
    if (!this._rendered) return;
    const badge = this.querySelector("#status-badge");
    if (badge) badge.innerHTML = this._statusBadge();

    const body = this.querySelector("#body");
    if (!body) return;
    body.innerHTML = this._body();

    body.querySelectorAll("[data-action]").forEach(el => {
      el.addEventListener("click", () => this[el.dataset.action] && this[el.dataset.action]());
    });

    body.querySelectorAll("[data-tablink]").forEach(el => {
      el.addEventListener("click", () => this._setTab(el.dataset.tablink));
    });

    body.querySelectorAll("[data-example]").forEach(el => {
      el.addEventListener("click", () => this._copyExample(el.dataset.example));
    });

    body.querySelectorAll("[data-field]").forEach(el => {
      el.addEventListener("input", event => {
        const field = el.dataset.field;
        const value = el.type === "number" ? Number(event.target.value) : event.target.value;
        this._input(field, value);
      });
    });

    body.querySelectorAll("[data-toggle-debug]").forEach(el => {
      el.addEventListener("change", event => {
        this._setDebug(el.dataset.toggleDebug, Boolean(event.target.checked));
      });
    });
  }
}

customElements.define("rflink-raw-tools-panel", RFLinkRawToolsPanel);
