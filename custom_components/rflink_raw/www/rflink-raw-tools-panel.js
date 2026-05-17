const APP_BUILD_ID = "v002-addon-controls-20260517";

class RFLinkRawToolsPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._rendered = false;
    this._timer = null;
    this._state = {
      tab: localStorage.getItem("rflink_raw_tools.tab") || "info",
      tool: localStorage.getItem("rflink_raw_tools.tool") || "send",
      busy: false,
      message: "",
      error: "",
      status: { readiness: "checking", readiness_detail: "Loading status…", options: {} },
      rawCommand: localStorage.getItem("rflink_raw_tools.rawCommand") || "",
      repeat: Number(localStorage.getItem("rflink_raw_tools.repeat") || 1),
      delayMs: Number(localStorage.getItem("rflink_raw_tools.delayMs") || 250),
      port: localStorage.getItem("rflink_raw_tools.port") || "/dev/ttyUSB0",
      logs: [],
      entities: [],
      aliases: [],
      teach: { id: "", name: "", entity_type: "switch", device_id: "", on_command: "", off_command: "", source_packet: "", notes: "" },
    };
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

  _escape(v) {
    return String(v ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;");
  }
  _attr(v) { return this._escape(v); }
  _options() { return (this._state.status && this._state.status.options) || {}; }
  _on(v) { return Boolean(v); }
  _debugEnabled(id) { return Boolean(this._state.status && this._state.status[id]); }
  _formatError(e) { return e && (e.message || e.error) ? (e.message || e.error) : String(e || "Unknown error"); }
  _feedback() { return `${this._state.message ? `<div class="message">${this._escape(this._state.message)}</div>` : ""}${this._state.error ? `<div class="error">${this._escape(this._state.error)}</div>` : ""}`; }

  async _loadAll(render = true) {
    await this._loadStatus(false);
    if (this._state.tab === "log") await this._loadLogs(false);
    if (this._state.tool === "captured") await this._loadCaptured(false);
    if (this._state.tool === "teach") await this._loadAliases(false);
    if (render) this._update();
  }

  async _loadStatus(render = true) {
    if (!this._hass) return;
    try {
      this._state.status = await this._hass.callApi("GET", "rflink_raw/status");
      this._state.error = "";
    } catch (e) {
      this._state.status = { readiness: "status_api_unavailable", readiness_detail: `Status API unavailable: ${this._formatError(e)}`, options: {} };
    }
    if (render) this._update();
  }

  async _loadLogs(render = true) {
    try {
      const data = await this._hass.callApi("GET", "rflink_raw/logs");
      this._state.logs = data.lines || [];
    } catch (e) { this._state.error = `Could not load logs: ${this._formatError(e)}`; }
    if (render) this._update();
  }

  async _loadCaptured(render = true) {
    try {
      const [entities, logs] = await Promise.all([this._hass.callApi("GET", "rflink_raw/entities"), this._hass.callApi("GET", "rflink_raw/logs")]);
      this._state.entities = entities.entities || [];
      this._state.logs = logs.lines || [];
    } catch (e) { this._state.error = `Could not load captured data: ${this._formatError(e)}`; }
    if (render) this._update();
  }

  async _loadAliases(render = true) {
    try {
      const data = await this._hass.callApi("GET", "rflink_raw/aliases");
      this._state.aliases = data.aliases || [];
    } catch (e) { this._state.error = `Could not load aliases: ${this._formatError(e)}`; }
    if (render) this._update();
  }

  async _callService(domain, service, data = {}, success = "Done.") {
    this._state.busy = true; this._state.message = ""; this._state.error = ""; this._update();
    try {
      await this._hass.callService(domain, service, data);
      this._state.message = success;
      await this._loadAll(false);
    } catch (e) { this._state.error = this._formatError(e); }
    finally { this._state.busy = false; this._update(); }
  }

  async _postOptions(data, success = "Configuration updated.") {
    this._state.busy = true; this._state.message = ""; this._state.error = ""; this._update();
    try {
      const res = await this._hass.callApi("POST", "rflink_raw/options", data);
      this._state.status.options = res.options || this._state.status.options || {};
      this._state.message = (res.result && res.result.message) || success;
      await this._loadStatus(false);
    } catch (e) { this._state.error = this._formatError(e); }
    finally { this._state.busy = false; this._update(); }
  }

  _setTab(tab) { this._state.tab = tab; localStorage.setItem("rflink_raw_tools.tab", tab); this._state.message = ""; this._state.error = ""; this._update(); if (tab === "log") this._loadLogs(); }
  _setTool(tool) { this._state.tool = tool; localStorage.setItem("rflink_raw_tools.tool", tool); this._state.message = ""; this._state.error = ""; this._update(); if (tool === "captured") this._loadCaptured(); if (tool === "teach") this._loadAliases(); }
  _input(field, value) { this._state[field] = value; }
  _teach(field, value) { this._state.teach = { ...(this._state.teach || {}), [field]: value }; }

  async _sendRaw() {
    const raw = String(this._state.rawCommand || "").trim();
    if (!raw) { this._state.error = "Paste a learned RFLink command first."; this._update(); return; }
    localStorage.setItem("rflink_raw_tools.rawCommand", raw);
    localStorage.setItem("rflink_raw_tools.repeat", String(this._state.repeat || 1));
    localStorage.setItem("rflink_raw_tools.delayMs", String(this._state.delayMs || 250));
    await this._callService("rflink_raw", "send_raw", { raw_command: raw, repeat: Number(this._state.repeat || 1), delay_ms: Number(this._state.delayMs || 250) }, "RFLink command sent.");
  }

  _copyCommand(cmd) { this._state.rawCommand = cmd || ""; this._setTool("send"); this._state.message = "Command copied to Send."; }
  _clearRawCommand() { this._state.rawCommand = ""; localStorage.removeItem("rflink_raw_tools.rawCommand"); this._state.message = "Raw command cleared."; this._update(); }
  _checkSetup() { return this._callService("rflink_raw", "ping_gateway", {}, "RFLink setup check complete."); }
  _clearStatus() { return this._callService("rflink_raw", "clear_status", {}, "Status cleared."); }
  _installYaml() { localStorage.setItem("rflink_raw_tools.port", this._state.port || "/dev/ttyUSB0"); return this._callService("rflink_raw", "install_rflink_yaml", { port: this._state.port || "/dev/ttyUSB0" }, "RFLink YAML install check complete."); }
  _removeYaml() { if (!confirm("Remove the RFLink YAML block created by RFLink Raw Tools? A backup will be created. User-managed RFLink YAML will not be removed.")) return; return this._callService("rflink_raw", "remove_rflink_yaml", {}, "RFLink YAML removal check complete."); }
  _setDebug(id, enabled) { return this._callService("rflink_raw", "set_debug", { debug_type: id, enabled: Boolean(enabled) }, `${id === "qrfdebug" ? "Raw RF capture logging" : "Decoded RFLink logging"} ${enabled ? "enabled" : "disabled"}.`); }
  _toggleOption(key, value) { return this._postOptions({ [key]: Boolean(value) }); }
  _installHomeCard() { return this._postOptions({ action: "install_home_card" }); }
  _removeHomeCard() { return this._postOptions({ action: "remove_home_card" }); }

  async _saveAlias() {
    const t = this._state.teach || {};
    if (!t.name || !t.device_id) { this._state.error = "Alias needs a friendly name and RFLink device id."; this._update(); return; }
    this._state.busy = true; this._state.error = ""; this._state.message = ""; this._update();
    try {
      const data = await this._hass.callApi("POST", "rflink_raw/aliases", t);
      this._state.aliases = data.aliases || [];
      this._state.teach = { id: "", name: "", entity_type: "switch", device_id: "", on_command: "", off_command: "", source_packet: "", notes: "" };
      this._state.message = "Alias saved. If alias switches are enabled, it will appear as a Home Assistant switch after refresh/restart."
    } catch (e) { this._state.error = this._formatError(e); }
    finally { this._state.busy = false; this._update(); }
  }

  _statusLabel() {
    const s = this._state.status || {};
    if (s.readiness === "ready") return "RFLink ready";
    if (s.readiness === "loaded") return "RFLink loaded";
    if (s.readiness === "configured_needs_restart") return "Restart needed";
    if (s.readiness === "not_configured") return "RFLink not configured";
    if (s.readiness === "status_api_unavailable") return "Status unavailable";
    return "Checking status…";
  }
  _tone() { const r = (this._state.status || {}).readiness; return (r === "ready" || r === "loaded") ? "ok" : (r === "not_configured" ? "bad" : "warn"); }

  _miniState(text, on) { return `<span class="mini-state ${on ? "ok" : "warn"}">${this._escape(text)}</span>`; }
  _toggleRow(title, text, key, enabled) { return `<div class="setting-row"><div><b>${this._escape(title)}</b><span>${text}</span></div><label class="switch"><input type="checkbox" data-option-toggle="${this._attr(key)}" ${enabled ? "checked" : ""}><span class="slider"></span></label></div>`; }

  _infoView() {
    const s = this._state.status || {}; const o = this._options();
    return `<section class="addon-card info-card">
      <div class="addon-head"><div><h2>RFLink Raw Tools (Beta)</h2><p>Current version: ${this._escape(s.version || "0.0.2")} <span class="linkish">(${APP_BUILD_ID})</span></p></div><div class="connection ${this._tone()}">${this._tone() === "ok" ? "●" : "⊘"}</div></div>
      <div class="badges"><span class="badge green">RF</span><span class="badge blue">Home Assistant</span><span class="badge blue">RFLink</span><span class="badge green">Switches</span><span class="badge blue">Capture</span></div>
      <p class="desc">A Home Assistant sidebar app for RFLink setup, RF capture, learned command sending, friendly aliases, and unsupported-remote evidence.</p>
      <p class="desc"><b>Status:</b> ${this._escape(s.readiness_detail || "Loading status…")}</p>
      <div class="settings-list">
        <div class="setting-row"><div><b>RFLink YAML</b><span>${s.rflink_configured ? "Configured. Configuration can install or remove the RFLink Raw Tools managed block." : "Not configured. Configuration can add a conservative top-level rflink: block."}</span></div>${this._miniState(s.rflink_configured ? "Configured" : "Missing", s.rflink_configured)}</div>
        <div class="setting-row"><div><b>Home Assistant RFLink bridge</b><span>${s.rflink_loaded ? "Loaded" : "Not loaded"} / ${s.rflink_connected ? "Connected" : "Loaded"}.</span></div>${this._miniState(s.rflink_loaded ? "Loaded" : "Not loaded", s.rflink_loaded)}</div>
        <div class="setting-row"><div><b>Alias-backed HA switches</b><span>Teach/Alias records with ON and OFF commands can appear as Home Assistant switches.</span></div>${this._miniState(o.alias_switches_enabled ? "Enabled" : "Disabled", o.alias_switches_enabled)}</div>
        <div class="setting-row"><div><b>Sidebar app</b><span>Controls whether RFLink Raw Tools appears in the left sidebar.</span></div>${this._miniState(o.sidebar_enabled ? "Shown" : "Hidden", o.sidebar_enabled)}</div>
        <div class="setting-row"><div><b>Home screen card</b><span>Reusable Lovelace card snippet for opening RFLink Raw Tools.</span></div>${this._miniState(o.home_card_installed ? "Installed" : "Not installed", o.home_card_installed)}</div>
      </div>
      <div class="footer-actions"><button data-tablink="configuration">Configuration</button><button class="secondary" data-tool="send">Send</button><button class="secondary" data-tool="captured">Captured</button><button class="secondary" data-tool="teach">Teach</button><button class="secondary" data-tablink="log">Log</button></div>
      ${this._feedback()}
    </section>
    <section class="addon-card tools-card"><h2>RFLink Tools</h2><div class="tool-tabs"><button class="tool ${this._state.tool === "send" ? "active" : ""}" data-tool="send">Send</button><button class="tool ${this._state.tool === "captured" ? "active" : ""}" data-tool="captured">Captured</button><button class="tool ${this._state.tool === "teach" ? "active" : ""}" data-tool="teach">Teach Alias</button></div>${this._toolView()}</section>`;
  }

  _configurationView() {
    const s = this._state.status || {}; const o = this._options();
    return `<section class="addon-card"><h2>Configuration</h2><p class="desc">These are the switches and maintenance actions for RFLink YAML, sidebar placement, Home screen card, and alias-backed Home Assistant switches.</p>
      <div class="config-grid">
        <div class="config-box"><h3>RFLink YAML</h3><p>${s.rflink_configured ? "RFLink is configured." : "RFLink is not configured."}</p><label>Serial port</label><input data-field="port" value="${this._attr(this._state.port)}"><div class="actions"><button data-action="_installYaml">Install / repair RFLink YAML</button><button class="danger" data-action="_removeYaml">Remove RFLink YAML</button></div><p class="note">Remove only deletes the block created by RFLink Raw Tools. It refuses to delete user-managed YAML.</p></div>
        <div class="config-box"><h3>App placement</h3>${this._toggleRow("Show in left sidebar", "Turn off only if you plan to open /rflink-raw-tools directly.", "sidebar_enabled", o.sidebar_enabled)}<div class="setting-row"><div><b>Home screen card</b><span>Writes or removes /config/rflink_raw_home_card.yaml. Add it to a dashboard manually if wanted.</span></div><div class="inline-actions"><button class="secondary" data-action="_installHomeCard">Install</button><button class="secondary" data-action="_removeHomeCard">Remove</button></div></div></div>
        <div class="config-box"><h3>Home Assistant entities</h3>${this._toggleRow("Expose aliases as HA switches", "Aliases with ON/OFF commands become optimistic Home Assistant switch entities.", "alias_switches_enabled", o.alias_switches_enabled)}<p class="note">After enabling or creating aliases, restart Home Assistant if entities do not appear immediately.</p></div>
        <div class="config-box"><h3>Maintenance</h3><div class="actions"><button class="secondary" data-action="_checkSetup">Check setup</button><button class="secondary" data-action="_clearStatus">Clear status</button></div><p class="note">HACS/GitHub releases handle app updates. There is no self-updater in the integration.</p></div>
      </div>${this._feedback()}</section>`;
  }

  _logView() {
    const rows = (this._state.logs || []).slice().reverse().slice(0, 80).map(i => `<div class="log-row">${i.raw_packet ? `<code>${this._escape(i.raw_packet)}</code>` : ""}${i.send_candidate ? `<button class="tiny" data-copy-command="${this._attr(i.send_candidate)}">Copy</button>` : ""}<pre>${this._escape(i.line || "")}</pre></div>`).join("");
    return `<section class="addon-card"><h2>Log</h2><p class="desc">Logging controls are here, separate from setup actions.</p>
      <div class="settings-list">
        <div class="setting-row"><div><b>Raw RF capture logging</b><span>Enable this, press the physical remote, then open Captured.</span></div><label class="switch"><input type="checkbox" data-debug-toggle="qrfdebug" ${this._debugEnabled("qrfdebug") ? "checked" : ""}><span class="slider"></span></label></div>
        <div class="setting-row"><div><b>Decoded RFLink logging</b><span>Useful for readable protocol messages in Home Assistant logs.</span></div><label class="switch"><input type="checkbox" data-debug-toggle="rfdebug" ${this._debugEnabled("rfdebug") ? "checked" : ""}><span class="slider"></span></label></div>
      </div>
      <div class="actions"><button data-action="_loadLogs">Refresh log lines</button><button class="secondary" data-action="_clearStatus">Clear status</button></div>${this._feedback()}<div class="log-list">${rows || `<div class="empty">No RFLink log lines found yet.</div>`}</div></section>`;
  }

  _toolView() {
    if (this._state.tool === "captured") return this._capturedTool();
    if (this._state.tool === "teach") return this._teachTool();
    return this._sendTool();
  }

  _sendTool() {
    return `<div class="tool-body"><label>RFLink command</label><textarea data-field="rawCommand" placeholder="newkaku_0000c6c2_1;on">${this._escape(this._state.rawCommand)}</textarea><div class="row"><div><label>Repeat</label><input data-field="repeat" type="number" min="1" value="${this._attr(this._state.repeat)}"></div><div><label>Delay between repeats (ms)</label><input data-field="delayMs" type="number" min="0" value="${this._attr(this._state.delayMs)}"></div></div><div class="actions"><button data-action="_sendRaw">Send command</button><button class="secondary" data-action="_clearRawCommand">Clear</button></div></div>`;
  }

  _capturedTool() {
    const entities = (this._state.entities || []).map((i, idx) => `<div class="entity-card"><b>${this._escape(i.name || i.entity_id)}</b><code>${this._escape(i.entity_id)}</code><p>${this._escape(i.protocol || "")}${i.address ? ` / ${this._escape(i.address)}` : ""}</p>${i.candidate_on ? `<div class="command-line"><code>${this._escape(i.candidate_on)}</code><button class="tiny" data-copy-command="${this._attr(i.candidate_on)}">Copy ON</button></div>` : ""}${i.candidate_off ? `<div class="command-line"><code>${this._escape(i.candidate_off)}</code><button class="tiny" data-copy-command="${this._attr(i.candidate_off)}">Copy OFF</button></div>` : ""}${i.send_device_id ? `<button class="secondary tiny" data-teach-from-entity="${idx}">Teach as switch</button>` : ""}</div>`).join("");
    const packets = (this._state.logs || []).filter(i => i.raw_packet || i.send_candidate).slice().reverse().slice(0, 20).map(i => `<div class="entity-card"><code>${this._escape(i.raw_packet || i.send_candidate)}</code>${i.send_candidate ? `<button class="tiny" data-copy-command="${this._attr(i.send_candidate)}">Copy candidate</button>` : ""}</div>`).join("");
    return `<div class="tool-body"><div class="actions"><button data-action="_loadCaptured">Refresh captured data</button><button class="secondary" data-tablink="log">Open Log</button></div><div class="captured-grid"><div><h3>Discovered entities</h3>${entities || `<div class="empty">No RFLink entities found.</div>`}</div><div><h3>Raw packets</h3>${packets || `<div class="empty">No raw packets found. Turn on Raw RF capture logging, press the remote, then refresh.</div>`}</div></div></div>`;
  }

  _teachTool() {
    const t = this._state.teach || {};
    const aliases = (this._state.aliases || []).map(a => `<div class="entity-card"><b>${this._escape(a.name)}</b><code>${this._escape(a.device_id)}</code><p>${this._escape(a.entity_type)}</p>${a.on_command ? `<div class="command-line"><code>${this._escape(a.on_command)}</code><button class="tiny" data-copy-command="${this._attr(a.on_command)}">Copy ON</button></div>` : ""}${a.off_command ? `<div class="command-line"><code>${this._escape(a.off_command)}</code><button class="tiny" data-copy-command="${this._attr(a.off_command)}">Copy OFF</button></div>` : ""}</div>`).join("");
    return `<div class="tool-body"><div class="captured-grid"><div><h3>Alias editor</h3><label>Friendly name</label><input data-teach-field="name" value="${this._attr(t.name || "")}" placeholder="Bedroom AC"><label>Type</label><select data-teach-field="entity_type"><option value="switch" ${(t.entity_type || "switch") === "switch" ? "selected" : ""}>switch</option><option value="light" ${t.entity_type === "light" ? "selected" : ""}>light-style switch</option><option value="button" ${t.entity_type === "button" ? "selected" : ""}>button</option></select><label>RFLink device id</label><input data-teach-field="device_id" value="${this._attr(t.device_id || "")}" placeholder="newkaku_0000c6c2_1"><label>ON command</label><input data-teach-field="on_command" value="${this._attr(t.on_command || "")}" placeholder="newkaku_0000c6c2_1;on"><label>OFF command</label><input data-teach-field="off_command" value="${this._attr(t.off_command || "")}" placeholder="newkaku_0000c6c2_1;off"><label>Notes / source packet</label><textarea data-teach-field="source_packet">${this._escape(t.source_packet || "")}</textarea><div class="actions"><button data-action="_saveAlias">Save alias</button></div></div><div><h3>Saved aliases</h3>${aliases || `<div class="empty">No aliases saved yet.</div>`}</div></div></div>`;
  }

  _body() { if (this._state.tab === "configuration") return this._configurationView(); if (this._state.tab === "log") return this._logView(); return this._infoView(); }

  _render() {
    this.innerHTML = `<style>
      :host{display:block;min-height:100vh;padding:16px 24px 32px;background:var(--primary-background-color);color:var(--primary-text-color);box-sizing:border-box}*{box-sizing:border-box}.shell{max-width:1180px;margin:0 auto}.topbar{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:12px}.brand{display:flex;align-items:center;gap:12px}.logo{width:38px;height:38px;border-radius:10px;border:1px solid var(--divider-color);background:var(--secondary-background-color);padding:4px}.brand h1{font-size:22px;margin:0}.brand p{margin:3px 0 0;color:var(--secondary-text-color)}.status-pill{border:1px solid var(--divider-color);border-radius:999px;background:var(--secondary-background-color);padding:8px 12px;font-weight:800}.status-pill.ok{color:#4caf50}.status-pill.warn{color:#ff9800}.status-pill.bad{color:#ff6b6b}.tabs{display:flex;justify-content:center;gap:46px;border-bottom:1px solid var(--divider-color);margin:0 -24px 20px;padding:0 24px;overflow:auto}.tab{border:0;border-bottom:3px solid transparent;background:transparent;color:var(--secondary-text-color);padding:16px 0 14px;border-radius:0;font-weight:700;cursor:pointer}.tab.active{color:var(--primary-color);border-bottom-color:var(--primary-color)}.addon-card{border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:12px;padding:0;margin-bottom:18px}.addon-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;padding:22px 22px 0}.addon-head h2{font-size:30px;font-weight:500;margin:0 0 8px}.addon-head p{margin:0;color:var(--secondary-text-color)}.connection{font-size:34px;line-height:1}.connection.ok{color:#4caf50}.connection.warn,.connection.bad{color:#ff5252}.badges{display:flex;gap:8px;flex-wrap:wrap;padding:22px 22px 0}.badge{color:#fff;border-radius:999px;padding:8px 14px;font-weight:700}.badge.green{background:#43a047}.badge.blue{background:var(--primary-color)}.desc{padding:0 22px;color:var(--secondary-text-color);line-height:1.45}.settings-list{display:grid;gap:16px;padding:22px}.setting-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:24px;align-items:center;max-width:850px}.setting-row b{display:block;font-weight:550;margin-bottom:5px}.setting-row span{display:block;color:var(--secondary-text-color);line-height:1.35}.mini-state{border:1px solid var(--divider-color);border-radius:999px;background:var(--secondary-background-color);padding:6px 10px;font-size:12px;font-weight:800;white-space:nowrap}.mini-state.ok{color:#4caf50}.mini-state.warn{color:#ff9800}.footer-actions{display:flex;gap:12px;flex-wrap:wrap;border-top:1px solid var(--divider-color);padding:16px 22px}.tools-card{padding:22px}.tools-card h2{margin-top:0}button{border:0;border-radius:12px;padding:10px 15px;font-weight:800;cursor:pointer;background:var(--primary-color);color:var(--text-primary-color,#fff)}.secondary{background:var(--secondary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color)}.danger{background:#b3261e;color:#fff}.tiny{font-size:12px;padding:6px 9px}.message,.error{border-radius:14px;padding:13px 15px;margin:16px 22px;font-weight:800}.message{background:rgba(76,175,80,.16);color:#81c784}.error{background:rgba(244,67,54,.18);color:#ff8a80}.config-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:22px}.config-box{border:1px solid var(--divider-color);background:var(--secondary-background-color);border-radius:14px;padding:16px}.config-box h3{margin-top:0}.note{font-size:13px;color:var(--secondary-text-color)}.actions,.inline-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}label{display:block;font-weight:800;margin:12px 0 7px}input,textarea,select{width:100%;border:1px solid var(--divider-color);background:var(--secondary-background-color);color:var(--primary-text-color);border-radius:12px;padding:12px;font:inherit}textarea{min-height:96px;font-family:monospace}.switch{position:relative;display:inline-block;width:54px;height:30px;margin:0}.switch input{opacity:0;width:0;height:0}.slider{position:absolute;cursor:pointer;inset:0;background:var(--divider-color);transition:.2s;border-radius:999px}.slider:before{position:absolute;content:"";height:22px;width:22px;left:4px;bottom:4px;background:#fff;transition:.2s;border-radius:50%}.switch input:checked+.slider{background:var(--primary-color)}.switch input:checked+.slider:before{transform:translateX(24px)}.tool-tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}.tool{background:var(--secondary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color)}.tool.active{background:var(--primary-color);color:var(--text-primary-color,#fff)}.row,.captured-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.entity-card,.log-row,.empty{border:1px solid var(--divider-color);background:var(--secondary-background-color);border-radius:14px;padding:12px;margin:10px 0}.entity-card code,.command-line code,.log-row code{display:block;word-break:break-word;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:9px;padding:7px;margin:6px 0}pre{white-space:pre-wrap;color:var(--secondary-text-color);font-family:monospace}.log-list{padding:0 22px 22px}.linkish{color:var(--primary-color)}@media(max-width:850px){:host{padding:14px}.topbar{align-items:flex-start;flex-direction:column}.tabs{justify-content:flex-start;gap:28px}.config-grid,.row,.captured-grid{grid-template-columns:1fr}.setting-row{grid-template-columns:1fr;gap:10px}.addon-head{display:block}.connection{margin-top:12px}}
    </style><div class="shell"><header class="topbar"><div class="brand"><img class="logo" src="/api/rflink_raw/static/logo.png" alt="RFLink Raw Tools"><div><h1>RFLink Raw Tools</h1><p>Setup, capture, aliases, and RFLink switch controls.</p></div></div><div id="status-badge">${this._statusBadge()}</div></header><nav class="tabs"><button class="tab ${this._state.tab === "info" ? "active" : ""}" data-tab="info">Info</button><button class="tab ${this._state.tab === "configuration" ? "active" : ""}" data-tab="configuration">Configuration</button><button class="tab ${this._state.tab === "log" ? "active" : ""}" data-tab="log">Log</button></nav><main id="body"></main></div>`;
    this._bind(); this._update();
  }

  _statusBadge() { return `<span class="status-pill ${this._tone()}">${this._escape(this._statusLabel())}</span>`; }
  _bind() { this.querySelectorAll("[data-tab]").forEach(b => b.addEventListener("click", () => this._setTab(b.dataset.tab))); }
  _updateTabs() { this.querySelectorAll("[data-tab]").forEach(b => b.classList.toggle("active", b.dataset.tab === this._state.tab)); const badge = this.querySelector("#status-badge"); if (badge) badge.innerHTML = this._statusBadge(); }
  _update() {
    if (!this._rendered) return;
    this._updateTabs();
    const body = this.querySelector("#body"); if (!body) return;
    body.innerHTML = this._body();
    body.querySelectorAll("[data-tablink]").forEach(el => el.addEventListener("click", () => this._setTab(el.dataset.tablink)));
    body.querySelectorAll("[data-tool]").forEach(el => el.addEventListener("click", () => this._setTool(el.dataset.tool)));
    body.querySelectorAll("[data-action]").forEach(el => el.addEventListener("click", () => this[el.dataset.action] && this[el.dataset.action]()));
    body.querySelectorAll("[data-field]").forEach(el => el.addEventListener("input", e => this._input(el.dataset.field, el.type === "number" ? Number(e.target.value) : e.target.value)));
    body.querySelectorAll("[data-teach-field]").forEach(el => el.addEventListener("input", e => this._teach(el.dataset.teachField, e.target.value)));
    body.querySelectorAll("select[data-teach-field]").forEach(el => el.addEventListener("change", e => this._teach(el.dataset.teachField, e.target.value)));
    body.querySelectorAll("[data-copy-command]").forEach(el => el.addEventListener("click", () => this._copyCommand(el.dataset.copyCommand)));
    body.querySelectorAll("[data-debug-toggle]").forEach(el => el.addEventListener("change", e => this._setDebug(el.dataset.debugToggle, e.target.checked)));
    body.querySelectorAll("[data-option-toggle]").forEach(el => el.addEventListener("change", e => this._toggleOption(el.dataset.optionToggle, e.target.checked)));
    body.querySelectorAll("[data-teach-from-entity]").forEach(el => el.addEventListener("click", () => {
      const i = (this._state.entities || [])[Number(el.dataset.teachFromEntity)]; if (!i) return;
      this._state.teach = { id: "", name: i.name || i.device_key || "", entity_type: "switch", device_id: i.send_device_id || "", on_command: i.candidate_on || "", off_command: i.candidate_off || "", source_packet: `Created from ${i.entity_id}`, notes: "" };
      this._setTool("teach");
    }));
  }
}

customElements.define("rflink-raw-tools-panel", RFLinkRawToolsPanel);
