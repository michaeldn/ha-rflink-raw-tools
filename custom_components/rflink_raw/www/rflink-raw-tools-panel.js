class RFLinkRawToolsPanel extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) {
      this._state = {
        tab: "send",
        rawCommand: localStorage.getItem("rflink_raw_tools.rawCommand") || "10;PING;",
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
      this._state.error = this._formatError(err);
      this._update();
    }
  }

  _formatError(err) {
    if (!err) return "Unknown error";
    if (typeof err === "string") return err;
    return err.message || err.error || JSON.stringify(err);
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
    this._saveInputs();
    await this._callService("rflink_raw", "send_raw", {
      raw_command: this._state.rawCommand,
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
          <p class="help">Paste a full RFLink command. This app converts it for Home Assistant's RFLink command bridge. If the header says “configured — test with Ping,” go to Debug and click Ping first.</p>

          <label>Raw command</label>
          <textarea data-field="rawCommand">${this._state.rawCommand}</textarea>

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
            <button class="secondary" data-tablink="debug">Open debug tools</button>
          </div>

          ${this._feedback()}
        </div>

        <div class="card">
          <h2>Examples</h2>
          <p class="help">Click an example to copy it into the raw command box.</p>
          <div class="example" data-example="10;PING;">10;PING;</div>
          <div class="example" data-example="10;VERSION;">10;VERSION;</div>
          <div class="example" data-example="10;rfdebug;on;">10;rfdebug;on;</div>
          <div class="example" data-example="10;qrfdebug;on;">10;qrfdebug;on;</div>
          <p class="help">For outlet commands, use the full command you learned from RFLink/HA logs.</p>
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
          <p class="help">Use these first to confirm the RFLink gateway is responding.</p>
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
          <div class="actions">
            <button class="secondary" data-action="_rfdebugOn">RFDEBUG on</button>
            <button class="secondary" data-action="_rfdebugOff">RFDEBUG off</button>
            <button class="secondary" data-action="_qrfdebugOn">QRFDEBUG on</button>
            <button class="secondary" data-action="_qrfdebugOff">QRFDEBUG off</button>
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
          <p><b>RFLink configuration:</b> ${status.rflink_configured ? "Found" : "Not found"} ${status.rflink_config_source ? `(${status.rflink_config_source})` : ""}</p>
          <p><b>RFLink live bridge:</b> ${status.rflink_connected ? "Connected" : "Not confirmed yet"}</p>
          <p class="help">${status.readiness_detail || "Use Ping on the Debug page to test the gateway."}</p>
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

  _ping() { return this._callService("rflink_raw", "ping_gateway", {}, "Ping sent."); }
  _version() { return this._callService("rflink_raw", "version_gateway", {}, "Version request sent."); }
  _rfdebugOn() { return this._setDebug("rfdebug", true); }
  _rfdebugOff() { return this._setDebug("rfdebug", false); }
  _qrfdebugOn() { return this._setDebug("qrfdebug", true); }
  _qrfdebugOff() { return this._setDebug("qrfdebug", false); }
}

customElements.define("rflink-raw-tools-panel", RFLinkRawToolsPanel);
