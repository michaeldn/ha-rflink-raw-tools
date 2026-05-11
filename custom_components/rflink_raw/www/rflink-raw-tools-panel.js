const APP_BUILD_ID = "pre-restart-check-fix-20260510";
class RFLinkRawToolsPanel extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) {
      this._state = {
        tab: "send",
        rawCommand: this._migrateOldSavedCommand(),
        deviceId: localStorage.getItem("rflink_raw_tools.deviceId") || "",
        protocolCommand: localStorage.getItem("rflink_raw_tools.protocolCommand") || "on",
        repeat: Number(localStorage.getItem("rflink_raw_tools.repeat") || "1"),
        delayMs: Number(localStorage.getItem("rflink_raw_tools.delayMs") || "250"),
        busy: false,
        status: null,
        message: "",
        error: ""
      };
      this._render();
      this._loadStatus();
    }
  }

  set narrow(value) {
    this._narrow = value;
  }

  connectedCallback() {
    if (this._hass && !this._rendered) {
      this._render();
      this._loadStatus();
    }
  }

  async _loadStatus() {
    if (!this._hass) return;
    try {
      const status = await this._hass.callWS({ type: "rflink_raw/status" });
      this._state.status = status;
      this._state.error = status.last_error || "";
      this._state.message = status.last_result || "";
      this._update();
    } catch (err) {
      this._state.status = {
        readiness: "status_error",
        readiness_label: "Status unavailable",
        readiness_detail: this._formatError(err),
        rflink_configured: false,
        rflink_connected: false
      };
      this._state.error = this._formatError(err);
      this._update();
    }
  }

  _formatError(err) {
    if (!err) return "Unknown error";
    if (typeof err === "string") return err;
    return err.message || err.error || JSON.stringify(err);
  }

  _normalizeRawCommand(raw) {
    return String(raw || "").trim().replace(/;+$/g, "").toUpperCase();
  }

  _rawCommandKind(raw) {
    const normalized = this._normalizeRawCommand(raw);
    if (normalized === "10;PING" || normalized === "PING") return "ping";
    if (normalized === "10;VERSION" || normalized === "VERSION") return "version";
    return "device";
  }

  _migrateOldSavedCommand() {
    const saved = localStorage.getItem("rflink_raw_tools.rawCommand");
    const kind = this._rawCommandKind(saved);
    if (kind === "ping" || kind === "version") {
      localStorage.removeItem("rflink_raw_tools.rawCommand");
      return "";
    }
    return saved || "";
  }

  _saveInputs() {
    localStorage.setItem("rflink_raw_tools.rawCommand", this._state.rawCommand);
    localStorage.setItem("rflink_raw_tools.deviceId", this._state.deviceId);
    localStorage.setItem("rflink_raw_tools.protocolCommand", this._state.protocolCommand);
    localStorage.setItem("rflink_raw_tools.repeat", String(this._state.repeat));
    localStorage.setItem("rflink_raw_tools.delayMs", String(this._state.delayMs));
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
      this._state.error = this._formatError(err);
      this._update();
    } finally {
      this._state.busy = false;
      this._update();
    }
  }

  async _sendRaw() {
    const raw = String(this._state.rawCommand || "").trim();
    if (!raw) {
      this._state.error = "Paste a learned RFLink device command first. Use Debug for Ping or Version.";
      this._state.message = "";
      this._update();
      return;
    }

    const kind = this._rawCommandKind(raw);
    if (kind === "ping") {
      await this._callService("rflink_raw", "ping_gateway", {}, "RFLink status check complete.");
      return;
    }
    if (kind === "version") {
      await this._callService("rflink_raw", "version_gateway", {}, "RFLink version check complete.");
      return;
    }

    this._saveInputs();
    await this._callService("rflink_raw", "send_raw", {
      raw_command: raw,
      repeat: this._state.repeat,
      delay_ms: this._state.delayMs
    }, "Raw command sent.");
  }

  async _sendProtocol() {
    this._saveInputs();
    await this._callService("rflink_raw", "send_protocol", {
      device_id: this._state.deviceId,
      command: this._state.protocolCommand,
      repeat: this._state.repeat,
      delay_ms: this._state.delayMs
    }, "Protocol command sent.");
  }

  async _setDebug(debugType, enabled) {
    this._state.status = this._state.status || {};
    if (debugType === "rfdebug") this._state.status.rfdebug = Boolean(enabled);
    if (debugType === "qrfdebug") this._state.status.qrfdebug = Boolean(enabled);
    this._state.message = `${debugType.toUpperCase()} ${enabled ? "enabled" : "disabled"}.`;
    this._state.error = "";
    this._update();

    await this._callService("rflink_raw", "set_debug", {
      debug_type: debugType,
      enabled
    }, `${debugType.toUpperCase()} ${enabled ? "enabled" : "disabled"}.`);
  }

  _switchTab(tab) {
    this._state.tab = tab;
    this._update();
  }

  _input(name, value) {
    this._state[name] = value;
    this._saveInputs();
    this._update();
  }

  _render() {
    this._rendered = true;
    this.innerHTML = `
      <style>
        :host {
          display: block;
          min-height: 100vh;
          color: var(--primary-text-color);
          background: var(--primary-background-color);
          font-family: var(--paper-font-body1_-_font-family, Roboto, Arial, sans-serif);
        }
        .wrap {
          max-width: 1180px;
          margin: 0 auto;
          padding: 24px;
        }
        .hero {
          display: grid;
          grid-template-columns: 72px 1fr auto;
          gap: 18px;
          align-items: center;
          margin-bottom: 18px;
        }
        .logo {
          width: 72px;
          height: 72px;
          border-radius: 18px;
          object-fit: cover;
          box-shadow: 0 8px 28px rgba(0,0,0,.25);
        }
        h1 {
          margin: 0;
          font-size: 32px;
          line-height: 1.1;
        }
        .sub {
          color: var(--secondary-text-color);
          margin-top: 6px;
          font-size: 15px;
        }
        .status-pill {
          border-radius: 999px;
          padding: 8px 12px;
          font-size: 13px;
          background: var(--card-background-color);
          border: 1px solid var(--divider-color);
          white-space: nowrap;
        }
        .ok { color: #4caf50; }
        .bad { color: #ff9800; }
        .tabs {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          margin: 14px 0 18px;
        }
        .tab {
          border: 1px solid var(--divider-color);
          border-radius: 999px;
          padding: 10px 14px;
          background: var(--card-background-color);
          color: var(--primary-text-color);
          cursor: pointer;
          font-weight: 600;
        }
        .tab.active {
          background: var(--primary-color);
          color: var(--text-primary-color, #fff);
          border-color: var(--primary-color);
        }
        .grid {
          display: grid;
          grid-template-columns: 1.2fr .8fr;
          gap: 16px;
        }
        .card {
          background: var(--card-background-color);
          border: 1px solid var(--divider-color);
          border-radius: 20px;
          padding: 20px;
          box-shadow: 0 6px 22px rgba(0,0,0,.12);
        }
        .card h2 {
          margin: 0 0 14px;
          font-size: 22px;
        }
        label {
          display: block;
          font-weight: 700;
          margin: 14px 0 7px;
        }
        input, textarea, select {
          width: 100%;
          box-sizing: border-box;
          border: 1px solid var(--divider-color);
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
          border-radius: 12px;
          padding: 12px;
          font-size: 16px;
        }
        textarea {
          min-height: 92px;
          resize: vertical;
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }
        .row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }
        .actions {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          margin-top: 16px;
        }
        button {
          border: 0;
          border-radius: 12px;
          background: var(--primary-color);
          color: var(--text-primary-color, #fff);
          padding: 12px 16px;
          font-weight: 800;
          cursor: pointer;
          font-size: 15px;
        }
        button.secondary {
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
          border: 1px solid var(--divider-color);
        }
        button.warn {
          background: #8a4b00;
          color: white;
        }
        button:disabled {
          opacity: .55;
          cursor: progress;
        }
        .message, .error {
          border-radius: 14px;
          padding: 13px 14px;
          margin-top: 14px;
          font-weight: 600;
        }
        .message {
          background: rgba(76, 175, 80, .14);
          color: #4caf50;
        }
        .error {
          background: rgba(244, 67, 54, .14);
          color: #ff6b6b;
        }
        .help {
          color: var(--secondary-text-color);
          line-height: 1.5;
        }
        .example {
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
          background: var(--secondary-background-color);
          border: 1px solid var(--divider-color);
          border-radius: 12px;
          padding: 10px 12px;
          margin: 8px 0;
          cursor: pointer;
        }
        .checklist {
          display: grid;
          gap: 10px;
        }
        .check {
          display: flex;
          align-items: flex-start;
          gap: 10px;
        }
        .dot {
          width: 10px;
          height: 10px;
          margin-top: 6px;
          border-radius: 999px;
          background: var(--primary-color);
          flex: 0 0 auto;
        }
        
        .toggle-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
          border: 1px solid var(--divider-color);
          background: var(--secondary-background-color);
          border-radius: 14px;
          padding: 14px;
          margin: 10px 0;
        }
        .toggle-text {
          display: grid;
          gap: 3px;
        }
        .toggle-title {
          font-weight: 800;
        }
        .toggle-help {
          color: var(--secondary-text-color);
          font-size: 13px;
        }
        .switch {
          position: relative;
          display: inline-block;
          width: 54px;
          height: 30px;
          flex: 0 0 auto;
        }
        .switch input {
          opacity: 0;
          width: 0;
          height: 0;
        }
        .slider {
          position: absolute;
          cursor: pointer;
          inset: 0;
          background: var(--divider-color);
          transition: .2s;
          border-radius: 999px;
        }
        .slider:before {
          position: absolute;
          content: "";
          height: 22px;
          width: 22px;
          left: 4px;
          bottom: 4px;
          background: white;
          transition: .2s;
          border-radius: 50%;
        }
        .switch input:checked + .slider {
          background: var(--primary-color);
        }
        .switch input:checked + .slider:before {
          transform: translateX(24px);
        }
        @media (max-width: 860px) {
          .wrap { padding: 16px; }
          .hero { grid-template-columns: 56px 1fr; }
          .logo { width: 56px; height: 56px; border-radius: 14px; }
          .status-pill { grid-column: 1 / -1; }
          .grid { grid-template-columns: 1fr; }
          .row { grid-template-columns: 1fr; }
        }
      </style>
      <div class="wrap">
        <div class="hero">
          <img class="logo" src="/api/rflink_raw/static/logo.png" alt="RFLink Raw Tools" data-logo-fallback="brand">
          <div>
            <h1>RFLink Raw Tools</h1>
            <div class="sub">Simple RFLink command sender for Home Assistant. Start with Ping, then send raw commands.</div>
          </div>
          <div id="connection" class="status-pill">Checking RFLink…</div>
        </div>

        <div class="tabs">
          <button class="tab" data-tab="send">Send</button>
          <button class="tab" data-tab="learn">Learn</button>
          <button class="tab" data-tab="debug">Debug</button>
          <button class="tab" data-tab="setup">Setup</button>
        </div>

        <div id="body"></div>
      </div>
    `;
    this.querySelectorAll(".tab").forEach(btn => {
      btn.addEventListener("click", () => this._switchTab(btn.dataset.tab));
    });
    this._wireLogoFallback();
    this._update();
  }

  _wireLogoFallback() {
    const logo = this.querySelector('.logo');
    if (!logo) return;
    logo.addEventListener('error', () => {
      if (logo.dataset.logoFallback === 'brand') {
        logo.dataset.logoFallback = 'none';
        logo.src = '/api/brands/integration/rflink_raw/logo.png';
      } else {
        logo.style.display = 'none';
      }
    });
  }

  _update() {
    if (!this._rendered) return;

    this.querySelectorAll(".tab").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.tab === this._state.tab);
    });

    const status = this._state.status;
    const connection = this.querySelector("#connection");
    if (connection) {
      const readiness = status && status.readiness ? status.readiness : "checking";
      if (readiness === "ready") {
        connection.innerHTML = `<span class="ok">● RFLink ready</span>`;
      } else if (readiness === "configured_unconfirmed") {
        connection.innerHTML = `<span class="warn">● RFLink configured — test with Ping</span>`;
      } else if (readiness === "not_configured") {
        connection.innerHTML = `<span class="bad">● RFLink config not found</span>`;
      } else if (readiness === "status_error") {
        connection.innerHTML = `<span class="bad">● Status unavailable</span>`;
      } else {
        connection.innerHTML = `<span class="warn">● Checking RFLink…</span>`;
      }
    }

    const body = this.querySelector("#body");
    if (!body) return;

    const tab = this._state.tab;
    body.innerHTML = this[`_${tab}View`]();

    body.querySelectorAll("[data-action]").forEach(el => {
      el.addEventListener("click", () => {
        const action = el.dataset.action;
        if (this[action]) this[action]();
      });
    });

    body.querySelectorAll("[data-tablink]").forEach(el => {
      el.addEventListener("click", () => this._switchTab(el.dataset.tablink));
    });

    body.querySelectorAll("[data-example]").forEach(el => {
      el.addEventListener("click", () => this._input("rawCommand", el.dataset.example));
    });

    body.querySelectorAll("[data-field]").forEach(el => {
      el.addEventListener("input", event => {
        const field = el.dataset.field;
        const rawValue = event.target.value;
        const value = el.type === "number" ? Number(rawValue) : rawValue;
        this._input(field, value);
      });
    });

    body.querySelectorAll("[data-toggle-debug]").forEach(el => {
      el.addEventListener("change", event => {
        this._setDebug(el.dataset.toggleDebug, Boolean(event.target.checked));
      });
    });
  }

  _sendWarning() {
    const kind = this._rawCommandKind(this._state.rawCommand);
    if (kind === "ping" || kind === "version") {
      return `<div class="message">This is a status check. The app will run it through the Debug action instead of sending it as a device command.</div>`;
    }
    return "";
  }

  _feedback() {
    return `
      ${this._state.message ? `<div class="message">${this._state.message}</div>` : ""}
      ${this._state.error ? `<div class="error">${this._state.error}</div>` : ""}
    `;
  }

  _sendView() {
    return `
      <div class="grid">
        <div class="card">
          <h2>Send raw RFLink command</h2>
          <p class="help">Paste a learned RFLink device command. Ping and Version are status checks on the Debug tab, not device commands.</p>

          <label>Raw command</label>
          <textarea data-field="rawCommand" placeholder="Paste learned command, for example: 10;NewKaku;01a2b3;1;ON;">${this._state.rawCommand}</textarea>

          <div class="row">
            <div>
              <label>Repeat</label>
              <input data-field="repeat" type="number" min="1" max="20" value="${this._state.repeat}">
            </div>
            <div>
              <label>Delay between repeats (ms)</label>
              <input data-field="delayMs" type="number" min="0" max="5000" value="${this._state.delayMs}">
            </div>
          </div>

          <div class="actions">
            <button data-action="_sendRaw" ${this._state.busy ? "disabled" : ""}>Send raw command</button>
            <button class="secondary" data-action="_clearRawCommand">Clear command</button>\n            <button class="secondary" data-tablink="debug">Open debug tools</button>
          </div>

          ${this._sendWarning()}\n          ${this._feedback()}
        </div>

        <div class="card">
          <h2>Examples</h2>
          <p class="help">Click an example to copy it into the raw command box.</p>
          <div class="example" data-example="10;NewKaku;01a2b3;1;ON;">Example format: 10;NewKaku;01a2b3;1;ON;</div>
          <div class="example" data-example="10;NewKaku;01a2b3;1;OFF;">Example format: 10;NewKaku;01a2b3;1;OFF;</div>
          <p class="help"><b>These examples are format examples only.</b> They will not control your outlets until you replace the device id with one learned from your RFLink logs. Do not use 10;PING; here; use Debug → Ping gateway.</p>
        </div>
      </div>
    `;
  }

  _learnView() {
    return `
      <div class="grid">
        <div class="card">
          <h2>Learn an RF command</h2>
          <div class="checklist">
            <div class="check"><span class="dot"></span><div>Open <b>Debug</b> and turn on RFDEBUG or QRFDEBUG.</div></div>
            <div class="check"><span class="dot"></span><div>Press the physical remote button you want to learn.</div></div>
            <div class="check"><span class="dot"></span><div>Open Home Assistant logs and look for the RFLink line/device id.</div></div>
            <div class="check"><span class="dot"></span><div>Paste the learned command into <b>Send</b> and test it.</div></div>
            <div class="check"><span class="dot"></span><div>Save working ON/OFF commands in a Home Assistant script or automation.</div></div>
          </div>
        </div>
        <div class="card">
          <h2>What to capture</h2>
          <p class="help">For each device, capture:</p>
          <div class="example">Device name / room</div>
          <div class="example">ON command</div>
          <div class="example">OFF command</div>
          <div class="example">How long to run it, for example 3 seconds</div>
          <p class="help">The next version can add a saved-device library after sending is stable.</p>
        </div>
      </div>
    `;
  }

  _debugView() {
    return `
      <div class="grid">
        <div class="card">
          <h2>Gateway checks</h2>
          <p class="help">Use these first to confirm Home Assistant has loaded RFLink. Hardware command testing still needs a real learned RFLink device command.</p>
          <div class="actions">
            <button data-action="_ping" ${this._state.busy ? "disabled" : ""}>Ping gateway</button>
            <button data-action="_version" ${this._state.busy ? "disabled" : ""}>Ask version</button>
            <button class="secondary" data-action="_loadStatus">Refresh status</button>
          </div>
          ${this._feedback()}
        </div>

        <div class="card">
          <h2>Debug capture</h2>
          <p class="help">Turn on one debug mode, press a remote button, then check Home Assistant logs.</p>

          <div class="toggle-row">
            <div class="toggle-text">
              <div class="toggle-title">RFDEBUG</div>
              <div class="toggle-help">${this._state.status && this._state.status.rfdebug ? "Enabled" : "Disabled"} — detailed RFLink debug output.</div>
            </div>
            <label class="switch">
              <input type="checkbox" data-toggle-debug="rfdebug" ${this._state.status && this._state.status.rfdebug ? "checked" : ""}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="toggle-row">
            <div class="toggle-text">
              <div class="toggle-title">QRFDEBUG</div>
              <div class="toggle-help">${this._state.status && this._state.status.qrfdebug ? "Enabled" : "Disabled"} — raw RF capture/debug output.</div>
            </div>
            <label class="switch">
              <input type="checkbox" data-toggle-debug="qrfdebug" ${this._state.status && this._state.status.qrfdebug ? "checked" : ""}>
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
          <h2>Status</h2>
          <p><b>Integration version:</b> ${status.version || "0.0.1"}</p>
          <p><b>App build:</b> ${typeof APP_BUILD_ID !== "undefined" ? APP_BUILD_ID : "unknown"}</p>
          <p><b>RFLink configuration scan:</b> ${status.rflink_configured ? "Found" : "Not found"} ${status.rflink_config_source ? `(${status.rflink_config_source})` : ""}</p>
          <p><b>RFLink live bridge:</b> ${status.rflink_connected ? "Connected" : "Not confirmed yet"}</p>
          <p class="help">${status.readiness_detail || "Use Ping on the Debug page to test the gateway."}</p>\n          <p class="help">If your RFLink block exists but this says Not found, use Debug → Ping gateway. The app can still work if Home Assistant has loaded RFLink.</p>
          <p><b>Last command:</b> ${status.last_command || "None yet"}</p>
          <p><b>Last result:</b> ${status.last_result || "None yet"}</p>
          <p><b>Last error:</b> ${status.last_error || "None"}</p>
          <p><b>Last updated:</b> ${status.last_updated || "Never"}</p>
          <div class="actions">
            <button data-action="_loadStatus">Refresh status</button>
          </div>
        </div>
        <div class="card">
          <h2>Install/update policy</h2>
          <p class="help">This app baseline does not self-update and does not edit configuration.yaml. Install/update through HACS or the terminal installer.</p>
          <p class="help">This avoids the registry and dashboard whack-a-mole from the earlier builds.</p>
          <div class="actions">
            <button class="secondary" data-tablink="send">Back to Send</button>
          </div>
        </div>
      </div>
    `;
  }

  _ping() { return this._callService("rflink_raw", "ping_gateway", {}, "RFLink status check complete."); }
  _version() { return this._callService("rflink_raw", "version_gateway", {}, "RFLink version check complete."); }
  _clearRawCommand() {
    this._state.rawCommand = "";
    localStorage.removeItem("rflink_raw_tools.rawCommand");
    this._state.message = "Raw command cleared.";
    this._state.error = "";
    this._update();
  }
  _rfdebugOn() { return this._setDebug("rfdebug", true); }
  _rfdebugOff() { return this._setDebug("rfdebug", false); }
  _qrfdebugOn() { return this._setDebug("qrfdebug", true); }
  _qrfdebugOff() { return this._setDebug("qrfdebug", false); }
}

customElements.define("rflink-raw-tools-panel", RFLinkRawToolsPanel);
