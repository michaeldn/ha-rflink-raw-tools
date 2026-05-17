const APP_BUILD_ID = "ha-addon-three-tab-20260517";

class RFLinkRawToolsPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._timer = null;
    this._rendered = false;
    this._autoClearedUnknown = false;
    this._state = {
      tab: this._initialTab(),
      busy: false,
      message: "",
      error: "",
      rawCommand: this._migrateOldSavedCommand(),
      repeat: Number(localStorage.getItem("rflink_raw_tools.repeat") || 1),
      delayMs: Number(localStorage.getItem("rflink_raw_tools.delayMs") || 250),
      port: localStorage.getItem("rflink_raw_tools.port") || "/dev/ttyUSB0",
      status: {
        readiness: "checking",
        readiness_detail: "Loading status…",
        rfdebug: false,
        qrfdebug: false,
      },
      entities: [],
      logs: [],
      aliases: [],
      teach: {
        id: "",
        name: "",
        entity_type: "switch",
        device_id: "",
        on_command: "",
        off_command: "",
        source_packet: "",
        notes: "",
      },
      firmwareLab: {
        project_name: "Digiten remote",
        notes: "",
        active: false,
        captures: [],
      },
      firmwareButtonLabel: "Digiten ON",
      firmwareButtonNotes: "",
      firmwareReport: "",
    };
  }


  _initialTab() {
    const stored = localStorage.getItem("rflink_raw_tools.tab") || "overview";
    if (["overview", "configuration", "log", "send", "captured", "teach", "firmware", "debug", "setup"].includes(stored)) return stored;
    return "overview";
  }

  _primaryTab(tab = this._state.tab) {
    if (["send", "teach", "firmware", "setup", "configuration"].includes(tab)) return "configuration";
    if (["captured", "debug", "log"].includes(tab)) return "log";
    return "overview";
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) {
      this._render();
      this._rendered = true;
    }
    this._loadAll();
  }

  connectedCallback() {
    if (this._timer) return;
    this._timer = window.setInterval(() => this._loadAll(false), 12000);
  }

  disconnectedCallback() {
    if (this._timer) window.clearInterval(this._timer);
    this._timer = null;
  }

  _escape(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  _attr(value) {
    return this._escape(value);
  }

  _formatError(e) {
    if (!e) return "Unknown error";
    if (typeof e === "string") return e;
    return e.message || e.error || JSON.stringify(e);
  }

  _isUnknownCommandText(v) {
    const t = String(v || "").trim();
    return t === "Unknown command";
  }

  _safeError(e) {
    const m = this._formatError(e);
    return this._isUnknownCommandText(m)
      ? "RFLink rejected that command. Use a real learned device command, not a placeholder/example."
      : m;
  }

  _sanitizeStatus(s) {
    const c = { ...(s || {}) };
    if (this._isUnknownCommandText(c.last_error)) c.last_error = "";
    if (this._isUnknownCommandText(c.last_result)) c.last_result = "";
    return c;
  }

  async _autoClearStaleUnknown(s) {
    if (!s || this._autoClearedUnknown) return;
    if (this._isUnknownCommandText(s.last_error) || this._isUnknownCommandText(s.last_result)) {
      this._autoClearedUnknown = true;
      try {
        await this._hass.callService("rflink_raw", "clear_status", {});
      } catch (e) {}
    }
  }

  _normalizeRawCommand(raw) {
    return String(raw || "").trim().replace(/;+$/g, "").toUpperCase();
  }

  _rawCommandKind(raw) {
    const n = this._normalizeRawCommand(raw);
    if (n === "10;PING" || n === "PING") return "status";
    if (n === "10;VERSION" || n === "VERSION") return "version";
    return "device";
  }

  _migrateOldSavedCommand() {
    const s = localStorage.getItem("rflink_raw_tools.rawCommand");
    const k = this._rawCommandKind(s);
    if (k === "status" || k === "version") {
      localStorage.removeItem("rflink_raw_tools.rawCommand");
      return "";
    }
    return s || "";
  }

  _debugLocalKey(t) {
    return `rflink_raw_tools.${t}`;
  }

  _debugEnabled(t) {
    const l = localStorage.getItem(this._debugLocalKey(t));
    if (l === "true") return true;
    if (l === "false") return false;
    return Boolean(this._state.status && this._state.status[t]);
  }

  async _loadAll(render = true) {
    await this._loadStatus(render);
    if (this._state.tab === "captured") await this._loadCaptured(false);
    if (this._state.tab === "teach") await this._loadAliases(false);
    if (this._state.tab === "firmware") await this._loadFirmwareLab(false);
  }

  async _loadStatus(render = true) {
    if (!this._hass) return;
    try {
      const raw = await this._hass.callApi("GET", "rflink_raw/status");
      await this._autoClearStaleUnknown(raw);
      this._state.status = this._sanitizeStatus(raw);
      if (!this._state.busy) this._state.error = "";
      if (render) this._update();
    } catch (e) {
      this._state.status = {
        readiness: "status_api_unavailable",
        readiness_detail: `Status API unavailable: ${this._safeError(e)}`,
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
      if (render) this._update();
    }
  }

  async _loadCaptured(render = true) {
    if (!this._hass) return;
    try {
      const [entities, logs] = await Promise.all([
        this._hass.callApi("GET", "rflink_raw/entities"),
        this._hass.callApi("GET", "rflink_raw/logs"),
      ]);
      this._state.entities = entities.entities || [];
      this._state.logs = logs.lines || [];
      this._state.error = "";
    } catch (e) {
      this._state.error = `Could not load captured data: ${this._safeError(e)}`;
    }
    if (render) this._update();
  }

  async _loadAliases(render = true) {
    if (!this._hass) return;
    try {
      const data = await this._hass.callApi("GET", "rflink_raw/aliases");
      this._state.aliases = data.aliases || [];
    } catch (e) {
      this._state.error = `Could not load aliases: ${this._safeError(e)}`;
    }
    if (render) this._update();
  }

  async _loadFirmwareLab(render = true) {
    if (!this._hass) return;
    try {
      const data = await this._hass.callApi("GET", "rflink_raw/firmware_lab");
      this._state.firmwareLab = data.lab || {};
      this._state.firmwareReport = data.report || "";
    } catch (e) {
      this._state.error = `Could not load Firmware Lab: ${this._safeError(e)}`;
    }
    if (render) this._update();
  }

  async _callService(domain, service, data = {}, success = "Done.") {
    this._state.busy = true;
    this._state.error = "";
    this._state.message = "";
    this._update();
    try {
      await this._hass.callService(domain, service, data);
      this._state.message = success;
      await this._loadStatus(false);
    } catch (e) {
      this._state.message = "";
      this._state.error = this._safeError(e);
    } finally {
      this._state.busy = false;
      this._update();
    }
  }

  _saveInputs() {
    localStorage.setItem("rflink_raw_tools.rawCommand", this._state.rawCommand || "");
    localStorage.setItem("rflink_raw_tools.repeat", String(this._state.repeat || 1));
    localStorage.setItem("rflink_raw_tools.delayMs", String(this._state.delayMs || 250));
    localStorage.setItem("rflink_raw_tools.port", this._state.port || "/dev/ttyUSB0");
  }

  async _sendRaw() {
    const raw = String(this._state.rawCommand || "").trim();
    if (!raw) {
      this._state.error = "Paste a learned RFLink device command first. Use Debug for setup checks.";
      this._state.message = "";
      this._update();
      return;
    }
    const k = this._rawCommandKind(raw);
    if (k === "status") return this._checkSetup();
    if (k === "version") return this._checkVersion();
    this._saveInputs();
    await this._callService(
      "rflink_raw",
      "send_raw",
      {
        raw_command: raw,
        repeat: Number(this._state.repeat || 1),
        delay_ms: Number(this._state.delayMs || 250),
      },
      "RFLink command sent."
    );
  }

  _checkSetup() {
    return this._callService("rflink_raw", "ping_gateway", {}, "RFLink setup check complete.");
  }

  _checkVersion() {
    return this._callService("rflink_raw", "version_gateway", {}, "RFLink version-support check complete.");
  }

  async _installRflinkYaml() {
    this._saveInputs();
    await this._callService(
      "rflink_raw",
      "install_rflink_yaml",
      { port: this._state.port || "/dev/ttyUSB0" },
      "RFLink YAML install check complete. Restart Home Assistant if YAML was added."
    );
  }

  async _setDebug(t, en) {
    this._state.status = this._state.status || {};
    this._state.status[t] = Boolean(en);
    localStorage.setItem(this._debugLocalKey(t), String(Boolean(en)));
    const label = t === "rfdebug" ? "Decoded RFLink logging" : "Raw RF capture logging";
    this._state.message = `${label} ${en ? "enabled" : "disabled"}.`;
    this._state.error = "";
    this._update();
    await this._callService(
      "rflink_raw",
      "set_debug",
      { debug_type: t, enabled: Boolean(en) },
      `${label} ${en ? "enabled" : "disabled"}.`
    );
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

  _copyCommand(cmd) {
    this._state.rawCommand = cmd || "";
    this._state.tab = "send";
    localStorage.setItem("rflink_raw_tools.tab", "send");
    this._state.message = "Command copied to Send.";
    this._state.error = "";
    this._update();
  }

  _input(f, v) {
    this._state[f] = v;
    this._update();
  }

  _setTab(t) {
    this._state.tab = t;
    localStorage.setItem("rflink_raw_tools.tab", t);
    this._state.error = "";
    this._state.message = "";
    this._update();
    if (t === "captured") this._loadCaptured();
    if (t === "teach") this._loadAliases();
    if (t === "firmware") this._loadFirmwareLab();
  }

  _slug(v) {
    return String(v || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/^_+|_+$/g, "") || "rflink_alias";
  }

  _setTeachField(f, v) {
    this._state.teach = { ...(this._state.teach || {}), [f]: v };
  }

  _teachFromEntity(idx) {
    const i = (this._state.entities || [])[Number(idx)];
    if (!i) return;
    this._state.teach = {
      id: this._slug(i.name || i.send_device_id || i.device_key),
      name: i.name || i.device_key || i.entity_id,
      entity_type: "switch",
      device_id: i.send_device_id || "",
      on_command: i.candidate_on || "",
      off_command: i.candidate_off || "",
      source_packet: "",
      notes: `Created from ${i.entity_id}`,
    };
    this._setTab("teach");
  }

  _teachFromLog(idx) {
    const rows = (this._state.logs || []).filter(i => i.raw_packet || i.send_candidate).slice().reverse();
    const i = rows[Number(idx)];
    if (!i) return;
    const cmd = i.send_candidate || "";
    const device = cmd.includes(";") ? cmd.split(";")[0] : "";
    this._state.teach = {
      id: this._slug(device || i.protocol || "captured_packet"),
      name: device || i.protocol || "Captured RFLink packet",
      entity_type: "switch",
      device_id: device,
      on_command: cmd.toLowerCase().endsWith(";off") ? "" : cmd,
      off_command: cmd.toLowerCase().endsWith(";off") ? cmd : "",
      source_packet: i.raw_packet || "",
      notes: "Created from captured RFLink packet",
    };
    this._setTab("teach");
  }

  async _saveAlias() {
    if (!this._state.teach.name || !this._state.teach.device_id) {
      this._state.error = "Alias needs a friendly name and RFLink device id.";
      this._state.message = "";
      this._update();
      return;
    }
    this._state.busy = true;
    this._state.error = "";
    this._state.message = "";
    this._update();
    try {
      const res = await this._hass.callApi("POST", "rflink_raw/aliases", this._state.teach);
      this._state.aliases = res.aliases || [];
      this._state.message = "Alias saved in RFLink Raw Tools.";
      this._state.teach = {
        id: "",
        name: "",
        entity_type: "switch",
        device_id: "",
        on_command: "",
        off_command: "",
        source_packet: "",
        notes: "",
      };
    } catch (e) {
      this._state.error = this._safeError(e);
    } finally {
      this._state.busy = false;
      this._update();
    }
  }

  async _deleteAlias(id) {
    this._state.busy = true;
    this._state.error = "";
    this._update();
    try {
      const res = await this._hass.callApi("POST", "rflink_raw/aliases", { delete: true, id });
      this._state.aliases = res.aliases || [];
      this._state.message = "Alias deleted.";
    } catch (e) {
      this._state.error = this._safeError(e);
    } finally {
      this._state.busy = false;
      this._update();
    }
  }

  _editAlias(id) {
    const a = (this._state.aliases || []).find(x => x.id === id);
    if (!a) return;
    this._state.teach = { ...a };
    this._update();
  }

  async _testAliasCommand(cmd) {
    if (!cmd) {
      this._state.error = "No command available for this alias.";
      this._update();
      return;
    }
    await this._callService("rflink_raw", "send_raw", { raw_command: cmd, repeat: 1, delay_ms: 250 }, "Alias command sent.");
  }

  _setLabField(f, v) {
    this._state.firmwareLab = { ...(this._state.firmwareLab || {}), [f]: v };
  }

  _setFirmwareField(f, v) {
    this._state[f] = v;
  }

  async _firmwarePost(data, success) {
    this._state.busy = true;
    this._state.error = "";
    this._state.message = "";
    this._update();
    try {
      const res = await this._hass.callApi("POST", "rflink_raw/firmware_lab", data);
      this._state.firmwareLab = res.lab || {};
      this._state.firmwareReport = res.report || "";
      this._state.message = success || "Firmware Lab updated.";
    } catch (e) {
      this._state.error = this._safeError(e);
    } finally {
      this._state.busy = false;
      this._update();
    }
  }

  async _startFirmwareLab() {
    const lab = this._state.firmwareLab || {};
    await this._firmwarePost(
      {
        action: "start",
        project_name: lab.project_name || "Digiten remote",
        notes: lab.notes || "",
        reset: false,
      },
      "Firmware Lab capture started. Name each button capture anything you want, then press the remote and capture it."
    );
  }

  async _stopFirmwareLab() {
    await this._firmwarePost({ action: "stop" }, "Firmware Lab capture stopped.");
  }

  async _captureFirmwareButton() {
    await this._firmwarePost(
      {
        action: "capture",
        label: this._state.firmwareButtonLabel || "Unnamed button",
        notes: this._state.firmwareButtonNotes || "",
      },
      "Button capture stored."
    );
  }

  async _clearFirmwareLab() {
    await this._firmwarePost({ action: "clear" }, "Firmware Lab cleared.");
  }

  async _deleteFirmwareCapture(id) {
    await this._firmwarePost({ action: "delete_capture", id }, "Capture deleted.");
  }

  async _saveFirmwareNotes() {
    const lab = this._state.firmwareLab || {};
    await this._firmwarePost(
      { action: "update", project_name: lab.project_name || "", notes: lab.notes || "" },
      "Firmware Lab notes saved."
    );
  }

  _downloadFirmwareReport() {
    const text = this._state.firmwareReport || "";
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `rflink-firmware-lab-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async _copyFirmwareReport() {
    await navigator.clipboard.writeText(this._state.firmwareReport || "");
    this._state.message = "Firmware Lab report copied.";
    this._state.error = "";
    this._update();
  }

  _statusTone(readiness = (this._state.status || {}).readiness) {
    if (readiness === "ready" || readiness === "loaded") return "ok";
    if (readiness === "not_configured" || readiness === "error") return "bad";
    return "warn";
  }

  _yesNo(v) {
    return v ? "Yes" : "No";
  }

  _statusBadge() {
    const r = (this._state.status || {}).readiness || "checking";
    const labels = {
      ready: "RFLink ready",
      loaded: "RFLink loaded",
      configured_needs_restart: "Restart needed",
      not_configured: "Not configured",
      status_api_unavailable: "Status unavailable",
      checking: "Checking status…",
    };
    return `<span class="status-pill ${this._statusTone(r)}"><span class="pulse-dot"></span>${this._escape(labels[r] || "Checking status…")}</span>`;
  }

  _statusCards() {
    const s = this._state.status || {};
    const cards = [
      {
        label: "RFLink gateway",
        value: s.rflink_connected ? "Connected" : s.rflink_loaded ? "Loaded" : "Not confirmed",
        tone: s.rflink_connected || s.rflink_loaded ? "ok" : "warn",
        detail: s.readiness_detail || "Use Check RFLink setup.",
      },
      {
        label: "RFLink YAML",
        value: s.rflink_configured ? "Found" : "Missing",
        tone: s.rflink_configured ? "ok" : "bad",
        detail: s.rflink_configured ? "Top-level rflink: block found." : "Setup can add a conservative block.",
      },
      {
        label: "Logging",
        value: this._debugEnabled("qrfdebug") || this._debugEnabled("rfdebug") ? "Enabled" : "Idle",
        tone: this._debugEnabled("qrfdebug") || this._debugEnabled("rfdebug") ? "ok" : "neutral",
        detail: `${this._debugEnabled("rfdebug") ? "Decoded on" : "Decoded off"} · ${this._debugEnabled("qrfdebug") ? "Raw on" : "Raw off"}`,
      },
    ];
    return cards.map(card => `<article class="status-card ${card.tone}">
      <div class="status-card-label">${this._escape(card.label)}</div>
      <div class="status-card-value">${this._escape(card.value)}</div>
      <div class="status-card-detail">${this._escape(card.detail)}</div>
    </article>`).join("");
  }

  _feedback() {
    return `${this._state.message ? `<div class="message">${this._escape(this._state.message)}</div>` : ""}${this._state.error ? `<div class="error">${this._escape(this._state.error)}</div>` : ""}`;
  }

  _overviewView() {
    const s = this._state.status || {};
    const version = s.version || "0.0.1";
    const yamlState = s.rflink_configured ? "Configured" : "Not configured";
    const loadedState = s.rflink_loaded ? "Loaded" : "Not loaded";
    const bridgeState = s.rflink_connected ? "Connected" : (s.rflink_loaded ? "Loaded" : "Not confirmed");
    const readiness = s.readiness_detail || "Use Check setup to confirm Home Assistant's RFLink bridge.";
    const lastRows = [
      s.last_command ? ["Last command", s.last_command] : null,
      s.last_result ? ["Last result", s.last_result] : null,
      s.last_error ? ["Last error", s.last_error] : null,
      s.last_updated ? ["Updated", s.last_updated] : null,
    ].filter(Boolean);

    return `<div class="addon-page">
      <section class="addon-card addon-info-card">
        <div class="addon-header-row">
          <div>
            <h2>RFLink Raw Tools (Beta)</h2>
            <p class="version-line">Current version: ${this._escape(version)} <span class="fake-link">(RFLink control center)</span></p>
          </div>
          <div class="connection-mark ${s.rflink_connected ? "online" : "offline"}" title="${this._attr(bridgeState)}">${s.rflink_connected ? "●" : "⊘"}</div>
        </div>

        <div class="addon-badges">
          <span class="addon-badge rating"><b>RF</b> 433 MHz</span>
          <span class="addon-badge blue">Home Assistant</span>
          <span class="addon-badge blue">RFLink</span>
          <span class="addon-badge green">Capture</span>
          <span class="addon-badge blue">Firmware Lab</span>
        </div>

        <p class="addon-description">A Home Assistant app for RFLink setup, RF capture, learned command sending, friendly aliases, and unsupported-remote evidence. ⚠️ BETA VERSION - use learned commands only; do not send placeholder examples.</p>
        <p class="addon-description">Status: <b>${this._escape(readiness)}</b></p>

        <div class="addon-settings">
          <div class="addon-setting-row">
            <div><b>RFLink YAML</b><span>${this._escape(yamlState)}. Setup can add a conservative top-level <code>rflink:</code> block if missing.</span></div>
            <span class="mini-state ${s.rflink_configured ? "ok" : "warn"}">${this._escape(yamlState)}</span>
          </div>
          <div class="addon-setting-row">
            <div><b>Home Assistant RFLink bridge</b><span>${this._escape(loadedState)} / ${this._escape(bridgeState)}.</span></div>
            <span class="mini-state ${s.rflink_connected || s.rflink_loaded ? "ok" : "bad"}">${this._escape(bridgeState)}</span>
          </div>
          <div class="addon-setting-row">
            <div><b>Raw RF capture logging</b><span>Enable this, press the physical remote, then open Captured.</span></div>
            <label class="switch"><input type="checkbox" data-toggle-debug="qrfdebug" ${this._debugEnabled("qrfdebug") ? "checked" : ""}><span class="slider"></span></label>
          </div>
          <div class="addon-setting-row">
            <div><b>Decoded RFLink logging</b><span>Useful for readable protocol messages in Home Assistant logs.</span></div>
            <label class="switch"><input type="checkbox" data-toggle-debug="rfdebug" ${this._debugEnabled("rfdebug") ? "checked" : ""}><span class="slider"></span></label>
          </div>
        </div>

        <div class="addon-footer-actions">
          <button data-action="_checkSetup">Check setup</button>
          <span class="footer-spacer"></span>
          <button class="secondary" data-tablink="log">Log</button>
          <button class="secondary" data-tablink="configuration">Configuration</button>
          <button class="danger-soft" data-action="_clearStatus">Clear status</button>
        </div>
        ${this._feedback()}
      </section>

      <section class="addon-card readme-card">
        <h2>RFLink Raw Tools Home Assistant App</h2>
        <div class="repo-badges">
          <span>hacs <b>yes</b></span>
          <span>local app <b>yes</b></span>
          <span>maintained <b>yes</b></span>
        </div>
        <p>This is a Home Assistant sidebar app for RFLink users who need a real GUI instead of generated Lovelace dashboards, fake action switches, and configuration drift.</p>
        <p>Recommended flow: use Log to turn on raw capture logging, press the physical remote, then use Configuration to capture, teach, and send usable ON/OFF commands.</p>
        <div class="quick-actions-line">
          <button class="secondary" data-tablink="send">Send</button>
          <button class="secondary" data-tablink="teach">Teach alias</button>
          <button class="secondary" data-tablink="firmware">Firmware Lab</button>
          <button class="secondary" data-tablink="log">Log</button>
        </div>
      </section>

      ${lastRows.length ? `<section class="addon-card"><h3>Recent RFLink activity</h3><div class="activity-list">${lastRows.map(row => `<div><span>${this._escape(row[0])}</span><code>${this._escape(row[1])}</code></div>`).join("")}</div></section>` : ""}
    </div>`;
  }

  _quickCard(tab, title, text) {
    return `<button class="quick-card" data-tablink="${this._attr(tab)}">
      <span class="quick-title">${this._escape(title)}</span>
      <span class="quick-text">${this._escape(text)}</span>
    </button>`;
  }

  _sendView() {
    return `<div class="grid">
      <div class="card primary-card">
        <div class="card-kicker">Command sender</div>
        <h2>Send RFLink device command</h2>
        <p class="help">Only send a real command copied from <b>Captured</b> or learned from RFLink logs. Examples are documentation, not working device IDs.</p>
        <label>RFLink command</label>
        <textarea data-field="rawCommand" placeholder="Paste from Captured, for example: newkaku_0000c6c2_1;on">${this._escape(this._state.rawCommand || "")}</textarea>
        <div class="row">
          <div><label>Repeat</label><input data-field="repeat" type="number" min="1" value="${this._attr(this._state.repeat || 1)}"></div>
          <div><label>Delay between repeats (ms)</label><input data-field="delayMs" type="number" min="0" value="${this._attr(this._state.delayMs || 250)}"></div>
        </div>
        <div class="actions">
          <button data-action="_sendRaw" ${this._state.busy ? "disabled" : ""}>Send command</button>
          <button class="secondary" data-action="_clearRawCommand">Clear command</button>
          <button class="secondary" data-tablink="captured">Open Captured</button>
        </div>
        ${this._feedback()}
      </div>

      <div class="card">
        <div class="card-kicker">Accepted formats</div>
        <h2>Command format</h2>
        <p class="help">Documentation only. Paste an actual candidate copied from Captured.</p>
        <div class="example no-copy"><code>newkaku_0000c6c2_1;on</code></div>
        <div class="example no-copy"><code>newkaku_0000c6c2_1;off</code></div>
        <div class="example no-copy"><code>10;NewKaku;0000c6c2;1;ON;</code></div>
        <p class="help">If RFLink returns <code>'id'</code>, that device/protocol is not sendable through Home Assistant RFLink. It is usually receive-only, sensor-like, RF noise, or unsupported by the RFLink database.</p>
      </div>
    </div>`;
  }

  _capturedView() {
    const entities = this._state.entities || [];
    const controllable = entities.filter(i => i.candidate_on || i.candidate_off).length;
    const rawPackets = (this._state.logs || []).filter(i => i.raw_packet || i.send_candidate);
    const otherLogs = (this._state.logs || []).filter(i => !i.raw_packet && !i.send_candidate);

    const entityCards = entities.map((i, idx) => {
      const isControllable = !!(i.candidate_on || i.candidate_off);
      const kind = isControllable ? "Command-capable" : "Read-only / sensor";
      return `<div class="entity-card ${isControllable ? "can-send" : "read-only"}">
        <div class="entity-top">
          <div>
            <div class="entity-title">${this._escape(i.name || i.entity_id)}</div>
            <code class="entity-id">${this._escape(i.entity_id)}</code>
          </div>
          <span class="state-pill">${this._escape(i.state || "unknown")}</span>
        </div>
        <div class="entity-meta">
          <span>Protocol <b>${this._escape(i.protocol || "—")}</b></span>
          <span>Address <b>${this._escape(i.address || "—")}</b></span>
          ${i.switch ? `<span>Switch <b>${this._escape(i.switch)}</b></span>` : ""}
          <span>${kind}</span>
        </div>
        <div class="device-key">RFLink device key <code>${this._escape(i.device_key || "—")}</code></div>
        ${isControllable ? `<div class="command-box"><button class="secondary tiny" data-teach-entity="${idx}">Teach as device</button>
          ${i.candidate_on ? `<div class="command-row"><code>${this._escape(i.candidate_on)}</code><button class="tiny" data-copy-command="${this._attr(i.candidate_on)}">Copy ON</button></div>` : ""}
          ${i.candidate_off ? `<div class="command-row"><code>${this._escape(i.candidate_off)}</code><button class="tiny" data-copy-command="${this._attr(i.candidate_off)}">Copy OFF</button></div>` : ""}
        </div>` : `<div class="no-command">No send command suggested for this entity type. Sensors/read-only entities are receive-only.</div>`}
      </div>`;
    }).join("");

    const rawRows = rawPackets.slice().reverse().map((i, idx) => `<div class="raw-card">
      ${i.raw_packet ? `<div class="raw-block"><div class="label">Raw packet</div><code>${this._escape(i.raw_packet)}</code></div>` : ""}
      ${i.send_candidate ? `<div class="raw-block candidate-send"><div class="label">Send candidate</div><code>${this._escape(i.send_candidate)}</code><button class="tiny" data-copy-command="${this._attr(i.send_candidate)}">Copy to Send</button><button class="secondary tiny" data-teach-log="${idx}">Teach</button></div>` : ""}
      <details><summary>Log line</summary><pre>${this._escape(i.line)}</pre></details>
    </div>`).join("");

    const otherLogRows = otherLogs.slice().reverse().slice(0, 8).map(i => `<div class="raw-card muted-card"><pre>${this._escape(i.line)}</pre></div>`).join("");

    return `<div class="captured-layout">
      <section class="card hero-card">
        <div class="hero-row">
          <div>
            <div class="card-kicker">Discovery</div>
            <h2>Captured RFLink data</h2>
            <p class="help">Turn RFLink discovery into usable ON/OFF commands. Entities are not the same as raw packets; raw packets appear after raw logging captures a remote press.</p>
          </div>
          <div class="stat-row">
            <div class="stat"><b>${entities.length}</b><span>entities</span></div>
            <div class="stat"><b>${controllable}</b><span>command candidates</span></div>
            <div class="stat"><b>${rawPackets.length}</b><span>raw packets</span></div>
          </div>
        </div>
        <div class="actions">
          <button data-action="_loadCaptured">Refresh captured data</button>
          <button class="secondary" data-tablink="log">Turn on raw logging</button>
        </div>
        ${this._feedback()}
      </section>

      <section class="captured-columns">
        <div class="card">
          <div class="section-heading">
            <div>
              <h3>Discovered RFLink entities</h3>
              <p class="help">These come from Home Assistant's RFLink entity registry. Command-capable lights/switches show candidate send commands.</p>
            </div>
          </div>
          ${entityCards ? `<div class="entity-grid">${entityCards}</div>` : `<div class="empty-state"><b>No RFLink entities found yet.</b><span>Enable RFLink, press a remote, then refresh.</span></div>`}
        </div>

        <aside class="card raw-panel">
          <h3>Raw RFLink packets</h3>
          <p class="help">To populate this panel: <b>Debug → Raw RF capture logging</b>, press one physical remote button, then refresh. This uses Home Assistant logs; it does not send rfdebug/qrfdebug commands to the gateway.</p>
          ${rawRows || `<div class="empty-state"><b>No raw RFLink packets found yet.</b><span>The app looked in <code>home-assistant.log</code> for recent <code>10;</code> or <code>20;</code> RFLink packets.</span></div>`}
          ${!rawRows && otherLogRows ? `<h4>Other recent RFLink log lines</h4>${otherLogRows}` : ""}
        </aside>
      </section>
    </div>`;
  }

  _teachView() {
    const t = this._state.teach || {};
    const aliases = this._state.aliases || [];
    const aliasCards = aliases.map(a => `<div class="alias-card">
      <div class="entity-top"><div><div class="entity-title">${this._escape(a.name)}</div><code class="entity-id">${this._escape(a.device_id)}</code></div><span class="state-pill">${this._escape(a.entity_type)}</span></div>
      <div class="command-box">
        ${a.on_command ? `<div class="command-row"><code>${this._escape(a.on_command)}</code><button class="tiny" data-alias-test="${this._attr(a.on_command)}">Test ON</button><button class="secondary tiny" data-copy-command="${this._attr(a.on_command)}">Copy</button></div>` : ""}
        ${a.off_command ? `<div class="command-row"><code>${this._escape(a.off_command)}</code><button class="tiny" data-alias-test="${this._attr(a.off_command)}">Test OFF</button><button class="secondary tiny" data-copy-command="${this._attr(a.off_command)}">Copy</button></div>` : ""}
      </div>
      <div class="actions"><button class="secondary" data-edit-alias="${this._attr(a.id)}">Edit</button><button class="secondary" data-delete-alias="${this._attr(a.id)}">Delete</button></div>
      ${a.source_packet ? `<details><summary>Source packet</summary><pre>${this._escape(a.source_packet)}</pre></details>` : ""}
    </div>`).join("");

    return `<div class="captured-layout">
      <section class="card hero-card"><div class="card-kicker">Friendly names</div><h2>Teach / Alias</h2><p class="help">Create friendly RFLink Raw Tools names from decoded RFLink packets or Captured command candidates. Saved aliases appear inside RFLink Raw Tools. Home Assistant entity exposure is disabled in this safe-loader build.</p>${this._feedback()}</section>
      <section class="captured-columns">
        <div class="card"><h3>Alias editor</h3>
          <label>Friendly name</label><input data-teach-field="name" value="${this._attr(t.name || "")}" placeholder="Bedroom AC outlet">
          <label>Entity type</label><select data-teach-field="entity_type"><option value="switch" ${(t.entity_type || "switch") === "switch" ? "selected" : ""}>switch</option><option value="light" ${t.entity_type === "light" ? "selected" : ""}>light-style switch</option><option value="button" ${t.entity_type === "button" ? "selected" : ""}>button / one-shot</option></select>
          <label>RFLink device id</label><input data-teach-field="device_id" value="${this._attr(t.device_id || "")}" placeholder="newkaku_0000c6c2_1">
          <label>ON command</label><input data-teach-field="on_command" value="${this._attr(t.on_command || "")}" placeholder="newkaku_0000c6c2_1;on">
          <label>OFF command</label><input data-teach-field="off_command" value="${this._attr(t.off_command || "")}" placeholder="newkaku_0000c6c2_1;off">
          <label>Source packet / notes</label><textarea data-teach-field="source_packet" placeholder="20;... or notes from the captured packet">${this._escape(t.source_packet || "")}</textarea><textarea data-teach-field="notes" placeholder="Notes">${this._escape(t.notes || "")}</textarea>
          <div class="actions"><button data-action="_saveAlias" ${this._state.busy ? "disabled" : ""}>Save alias</button><button class="secondary" data-tablink="captured">Back to Captured</button></div>
        </div>
        <aside class="card raw-panel"><h3>Saved aliases</h3>${aliasCards || `<div class="empty-state"><b>No aliases saved yet.</b><span>Use Captured → Teach as device, or fill the editor manually.</span></div>`}</aside>
      </section>
    </div>`;
  }

  _firmwareView() {
    const lab = this._state.firmwareLab || {};
    const captures = lab.captures || [];
    const captureCards = captures.slice().reverse().map(c => `<div class="alias-card">
      <div class="entity-top"><div><div class="entity-title">${this._escape(c.label || "Unnamed capture")}</div><code class="entity-id">${this._escape(c.captured_at || "")}</code></div><span class="state-pill">${this._escape((c.summary && c.summary.line_count) || 0)} lines</span></div>
      ${c.notes ? `<p class="help">${this._escape(c.notes)}</p>` : ""}
      <div class="entity-meta">
        <span>Raw packets <b>${this._escape((c.summary && c.summary.raw_packet_count) || 0)}</b></span>
        <span>Pulse lines <b>${this._escape((c.summary && c.summary.pulse_line_count) || 0)}</b></span>
        <span>Protocols <b>${this._escape(((c.summary && c.summary.protocols) || []).join(", ") || "—")}</b></span>
      </div>
      <details><summary>Captured log lines</summary><pre>${this._escape((c.lines || []).join("\n") || "No matching RFLink debug/pulse lines found for this capture.")}</pre></details>
      <div class="actions"><button class="secondary" data-delete-firmware-capture="${this._attr(c.id)}">Delete capture</button></div>
    </div>`).join("");

    return `<div class="captured-layout">
      <section class="card hero-card">
        <div class="hero-row"><div><div class="card-kicker">Protocol evidence</div><h2>Firmware Lab</h2><p class="help">Capture unsupported remote evidence for firmware/protocol work. You can name each capture anything you want: <b>Digiten ON</b>, <b>Digiten OFF</b>, <b>Button 1</b>, etc.</p></div><div class="stat-row"><div class="stat"><b>${captures.length}</b><span>captures</span></div><div class="stat"><b>${lab.active ? "ON" : "OFF"}</b><span>capture mode</span></div><div class="stat"><b>${captures.reduce((n, c) => n + ((c.summary && c.summary.line_count) || 0), 0)}</b><span>stored lines</span></div></div></div>
        ${this._feedback()}
      </section>
      <section class="captured-columns">
        <div class="card"><h3>Capture setup</h3>
          <label>Lab/project name</label><input data-lab-field="project_name" value="${this._attr(lab.project_name || "Digiten remote")}" placeholder="Digiten remote">
          <label>Protocol notes</label><textarea data-lab-field="notes" placeholder="Paste protocol notes, observations, battery/device model, FCC ID, button behavior, repeat count, etc.">${this._escape(lab.notes || "")}</textarea>
          <div class="actions"><button data-action="_startFirmwareLab" ${this._state.busy ? "disabled" : ""}>Start RF debug capture</button><button class="secondary" data-action="_stopFirmwareLab">Stop capture</button><button class="secondary" data-action="_saveFirmwareNotes">Save notes</button></div>
          <hr>
          <h3>Store one button press</h3>
          <p class="help">Type any label you want, press the physical remote button, then click Store latest lines. Typing will not refresh or shift the screen.</p>
          <label>Button/capture name</label><input data-firmware-field="firmwareButtonLabel" value="${this._attr(this._state.firmwareButtonLabel || "Digiten ON")}" placeholder="Digiten ON">
          <label>Button notes</label><textarea data-firmware-field="firmwareButtonNotes" placeholder="Example: held for 1 second, outlet ON, red LED flashed">${this._escape(this._state.firmwareButtonNotes || "")}</textarea>
          <div class="actions"><button data-action="_captureFirmwareButton" ${this._state.busy ? "disabled" : ""}>Store latest RFLink lines for this button</button><button class="secondary" data-action="_clearFirmwareLab">Clear lab</button></div>
          <p class="help">This uses Home Assistant RFLink logging. If no pulse/debug lines appear, RFLink/HA is not exposing raw firmware-level timing data yet.</p>
        </div>
        <aside class="card raw-panel"><h3>Unsupported-device report</h3><p class="help">Export this for RFLink firmware/protocol support or future firmware development.</p><div class="actions"><button data-action="_downloadFirmwareReport">Download report</button><button class="secondary" data-action="_copyFirmwareReport">Copy report</button></div><h3>Stored captures</h3>${captureCards || `<div class="empty-state"><b>No button captures yet.</b><span>Start capture, press the remote, then store latest RFLink lines.</span></div>`}</aside>
      </section>
    </div>`;
  }

  _debugView() {
    return `<div class="grid">
      <div class="card primary-card"><div class="card-kicker">Status checks</div><h2>Diagnostics</h2><p class="help">These checks do not send RF hardware commands and should not show red errors.</p><div class="actions"><button data-action="_checkSetup">Check RFLink setup</button><button class="secondary" data-action="_checkVersion">Check version support</button><button class="secondary" data-action="_clearStatus">Clear status</button></div>${this._feedback()}</div>
      <div class="card"><div class="card-kicker">Logging</div><h2>Logging switches</h2><p class="help">This changes Home Assistant RFLink logging only; it does not send rfdebug/qrfdebug commands to the gateway.</p><p class="help">Use Raw RF capture logging to learn a remote. Switches keep their visual state across tabs.</p>${this._toggle("rfdebug", "Decoded RFLink logging", "decoded protocol messages in Home Assistant logs")}${this._toggle("qrfdebug", "Raw RF capture logging", "raw 433 MHz capture output used to learn remotes")}</div>
    </div>`;
  }

  _toggle(id, title, help) {
    return `<div class="toggle-row"><div><div class="toggle-title">${this._escape(title)}</div><div class="toggle-help">${this._debugEnabled(id) ? "Enabled" : "Disabled"} — ${this._escape(help)}.</div></div><label class="switch"><input type="checkbox" data-toggle-debug="${this._attr(id)}" ${this._debugEnabled(id) ? "checked" : ""}><span class="slider"></span></label></div>`;
  }

  _setupView() {
    const s = this._state.status || {};
    return `<div class="grid">
      <div class="card primary-card"><div class="card-kicker">Configuration</div><h2>Setup</h2><div class="detail-list"><p><b>Integration version:</b> ${this._escape(s.version || "0.0.1")}</p><p><b>RFLink YAML:</b> ${s.rflink_configured ? "Found" : "Not found"}</p><p><b>Home Assistant RFLink loaded:</b> ${s.rflink_loaded ? "Yes" : "No"}</p><p><b>RFLink live bridge:</b> ${s.rflink_connected ? "Connected" : "Not confirmed"}</p></div><p class="help">${this._escape(s.readiness_detail || "Use Check RFLink setup.")}</p><div class="actions"><button data-action="_checkSetup">Check RFLink setup</button><button class="secondary" data-action="_clearStatus">Clear status</button></div>${this._feedback()}</div>
      <div class="card"><div class="card-kicker">YAML helper</div><h2>Install RFLink YAML</h2><p class="help">Only use this if RFLink YAML is not found. It adds a conservative top-level <code>rflink:</code> block and makes a backup first.</p><label>Serial port</label><input data-field="port" value="${this._attr(this._state.port || "/dev/ttyUSB0")}"><div class="actions"><button data-action="_installRflinkYaml">Install RFLink YAML</button></div><p class="help">After install, restart Home Assistant Core. This does not edit Lovelace dashboards.</p></div>
    </div>`;
  }

  _configurationView() {
    const s = this._state.status || {};
    return `<div class="addon-page">
      <section class="addon-card addon-info-card">
        <div class="addon-header-row">
          <div>
            <h2>Configuration</h2>
            <p class="version-line">RFLink Raw Tools settings and command workflow</p>
          </div>
          <div class="connection-mark ${s.rflink_connected ? "online" : "offline"}">${s.rflink_connected ? "●" : "⊘"}</div>
        </div>
        <div class="addon-settings">
          <div class="addon-setting-row"><div><b>Serial port</b><span>The normal Home Assistant RFLink integration still owns the live RFLink connection.</span></div><code>${this._escape(this._state.port || "/dev/ttyUSB0")}</code></div>
          <div class="addon-setting-row"><div><b>RFLink YAML</b><span>${s.rflink_configured ? "Found in configuration.yaml." : "Not found. Use the YAML helper only if RFLink is not configured."}</span></div><span class="mini-state ${s.rflink_configured ? "ok" : "warn"}">${s.rflink_configured ? "Configured" : "Missing"}</span></div>
          <div class="addon-setting-row"><div><b>Home Assistant RFLink bridge</b><span>${s.rflink_loaded ? "Loaded" : "Not loaded"} / ${s.rflink_connected ? "connected" : "not confirmed"}.</span></div><span class="mini-state ${s.rflink_loaded || s.rflink_connected ? "ok" : "bad"}">${s.rflink_connected ? "Connected" : (s.rflink_loaded ? "Loaded" : "Not ready")}</span></div>
        </div>
        <div class="addon-footer-actions">
          <button data-action="_checkSetup">Check setup</button>
          <button class="secondary" data-action="_checkVersion">Check version support</button>
          <span class="footer-spacer"></span>
          <button class="secondary" data-tablink="send">Send command</button>
          <button class="secondary" data-tablink="captured">Captured</button>
          <button class="secondary" data-tablink="teach">Teach alias</button>
          <button class="secondary" data-tablink="firmware">Firmware Lab</button>
        </div>
        ${this._feedback()}
      </section>

      <section class="grid">
        <div class="card primary-card">
          <div class="card-kicker">Command sender</div>
          <h2>Send learned RFLink command</h2>
          <p class="help">Paste a real command from Captured. Do not use placeholder examples.</p>
          <label>RFLink command</label>
          <textarea data-field="rawCommand" placeholder="newkaku_0000c6c2_1;on">${this._escape(this._state.rawCommand || "")}</textarea>
          <div class="row">
            <div><label>Repeat</label><input data-field="repeat" type="number" min="1" value="${this._attr(this._state.repeat || 1)}"></div>
            <div><label>Delay between repeats (ms)</label><input data-field="delayMs" type="number" min="0" value="${this._attr(this._state.delayMs || 250)}"></div>
          </div>
          <div class="actions"><button data-action="_sendRaw" ${this._state.busy ? "disabled" : ""}>Send command</button><button class="secondary" data-action="_clearRawCommand">Clear</button></div>
        </div>
        <div class="card">
          <div class="card-kicker">YAML helper</div>
          <h2>Install RFLink YAML</h2>
          <p class="help">Only use this if RFLink YAML is not found. It adds a conservative top-level <code>rflink:</code> block and makes a backup first.</p>
          <label>Serial port</label><input data-field="port" value="${this._attr(this._state.port || "/dev/ttyUSB0")}">
          <div class="actions"><button data-action="_installRflinkYaml">Install RFLink YAML</button></div>
          <p class="help">After install, restart Home Assistant Core.</p>
        </div>
      </section>
    </div>`;
  }

  _logView() {
    return `<div class="addon-page">
      <section class="addon-card addon-info-card">
        <div class="addon-header-row">
          <div>
            <h2>Log</h2>
            <p class="version-line">Capture RFLink activity and inspect troubleshooting output</p>
          </div>
        </div>
        <div class="addon-settings">
          <div class="addon-setting-row"><div><b>Raw RF capture logging</b><span>Enable this, press the physical remote, then refresh Captured.</span></div><label class="switch"><input type="checkbox" data-toggle-debug="qrfdebug" ${this._debugEnabled("qrfdebug") ? "checked" : ""}><span class="slider"></span></label></div>
          <div class="addon-setting-row"><div><b>Decoded RFLink logging</b><span>Readable RFLink protocol messages in Home Assistant logs.</span></div><label class="switch"><input type="checkbox" data-toggle-debug="rfdebug" ${this._debugEnabled("rfdebug") ? "checked" : ""}><span class="slider"></span></label></div>
        </div>
        <div class="addon-footer-actions"><button data-action="_loadCaptured">Refresh captured data</button><button class="secondary" data-tablink="captured">Open captured packets</button><button class="secondary" data-action="_clearStatus">Clear status</button></div>
        ${this._feedback()}
      </section>
      ${this._capturedView()}
    </div>`;
  }

  _body() {
    if (this._state.tab === "overview") return this._overviewView();
    if (this._state.tab === "configuration") return this._configurationView();
    if (this._state.tab === "log") return this._logView();
    if (this._state.tab === "captured") return this._capturedView();
    if (this._state.tab === "teach") return this._teachView();
    if (this._state.tab === "firmware") return this._firmwareView();
    if (this._state.tab === "debug") return this._debugView();
    if (this._state.tab === "setup") return this._setupView();
    return this._sendView();
  }

  _navButton(tab, title, subtitle) {
    return `<button class="tab ${this._primaryTab() === tab ? "active" : ""}" data-tab="${this._attr(tab)}"><span>${this._escape(title)}</span><small>${this._escape(subtitle)}</small></button>`;
  }

  _render() {
    this.innerHTML = `<style>
      :host{display:block;min-height:100vh;box-sizing:border-box;color:var(--primary-text-color);background:var(--primary-background-color);padding:16px 24px 32px}
      *{box-sizing:border-box}
      .app-shell{max-width:1220px;margin:0 auto;display:grid;gap:18px}
      .topbar{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:18px;align-items:center;background:transparent;border:0;border-radius:0;padding:4px 0 0;box-shadow:none}
      .brand{display:flex;align-items:center;gap:12px;min-width:0}.logo{width:38px;height:38px;border-radius:10px;object-fit:contain;background:var(--secondary-background-color);border:1px solid var(--divider-color);padding:4px}.brand h1{margin:0;font-size:22px;line-height:1.1}.brand p{margin:4px 0 0;color:var(--secondary-text-color);line-height:1.35}.title-row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.build-chip{display:none}.beta-chip{border:1px solid color-mix(in srgb,var(--primary-color) 42%,var(--divider-color));background:var(--secondary-background-color);color:var(--primary-color);border-radius:999px;padding:4px 8px;font-size:12px;font-weight:800}
      .status-pill{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--divider-color);border-radius:999px;padding:9px 12px;font-weight:900;white-space:nowrap;background:var(--secondary-background-color)}.status-pill.ok{color:#4caf50}.status-pill.warn{color:#ff9800}.status-pill.bad{color:#ff6b6b}.pulse-dot{width:8px;height:8px;border-radius:50%;background:currentColor;box-shadow:0 0 0 4px color-mix(in srgb,currentColor 18%,transparent)}
      .status-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.status-card{border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:20px;padding:16px;min-height:116px;box-shadow:0 5px 18px rgba(0,0,0,.05)}.status-card.ok{border-left:4px solid #4caf50}.status-card.warn{border-left:4px solid #ff9800}.status-card.bad{border-left:4px solid #ff6b6b}.status-card.neutral{border-left:4px solid var(--divider-color)}.status-card-label{color:var(--secondary-text-color);font-size:12px;text-transform:uppercase;letter-spacing:.06em;font-weight:900}.status-card-value{font-size:22px;font-weight:950;margin:8px 0 6px}.status-card-detail{color:var(--secondary-text-color);font-size:13px;line-height:1.35}
      .tabs{display:flex;justify-content:center;align-items:center;gap:34px;border-bottom:1px solid var(--divider-color);margin:0 -24px 8px;padding:0 24px;overflow:auto}.tab,button{font:inherit}.tab{border:0;border-bottom:3px solid transparent;border-radius:0;padding:16px 0 14px;cursor:pointer;background:transparent;color:var(--secondary-text-color);text-align:center;display:flex;align-items:center;gap:8px;min-height:0;box-shadow:none;white-space:nowrap}.tab span{font-weight:750}.tab small{display:none}.tab.active{border-bottom-color:var(--primary-color);background:transparent;color:var(--primary-color);box-shadow:none}.tab:hover{color:var(--primary-text-color);transform:none}
      main{display:block}.grid{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(320px,.8fr);gap:18px;align-items:start}.card,.hero-panel,.service-card{border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:22px;padding:22px;box-shadow:0 8px 22px rgba(0,0,0,.06)}.primary-card{border-top:4px solid var(--primary-color)}.card-kicker,.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--primary-color);font-weight:950;margin-bottom:8px}h2{margin:0 0 14px;font-size:24px;line-height:1.15}h3{margin:0 0 12px;font-size:18px}h4{margin:18px 0 10px}p{color:var(--secondary-text-color);line-height:1.45}.help{color:var(--secondary-text-color)}
      button{border:0;border-radius:12px;padding:11px 16px;font-weight:900;cursor:pointer;background:var(--primary-color);color:var(--text-primary-color,#fff)}button:hover{filter:brightness(.98)}button:disabled{opacity:.55;cursor:not-allowed}.secondary{background:var(--secondary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color)}.tiny{padding:7px 10px;font-size:12px;margin-right:8px}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}
      label{display:block;font-weight:900;margin:14px 0 8px}textarea,input,select{width:100%;background:var(--secondary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color);border-radius:13px;padding:14px;font:inherit}textarea{min-height:108px;font-family:monospace}.row{display:grid;grid-template-columns:1fr 1fr;gap:14px}hr{border:0;border-top:1px solid var(--divider-color);margin:22px 0}.message,.error{border-radius:15px;padding:14px 16px;margin-top:16px;font-weight:900}.message{background:rgba(76,175,80,.16);color:#81c784}.error{background:rgba(244,67,54,.18);color:#ff8a80}.example,.log-line{border:1px solid var(--divider-color);border-radius:13px;padding:12px;margin:10px 0;background:var(--secondary-background-color);font-family:monospace}code,pre{font-family:monospace}pre{white-space:pre-wrap;color:var(--secondary-text-color);margin:8px 0 0}.detail-list p{margin:8px 0}
      .addon-page{display:grid;gap:18px}.addon-card{border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:12px;padding:22px;box-shadow:none}.addon-info-card{padding:0}.addon-header-row{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;padding:22px 22px 0}.addon-header-row h2{font-size:30px;font-weight:500;margin:0 0 8px}.version-line{margin:0;color:var(--secondary-text-color)}.fake-link{color:var(--primary-color)}.connection-mark{font-size:34px;line-height:1;color:#ff5252;font-weight:300}.connection-mark.online{color:#4caf50}.connection-mark.offline{color:#ff5252}.addon-badges{display:flex;flex-wrap:wrap;gap:8px;padding:22px 22px 0}.addon-badge{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:9px 16px;font-size:14px;font-weight:700;color:#fff;background:#0097bd}.addon-badge.rating,.addon-badge.green{background:#43a047}.addon-badge.blue{background:var(--primary-color)}.addon-description{padding:0 22px;margin:20px 0 0;max-width:980px;color:var(--secondary-text-color)}.addon-settings{display:grid;gap:16px;padding:22px}.addon-setting-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:24px;align-items:center;max-width:760px}.addon-setting-row b{display:block;font-size:16px;font-weight:500;color:var(--primary-text-color);margin-bottom:5px}.addon-setting-row span{display:block;color:var(--secondary-text-color);line-height:1.35}.mini-state{border:1px solid var(--divider-color);border-radius:999px;padding:6px 10px;font-size:12px;font-weight:800;background:var(--secondary-background-color);white-space:nowrap}.mini-state.ok{color:#4caf50}.mini-state.warn{color:#ff9800}.mini-state.bad{color:#ff6b6b}.addon-footer-actions{display:flex;align-items:center;gap:14px;border-top:1px solid var(--divider-color);padding:16px 22px;margin-top:10px}.footer-spacer{flex:1}.danger-soft{background:transparent;color:#ff6b7a;border:0}.readme-card{padding:28px}.readme-card h2{font-size:32px;font-weight:800;margin-bottom:18px}.repo-badges{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 24px}.repo-badges span{display:inline-flex;align-items:center;gap:6px;background:#666;color:#fff;border-radius:3px;padding:4px 8px;font-size:13px}.repo-badges b{background:#43a047;margin:-4px -8px -4px 0;padding:4px 7px;border-radius:0 3px 3px 0}.quick-actions-line{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.activity-list{display:grid;gap:10px}.activity-list div{border:1px solid var(--divider-color);background:var(--secondary-background-color);border-radius:14px;padding:12px}.activity-list span{display:block;color:var(--secondary-text-color);font-size:12px;font-weight:900;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}.activity-list code{display:block;white-space:normal;word-break:break-word}.captured-layout{display:grid;gap:18px}      .toggle-row{display:flex;align-items:center;justify-content:space-between;gap:16px;border:1px solid var(--divider-color);background:var(--secondary-background-color);border-radius:16px;padding:16px;margin:12px 0}.toggle-title{font-weight:950}.toggle-help{color:var(--secondary-text-color);font-size:13px;margin-top:4px}.switch{position:relative;display:inline-block;width:54px;height:30px;margin:0;flex:0 0 auto}.switch input{opacity:0;width:0;height:0}.slider{position:absolute;cursor:pointer;inset:0;background:var(--divider-color);transition:.2s;border-radius:999px}.slider:before{position:absolute;content:"";height:22px;width:22px;left:4px;bottom:4px;background:white;transition:.2s;border-radius:50%}.switch input:checked+.slider{background:var(--primary-color)}.switch input:checked+.slider:before{transform:translateX(24px)}
      .hero-card{padding:24px}.hero-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:20px;align-items:start}.stat-row{display:grid;grid-template-columns:repeat(3,minmax(92px,1fr));gap:10px;min-width:330px}.stat{border:1px solid var(--divider-color);border-radius:16px;background:var(--secondary-background-color);padding:12px;text-align:center}.stat b{display:block;font-size:24px;line-height:1.1;color:var(--primary-text-color)}.stat span{display:block;color:var(--secondary-text-color);font-size:12px;margin-top:4px}.captured-columns{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(340px,.85fr);gap:18px;align-items:start}.section-heading{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.entity-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:12px;margin-top:14px}.entity-card{border:1px solid var(--divider-color);border-radius:18px;background:var(--secondary-background-color);padding:15px;display:grid;gap:10px;min-width:0}.entity-card.can-send{border-color:color-mix(in srgb,var(--primary-color) 42%,var(--divider-color));box-shadow:inset 3px 0 0 var(--primary-color)}.entity-card.read-only{opacity:.86}.entity-top{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:start}.entity-title{font-weight:950;font-size:15px;line-height:1.25;word-break:break-word}.entity-id{display:block;margin-top:4px;color:var(--secondary-text-color);white-space:normal;word-break:break-word;font-size:12px}.state-pill{border:1px solid var(--divider-color);border-radius:999px;padding:5px 9px;font-size:12px;color:var(--secondary-text-color);white-space:nowrap;background:var(--card-background-color)}.entity-meta{display:flex;flex-wrap:wrap;gap:7px}.entity-meta span{border:1px solid var(--divider-color);border-radius:999px;padding:5px 8px;font-size:12px;color:var(--secondary-text-color);background:var(--card-background-color)}.device-key{color:var(--secondary-text-color);font-size:12px;word-break:break-word}.command-box{display:grid;gap:8px}.command-row,.candidate-send{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:8px;align-items:center}.command-row code,.raw-block code{display:block;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:10px;padding:8px;white-space:normal;word-break:break-word;font-size:12px}.no-command{color:var(--secondary-text-color);font-size:13px}.raw-panel{position:sticky;top:18px}.raw-card,.alias-card{border:1px solid var(--divider-color);border-radius:18px;background:var(--secondary-background-color);padding:14px;margin:12px 0}.raw-block{margin:8px 0}.label{font-size:12px;font-weight:950;color:var(--secondary-text-color);margin-bottom:6px;text-transform:uppercase;letter-spacing:.04em}.empty-state{border:1px dashed var(--divider-color);border-radius:16px;padding:18px;background:var(--secondary-background-color);display:grid;gap:6px;color:var(--secondary-text-color)}.empty-state b{color:var(--primary-text-color)}.muted-card pre{max-height:180px;overflow:auto}
      @media(max-width:1100px){.grid,.captured-columns{grid-template-columns:1fr}.raw-panel{position:static}.topbar{grid-template-columns:1fr}.top-status{justify-self:start}.tabs{justify-content:flex-start;gap:24px}.addon-setting-row{max-width:none}}
      @media(max-width:720px){:host{padding:14px}.brand{align-items:flex-start}.logo{width:36px;height:36px}.brand h1{font-size:21px}.row,.hero-row{grid-template-columns:1fr}.stat-row{grid-template-columns:repeat(3,1fr);min-width:0;width:100%}.entity-grid{grid-template-columns:1fr}.command-row,.candidate-send{grid-template-columns:1fr}.addon-header-row,.addon-setting-row,.addon-footer-actions{grid-template-columns:1fr;align-items:start}.addon-footer-actions{display:grid}.footer-spacer{display:none}.readme-card h2,.addon-header-row h2{font-size:24px}}
    </style>
    <div class="app-shell">
      <header class="topbar">
        <div class="brand">
          <img class="logo" src="/api/rflink_raw/static/logo.png" alt="RFLink Raw Tools">
          <div>
            <div class="title-row"><h1>RFLink Raw Tools</h1><span class="beta-chip">Beta</span><span class="build-chip">${APP_BUILD_ID}</span></div>
            <p>Home Assistant add-on style RFLink control center with Info, Configuration, and Log tabs.</p>
          </div>
        </div>
        <div class="top-status" id="status-badge">${this._statusBadge()}</div>
      </header>
      <nav class="tabs">
        ${this._navButton("overview", "Info", "")}
        ${this._navButton("configuration", "Configuration", "")}
        ${this._navButton("log", "Log", "")}
      </nav>
      <main id="body"></main>
    </div>`;
    this._bind();
    this._update();
  }

  _bind() {
    this.querySelectorAll("[data-tab]").forEach(b => b.addEventListener("click", () => this._setTab(b.dataset.tab)));
  }

  _updateStatusBadge() {
    const badge = this.querySelector("#status-badge");
    if (badge) badge.innerHTML = this._statusBadge();
  }

  _updateStatusCards() {
    const cards = this.querySelector("#status-cards");
    if (cards) cards.innerHTML = this._statusCards();
  }

  _updateTabs() {
    this.querySelectorAll("[data-tab]").forEach(b => b.classList.toggle("active", b.dataset.tab === this._primaryTab()));
  }

  _update() {
    if (!this._rendered) return;
    this._updateTabs();
    this._updateStatusBadge();
    this._updateStatusCards();
    const body = this.querySelector("#body");
    if (!body) return;
    body.innerHTML = this._body();
    body.querySelectorAll("[data-action]").forEach(el => el.addEventListener("click", () => this[el.dataset.action] && this[el.dataset.action]()));
    body.querySelectorAll("[data-tablink]").forEach(el => el.addEventListener("click", () => this._setTab(el.dataset.tablink)));
    body.querySelectorAll("[data-copy-command]").forEach(el => el.addEventListener("click", () => this._copyCommand(el.dataset.copyCommand)));
    body.querySelectorAll("[data-field]").forEach(el => el.addEventListener("input", e => this._input(el.dataset.field, el.type === "number" ? Number(e.target.value) : e.target.value)));
    body.querySelectorAll("[data-toggle-debug]").forEach(el => el.addEventListener("change", e => this._setDebug(el.dataset.toggleDebug, Boolean(e.target.checked))));
    body.querySelectorAll("[data-teach-field]").forEach(el => el.addEventListener("input", e => this._setTeachField(el.dataset.teachField, e.target.value)));
    body.querySelectorAll("select[data-teach-field]").forEach(el => el.addEventListener("change", e => this._setTeachField(el.dataset.teachField, e.target.value)));
    body.querySelectorAll("[data-teach-entity]").forEach(el => el.addEventListener("click", () => this._teachFromEntity(el.dataset.teachEntity)));
    body.querySelectorAll("[data-teach-log]").forEach(el => el.addEventListener("click", () => this._teachFromLog(el.dataset.teachLog)));
    body.querySelectorAll("[data-delete-alias]").forEach(el => el.addEventListener("click", () => this._deleteAlias(el.dataset.deleteAlias)));
    body.querySelectorAll("[data-edit-alias]").forEach(el => el.addEventListener("click", () => this._editAlias(el.dataset.editAlias)));
    body.querySelectorAll("[data-alias-test]").forEach(el => el.addEventListener("click", () => this._testAliasCommand(el.dataset.aliasTest)));
    body.querySelectorAll("[data-lab-field]").forEach(el => el.addEventListener("input", e => this._setLabField(el.dataset.labField, e.target.value)));
    body.querySelectorAll("[data-firmware-field]").forEach(el => el.addEventListener("input", e => this._setFirmwareField(el.dataset.firmwareField, e.target.value)));
    body.querySelectorAll("[data-delete-firmware-capture]").forEach(el => el.addEventListener("click", () => this._deleteFirmwareCapture(el.dataset.deleteFirmwareCapture)));
  }
}

customElements.define("rflink-raw-tools-panel", RFLinkRawToolsPanel);
