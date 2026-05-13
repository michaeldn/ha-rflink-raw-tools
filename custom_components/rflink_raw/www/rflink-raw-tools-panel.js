
const APP_BUILD_ID = "safe-loader-fix-20260512";
class RFLinkRawToolsPanel extends HTMLElement {
  constructor(){super();this._hass=null;this._timer=null;this._autoClearedUnknown=false;this._state={tab:localStorage.getItem("rflink_raw_tools.tab")||"send",busy:false,message:"",error:"",rawCommand:this._migrateOldSavedCommand(),repeat:Number(localStorage.getItem("rflink_raw_tools.repeat")||1),delayMs:Number(localStorage.getItem("rflink_raw_tools.delayMs")||250),port:localStorage.getItem("rflink_raw_tools.port")||"/dev/ttyUSB0",status:{readiness:"checking",readiness_detail:"Loading status…",rfdebug:false,qrfdebug:false},entities:[],logs:[],aliases:[],teach:{id:'',name:'',entity_type:'switch',device_id:'',on_command:'',off_command:'',source_packet:'',notes:''},firmwareLab:{project_name:'Digiten remote',notes:'',active:false,captures:[]},firmwareButtonLabel:'Digiten ON',firmwareButtonNotes:'',firmwareReport:''};}
  set hass(hass){this._hass=hass;if(!this._rendered){this._render();this._rendered=true;}this._loadAll();}
  connectedCallback(){if(this._timer)return;this._timer=window.setInterval(()=>this._loadAll(false),12000);}
  disconnectedCallback(){if(this._timer)window.clearInterval(this._timer);this._timer=null;}
  _formatError(e){if(!e)return"Unknown error";if(typeof e==="string")return e;return e.message||e.error||JSON.stringify(e);}
  _isUnknownCommandText(v){const t=String(v||"").trim();return t==="Unknown command";}
  _safeError(e){const m=this._formatError(e);return this._isUnknownCommandText(m)?"RFLink rejected that command. Use a real learned device command, not a placeholder/example.":m;}
  _sanitizeStatus(s){const c={...(s||{})};if(this._isUnknownCommandText(c.last_error))c.last_error="";if(this._isUnknownCommandText(c.last_result))c.last_result="";return c;}
  async _autoClearStaleUnknown(s){if(!s||this._autoClearedUnknown)return;if(this._isUnknownCommandText(s.last_error)||this._isUnknownCommandText(s.last_result)){this._autoClearedUnknown=true;try{await this._hass.callService("rflink_raw","clear_status",{});}catch(e){}}}
  _normalizeRawCommand(raw){return String(raw||"").trim().replace(/;+$/g,"").toUpperCase();}
  _rawCommandKind(raw){const n=this._normalizeRawCommand(raw);if(n==="10;PING"||n==="PING")return"status";if(n==="10;VERSION"||n==="VERSION")return"version";return"device";}
  _migrateOldSavedCommand(){const s=localStorage.getItem("rflink_raw_tools.rawCommand");const k=this._rawCommandKind(s);if(k==="status"||k==="version"){localStorage.removeItem("rflink_raw_tools.rawCommand");return"";}return s||"";}
  _debugLocalKey(t){return`rflink_raw_tools.${t}`;}
  _debugEnabled(t){const l=localStorage.getItem(this._debugLocalKey(t));if(l==="true")return true;if(l==="false")return false;return Boolean(this._state.status&&this._state.status[t]);}
  async _loadAll(render=true){await this._loadStatus(render);if(this._state.tab==="captured")await this._loadCaptured(false);if(this._state.tab==="teach")await this._loadAliases(false);if(this._state.tab==="firmware")await this._loadFirmwareLab(false);}
  async _loadStatus(render=true){if(!this._hass)return;try{const raw=await this._hass.callApi("GET","rflink_raw/status");await this._autoClearStaleUnknown(raw);this._state.status=this._sanitizeStatus(raw);if(!this._state.busy)this._state.error="";if(render)this._update();}catch(e){this._state.status={readiness:"status_api_unavailable",readiness_detail:`Status API unavailable: ${this._safeError(e)}`,rflink_configured:false,rflink_loaded:false,rflink_connected:false,last_error:"",last_result:"",last_command:"",last_updated:"",rfdebug:this._debugEnabled("rfdebug"),qrfdebug:this._debugEnabled("qrfdebug")};this._state.error="";if(render)this._update();}}
  async _loadCaptured(render=true){if(!this._hass)return;try{const [entities,logs]=await Promise.all([this._hass.callApi("GET","rflink_raw/entities"),this._hass.callApi("GET","rflink_raw/logs")]);this._state.entities=entities.entities||[];this._state.logs=logs.lines||[];this._state.error="";}catch(e){this._state.error=`Could not load captured data: ${this._safeError(e)}`;}if(render)this._update();}
  async _loadAliases(render=true){if(!this._hass)return;try{const data=await this._hass.callApi("GET","rflink_raw/aliases");this._state.aliases=data.aliases||[];}catch(e){this._state.error=`Could not load aliases: ${this._safeError(e)}`;}if(render)this._update();}
  async _loadFirmwareLab(render=true){if(!this._hass)return;try{const data=await this._hass.callApi("GET","rflink_raw/firmware_lab");this._state.firmwareLab=data.lab||{};this._state.firmwareReport=data.report||"";}catch(e){this._state.error=`Could not load Firmware Lab: ${this._safeError(e)}`;}if(render)this._update();}
  async _callService(domain,service,data={},success="Done."){this._state.busy=true;this._state.error="";this._state.message="";this._update();try{await this._hass.callService(domain,service,data);this._state.message=success;await this._loadStatus(false);}catch(e){this._state.message="";this._state.error=this._safeError(e);}finally{this._state.busy=false;this._update();}}
  _saveInputs(){localStorage.setItem("rflink_raw_tools.rawCommand",this._state.rawCommand||"");localStorage.setItem("rflink_raw_tools.repeat",String(this._state.repeat||1));localStorage.setItem("rflink_raw_tools.delayMs",String(this._state.delayMs||250));localStorage.setItem("rflink_raw_tools.port",this._state.port||"/dev/ttyUSB0");}
  async _sendRaw(){const raw=String(this._state.rawCommand||"").trim();if(!raw){this._state.error="Paste a learned RFLink device command first. Use Debug for setup checks.";this._state.message="";this._update();return;}const k=this._rawCommandKind(raw);if(k==="status")return this._checkSetup();if(k==="version")return this._checkVersion();this._saveInputs();await this._callService("rflink_raw","send_raw",{raw_command:raw,repeat:Number(this._state.repeat||1),delay_ms:Number(this._state.delayMs||250)},"RFLink command sent.");}
  _checkSetup(){return this._callService("rflink_raw","ping_gateway",{},"RFLink setup check complete.");}
  _checkVersion(){return this._callService("rflink_raw","version_gateway",{},"RFLink version-support check complete.");}
  async _installRflinkYaml(){this._saveInputs();await this._callService("rflink_raw","install_rflink_yaml",{port:this._state.port||"/dev/ttyUSB0"},"RFLink YAML install check complete. Restart Home Assistant if YAML was added.");}
  async _setDebug(t,en){this._state.status=this._state.status||{};this._state.status[t]=Boolean(en);localStorage.setItem(this._debugLocalKey(t),String(Boolean(en)));const label=t==="rfdebug"?"Decoded RFLink logging":"Raw RF capture logging";this._state.message=`${label} ${en?"enabled":"disabled"}.`;this._state.error="";this._update();await this._callService("rflink_raw","set_debug",{debug_type:t,enabled:Boolean(en)},`${label} ${en?"enabled":"disabled"}.`);}
  _clearRawCommand(){this._state.rawCommand="";localStorage.removeItem("rflink_raw_tools.rawCommand");this._state.message="Raw command cleared.";this._state.error="";this._update();}
  async _clearStatus(){this._state.message="";this._state.error="";await this._callService("rflink_raw","clear_status",{},"Status cleared.");}
  _copyCommand(cmd){this._state.rawCommand=cmd||"";this._state.tab="send";localStorage.setItem("rflink_raw_tools.tab","send");this._state.message="Command copied to Send.";this._state.error="";this._update();}
  _input(f,v){this._state[f]=v;this._update();}
  _setTab(t){this._state.tab=t;localStorage.setItem("rflink_raw_tools.tab",t);this._state.error="";this._state.message="";this._update();if(t==="captured")this._loadCaptured();if(t==="teach")this._loadAliases();if(t==="firmware")this._loadFirmwareLab();}

  _slug(v){return String(v||"").trim().toLowerCase().replace(/[^a-z0-9_]+/g,"_").replace(/^_+|_+$/g,"")||"rflink_alias";}
  _setTeachField(f,v){this._state.teach={...(this._state.teach||{}),[f]:v};}
  _teachFromEntity(idx){const i=(this._state.entities||[])[Number(idx)];if(!i)return;this._state.teach={id:this._slug(i.name||i.send_device_id||i.device_key),name:i.name||i.device_key||i.entity_id,entity_type:"switch",device_id:i.send_device_id||"",on_command:i.candidate_on||"",off_command:i.candidate_off||"",source_packet:"",notes:`Created from ${i.entity_id}`};this._setTab("teach");}
  _teachFromLog(idx){const rows=(this._state.logs||[]).filter(i=>i.raw_packet||i.send_candidate).slice().reverse();const i=rows[Number(idx)];if(!i)return;const cmd=i.send_candidate||"";const device=cmd.includes(";")?cmd.split(";")[0]:"";this._state.teach={id:this._slug(device||i.protocol||"captured_packet"),name:device||i.protocol||"Captured RFLink packet",entity_type:"switch",device_id:device,on_command:cmd.toLowerCase().endsWith(";off")?"":cmd,off_command:cmd.toLowerCase().endsWith(";off")?cmd:"",source_packet:i.raw_packet||"",notes:"Created from captured RFLink packet"};this._setTab("teach");}
  async _saveAlias(){if(!this._state.teach.name||!this._state.teach.device_id){this._state.error="Alias needs a friendly name and RFLink device id.";this._state.message="";this._update();return;}this._state.busy=true;this._state.error="";this._state.message="";this._update();try{const res=await this._hass.callApi("POST","rflink_raw/aliases",this._state.teach);this._state.aliases=res.aliases||[];this._state.message="Alias saved in RFLink Raw Tools.";this._state.teach={id:"",name:"",entity_type:"switch",device_id:"",on_command:"",off_command:"",source_packet:"",notes:""};}catch(e){this._state.error=this._safeError(e);}finally{this._state.busy=false;this._update();}}
  async _deleteAlias(id){this._state.busy=true;this._state.error="";this._update();try{const res=await this._hass.callApi("POST","rflink_raw/aliases",{delete:true,id});this._state.aliases=res.aliases||[];this._state.message="Alias deleted.";}catch(e){this._state.error=this._safeError(e);}finally{this._state.busy=false;this._update();}}
  _editAlias(id){const a=(this._state.aliases||[]).find(x=>x.id===id);if(!a)return;this._state.teach={...a};this._update();}
  async _testAliasCommand(cmd){if(!cmd){this._state.error="No command available for this alias.";this._update();return;}await this._callService("rflink_raw","send_raw",{raw_command:cmd,repeat:1,delay_ms:250},"Alias command sent.");}


  _setLabField(f,v){this._state.firmwareLab={...(this._state.firmwareLab||{}),[f]:v};}
  _setFirmwareField(f,v){this._state[f]=v;}
  async _firmwarePost(data,success){this._state.busy=true;this._state.error="";this._state.message="";this._update();try{const res=await this._hass.callApi("POST","rflink_raw/firmware_lab",data);this._state.firmwareLab=res.lab||{};this._state.firmwareReport=res.report||"";this._state.message=success||"Firmware Lab updated.";}catch(e){this._state.error=this._safeError(e);}finally{this._state.busy=false;this._update();}}
  async _startFirmwareLab(){const lab=this._state.firmwareLab||{};await this._firmwarePost({action:"start",project_name:lab.project_name||"Digiten remote",notes:lab.notes||"",reset:false},"Firmware Lab capture started. Name each button capture anything you want, then press the remote and capture it.");}
  async _stopFirmwareLab(){await this._firmwarePost({action:"stop"},"Firmware Lab capture stopped.");}
  async _captureFirmwareButton(){await this._firmwarePost({action:"capture",label:this._state.firmwareButtonLabel||"Unnamed button",notes:this._state.firmwareButtonNotes||""},"Button capture stored.");}
  async _clearFirmwareLab(){await this._firmwarePost({action:"clear"},"Firmware Lab cleared.");}
  async _deleteFirmwareCapture(id){await this._firmwarePost({action:"delete_capture",id},"Capture deleted.");}
  async _saveFirmwareNotes(){const lab=this._state.firmwareLab||{};await this._firmwarePost({action:"update",project_name:lab.project_name||"",notes:lab.notes||""},"Firmware Lab notes saved.");}
  _downloadFirmwareReport(){const text=this._state.firmwareReport||"";const blob=new Blob([text],{type:"text/plain"});const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download=`rflink-firmware-lab-${Date.now()}.txt`;a.click();URL.revokeObjectURL(url);}
  async _copyFirmwareReport(){await navigator.clipboard.writeText(this._state.firmwareReport||"");this._state.message="Firmware Lab report copied.";this._state.error="";this._update();}

  _feedback(){return`${this._state.message?`<div class="message">${this._state.message}</div>`:""}${this._state.error?`<div class="error">${this._state.error}</div>`:""}`;}
  _statusBadge(){const r=(this._state.status||{}).readiness||"checking";if(r==="ready")return`<span class="badge ok">● RFLink ready</span>`;if(r==="loaded")return`<span class="badge ok">● RFLink loaded</span>`;if(r==="configured_needs_restart")return`<span class="badge warn">● RFLink configured — restart needed</span>`;if(r==="not_configured")return`<span class="badge bad">● RFLink not configured</span>`;if(r==="status_api_unavailable")return`<span class="badge warn">● Status unavailable</span>`;return`<span class="badge warn">● Checking status…</span>`;}
  _sendView(){
    return`<div class="grid">
      <div class="card">
        <h2>Send RFLink device command</h2>
        <p class="help">Only send a real command copied from <b>Captured</b> or learned from RFLink logs. The examples on this page are documentation only; they are not working device IDs.</p>
        <label>RFLink command</label>
        <textarea data-field="rawCommand" placeholder="Paste from Captured, for example: newkaku_0000c6c2_1;on">${this._state.rawCommand||""}</textarea>
        <div class="row">
          <div><label>Repeat</label><input data-field="repeat" type="number" min="1" value="${this._state.repeat||1}"></div>
          <div><label>Delay between repeats (ms)</label><input data-field="delayMs" type="number" min="0" value="${this._state.delayMs||250}"></div>
        </div>
        <div class="actions">
          <button data-action="_sendRaw" ${this._state.busy?"disabled":""}>Send command</button>
          <button class="secondary" data-action="_clearRawCommand">Clear command</button>
          <button class="secondary" data-tablink="captured">Open Captured</button>
        </div>
        ${this._feedback()}
      </div>

      <div class="card">
        <h2>Accepted command formats</h2>
        <p class="help">Documentation only. Do not send these examples; paste an actual candidate copied from Captured.</p>
        <div class="example no-copy"><code>newkaku_0000c6c2_1;on</code></div>
        <div class="example no-copy"><code>newkaku_0000c6c2_1;off</code></div>
        <div class="example no-copy"><code>10;NewKaku;0000c6c2;1;ON;</code></div>
        <p class="help">If RFLink returns <code>'id'</code>, that device/protocol is not sendable through Home Assistant RFLink. It is usually receive-only, sensor-like, RF noise, or unsupported by the RFLink database.</p>
      </div>
    </div>`;}

  _capturedView(){
    const entities=this._state.entities||[];
    const controllable=entities.filter(i=>i.candidate_on||i.candidate_off).length;
    const rawPackets=(this._state.logs||[]).filter(i=>i.raw_packet||i.send_candidate);
    const otherLogs=(this._state.logs||[]).filter(i=>!i.raw_packet&&!i.send_candidate);

    const entityCards=entities.map((i,idx)=>{
      const isControllable=!!(i.candidate_on||i.candidate_off);
      const kind=isControllable?"Command-capable":"Read-only / sensor";
      return `<div class="entity-card ${isControllable?"can-send":"read-only"}">
        <div class="entity-top">
          <div>
            <div class="entity-title">${i.name||i.entity_id}</div>
            <code class="entity-id">${i.entity_id}</code>
          </div>
          <span class="state-pill">${i.state||"unknown"}</span>
        </div>
        <div class="entity-meta">
          <span>Protocol <b>${i.protocol||"—"}</b></span>
          <span>Address <b>${i.address||"—"}</b></span>
          ${i.switch?`<span>Switch <b>${i.switch}</b></span>`:""}
          <span>${kind}</span>
        </div>
        <div class="device-key">RFLink device key <code>${i.device_key||"—"}</code></div>
        ${isControllable?`<div class="command-box"><button class="secondary tiny" data-teach-entity="${idx}">Teach as device</button>
          ${i.candidate_on?`<div class="command-row"><code>${i.candidate_on}</code><button class="tiny" data-copy-command="${i.candidate_on}">Copy ON</button></div>`:""}
          ${i.candidate_off?`<div class="command-row"><code>${i.candidate_off}</code><button class="tiny" data-copy-command="${i.candidate_off}">Copy OFF</button></div>`:""}
        </div>`:`<div class="no-command">No send command suggested for this entity type. Sensors/read-only entities are receive-only.</div>`}
      </div>`;
    }).join("");

    const rawRows=rawPackets.slice().reverse().map((i,idx)=>`<div class="raw-card">
      ${i.raw_packet?`<div class="raw-block"><div class="label">Raw packet</div><code>${i.raw_packet}</code></div>`:""}
      ${i.send_candidate?`<div class="raw-block candidate-send"><div class="label">Send candidate</div><code>${i.send_candidate}</code><button class="tiny" data-copy-command="${i.send_candidate}">Copy to Send</button><button class="secondary tiny" data-teach-log="${idx}">Teach</button></div>`:""}
      <details><summary>Log line</summary><pre>${i.line}</pre></details>
    </div>`).join("");

    const otherLogRows=otherLogs.slice().reverse().slice(0,8).map(i=>`<div class="raw-card muted-card"><pre>${i.line}</pre></div>`).join("");

    return`<div class="captured-layout">
      <section class="card hero-card">
        <div class="hero-row">
          <div>
            <h2>Captured RFLink data</h2>
            <p class="help">Use this page to turn noisy RFLink discovery into usable ON/OFF commands. Entities are not the same as raw packets; raw packets appear after raw logging captures a remote press.</p>
          </div>
          <div class="stat-row">
            <div class="stat"><b>${entities.length}</b><span>entities</span></div>
            <div class="stat"><b>${controllable}</b><span>command candidates</span></div>
            <div class="stat"><b>${rawPackets.length}</b><span>raw packets</span></div>
          </div>
        </div>
        <div class="actions">
          <button data-action="_loadCaptured">Refresh captured data</button>
          <button class="secondary" data-tablink="debug">Turn on raw logging</button>
        </div>
        ${this._feedback()}
      </section>

      <section class="captured-columns">
        <div class="card">
          <div class="section-heading">
            <div>
              <h3>Discovered RFLink entities</h3><p class="help">Candidate send commands are shown only when the entity looks command-capable.</p><h3 style="display:none"></h3>
              <p class="help">These come from Home Assistant's RFLink entity registry. Command-capable lights/switches show candidate send commands.</p>
            </div>
          </div>
          ${entityCards?`<div class="entity-grid">${entityCards}</div>`:`<div class="empty-state"><b>No RFLink entities found yet.</b><span>Enable RFLink, press a remote, then refresh.</span></div>`}
        </div>

        <aside class="card raw-panel">
          <h3>Raw RFLink packets</h3>
          <p class="help">To populate this panel: <b>Debug → Raw RF capture logging</b>, press one physical remote button, then refresh. This uses Home Assistant logs; it does not send rfdebug/qrfdebug commands to the gateway.</p>
          ${rawRows||`<div class="empty-state"><b>No raw RFLink packets found yet.</b><span>The app looked in <code>home-assistant.log</code> for recent <code>10;</code> or <code>20;</code> RFLink packets.</span></div>`}
          ${!rawRows&&otherLogRows?`<h4>Other recent RFLink log lines</h4>${otherLogRows}`:""}
        </aside>
      </section>
    </div>`;}

  _teachView(){const t=this._state.teach||{};const aliases=this._state.aliases||[];const aliasCards=aliases.map(a=>`<div class="alias-card"><div class="entity-top"><div><div class="entity-title">${a.name}</div><code class="entity-id">${a.device_id}</code></div><span class="state-pill">${a.entity_type}</span></div><div class="command-box">${a.on_command?`<div class="command-row"><code>${a.on_command}</code><button class="tiny" data-alias-test="${a.on_command}">Test ON</button><button class="secondary tiny" data-copy-command="${a.on_command}">Copy</button></div>`:""}${a.off_command?`<div class="command-row"><code>${a.off_command}</code><button class="tiny" data-alias-test="${a.off_command}">Test OFF</button><button class="secondary tiny" data-copy-command="${a.off_command}">Copy</button></div>`:""}</div><div class="actions"><button class="secondary" data-edit-alias="${a.id}">Edit</button><button class="secondary" data-delete-alias="${a.id}">Delete</button></div>${a.source_packet?`<details><summary>Source packet</summary><pre>${a.source_packet}</pre></details>`:""}</div>`).join("");
    return`<div class="captured-layout"><section class="card hero-card"><h2>Teach / Alias</h2><p class="help">Create friendly RFLink Raw Tools names from decoded RFLink packets or Captured command candidates. Saved aliases appear inside RFLink Raw Tools. Home Assistant entity exposure is disabled in this safe-loader build.</p>${this._feedback()}</section><section class="captured-columns"><div class="card"><h3>Alias editor</h3><label>Friendly name</label><input data-teach-field="name" value="${t.name||""}" placeholder="Bedroom AC outlet"><label>Entity type</label><select data-teach-field="entity_type"><option value="switch" ${(t.entity_type||"switch")==="switch"?"selected":""}>switch</option><option value="light" ${t.entity_type==="light"?"selected":""}>light-style switch</option><option value="button" ${t.entity_type==="button"?"selected":""}>button / one-shot</option></select><label>RFLink device id</label><input data-teach-field="device_id" value="${t.device_id||""}" placeholder="newkaku_0000c6c2_1"><label>ON command</label><input data-teach-field="on_command" value="${t.on_command||""}" placeholder="newkaku_0000c6c2_1;on"><label>OFF command</label><input data-teach-field="off_command" value="${t.off_command||""}" placeholder="newkaku_0000c6c2_1;off"><label>Source packet / notes</label><textarea data-teach-field="source_packet" placeholder="20;... or notes from the captured packet">${t.source_packet||""}</textarea><textarea data-teach-field="notes" placeholder="Notes">${t.notes||""}</textarea><div class="actions"><button data-action="_saveAlias" ${this._state.busy?"disabled":""}>Save alias</button><button class="secondary" data-tablink="captured">Back to Captured</button></div></div><aside class="card raw-panel"><h3>Saved aliases</h3>${aliasCards||`<div class="empty-state"><b>No aliases saved yet.</b><span>Use Captured → Teach as device, or fill the editor manually.</span></div>`}</aside></section></div>`;}


  _firmwareView(){
    const lab=this._state.firmwareLab||{};
    const captures=lab.captures||[];
    const captureCards=captures.slice().reverse().map(c=>`<div class="alias-card">
      <div class="entity-top"><div><div class="entity-title">${c.label||"Unnamed capture"}</div><code class="entity-id">${c.captured_at||""}</code></div><span class="state-pill">${(c.summary&&c.summary.line_count)||0} lines</span></div>
      ${c.notes?`<p class="help">${c.notes}</p>`:""}
      <div class="entity-meta">
        <span>Raw packets <b>${(c.summary&&c.summary.raw_packet_count)||0}</b></span>
        <span>Pulse lines <b>${(c.summary&&c.summary.pulse_line_count)||0}</b></span>
        <span>Protocols <b>${((c.summary&&c.summary.protocols)||[]).join(", ")||"—"}</b></span>
      </div>
      <details><summary>Captured log lines</summary><pre>${(c.lines||[]).join("\n")||"No matching RFLink debug/pulse lines found for this capture."}</pre></details>
      <div class="actions"><button class="secondary" data-delete-firmware-capture="${c.id}">Delete capture</button></div>
    </div>`).join("");
    return`<div class="captured-layout">
      <section class="card hero-card">
        <div class="hero-row"><div><h2>Firmware Lab</h2><p class="help">Capture unsupported remote evidence for firmware/protocol work. You can name each capture anything you want: <b>Digiten ON</b>, <b>Digiten OFF</b>, <b>Button 1</b>, etc.</p></div><div class="stat-row"><div class="stat"><b>${captures.length}</b><span>captures</span></div><div class="stat"><b>${lab.active?"ON":"OFF"}</b><span>capture mode</span></div><div class="stat"><b>${captures.reduce((n,c)=>n+((c.summary&&c.summary.line_count)||0),0)}</b><span>stored lines</span></div></div></div>
        ${this._feedback()}
      </section>
      <section class="captured-columns">
        <div class="card">
          <h3>Capture setup</h3>
          <label>Lab/project name</label><input data-lab-field="project_name" value="${lab.project_name||"Digiten remote"}" placeholder="Digiten remote">
          <label>Protocol notes</label><textarea data-lab-field="notes" placeholder="Paste protocol notes, observations, battery/device model, FCC ID, button behavior, repeat count, etc.">${lab.notes||""}</textarea>
          <div class="actions"><button data-action="_startFirmwareLab" ${this._state.busy?"disabled":""}>Start RF debug capture</button><button class="secondary" data-action="_stopFirmwareLab">Stop capture</button><button class="secondary" data-action="_saveFirmwareNotes">Save notes</button></div>
          <hr>
          <h3>Store one button press</h3>
          <p class="help">Type any label you want, press the physical remote button, then click Store latest lines. Typing will not refresh or shift the screen.</p>
          <label>Button/capture name</label><input data-firmware-field="firmwareButtonLabel" value="${this._state.firmwareButtonLabel||"Digiten ON"}" placeholder="Digiten ON">
          <label>Button notes</label><textarea data-firmware-field="firmwareButtonNotes" placeholder="Example: held for 1 second, outlet ON, red LED flashed">${this._state.firmwareButtonNotes||""}</textarea>
          <div class="actions"><button data-action="_captureFirmwareButton" ${this._state.busy?"disabled":""}>Store latest RFLink lines for this button</button><button class="secondary" data-action="_clearFirmwareLab">Clear lab</button></div>
          <p class="help">This uses Home Assistant RFLink logging. If no pulse/debug lines appear, RFLink/HA is not exposing raw firmware-level timing data yet.</p>
        </div>
        <aside class="card raw-panel">
          <h3>Unsupported-device report</h3>
          <p class="help">Export this for RFLink firmware/protocol support or future firmware development.</p>
          <div class="actions"><button data-action="_downloadFirmwareReport">Download report</button><button class="secondary" data-action="_copyFirmwareReport">Copy report</button></div>
          <h3>Stored captures</h3>
          ${captureCards||`<div class="empty-state"><b>No button captures yet.</b><span>Start capture, press the remote, then store latest RFLink lines.</span></div>`}
        </aside>
      </section>
    </div>`;}

  _debugView(){return`<div class="grid"><div class="card"><h2>Diagnostics</h2><p class="help">These checks do not send RF hardware commands and should not show red errors.</p><div class="actions"><button data-action="_checkSetup">Check RFLink setup</button><button class="secondary" data-action="_checkVersion">Check version support</button><button class="secondary" data-action="_clearStatus">Clear status</button></div>${this._feedback()}</div><div class="card"><h2>Logging switches</h2><p class="help">This changes Home Assistant RFLink logging only; it does not send rfdebug/qrfdebug commands to the gateway.</p><p class="help">Use Raw RF capture logging to learn a remote. Switches keep their visual state across tabs.</p>${this._toggle('rfdebug','Decoded RFLink logging','decoded protocol messages in Home Assistant logs')}${this._toggle('qrfdebug','Raw RF capture logging','raw 433 MHz capture output used to learn remotes')}</div></div>`;}
  _toggle(id,title,help){return`<div class="toggle-row"><div><div class="toggle-title">${title}</div><div class="toggle-help">${this._debugEnabled(id)?"Enabled":"Disabled"} — ${help}.</div></div><label class="switch"><input type="checkbox" data-toggle-debug="${id}" ${this._debugEnabled(id)?"checked":""}><span class="slider"></span></label></div>`;}
  _setupView(){const s=this._state.status||{};return`<div class="grid"><div class="card"><h2>Setup</h2><p><b>Integration version:</b> ${s.version||"0.0.1"}</p><p><b>RFLink YAML:</b> ${s.rflink_configured?"Found":"Not found"}</p><p><b>Home Assistant RFLink loaded:</b> ${s.rflink_loaded?"Yes":"No"}</p><p><b>RFLink live bridge:</b> ${s.rflink_connected?"Connected":"Not confirmed"}</p><p class="help">${s.readiness_detail||"Use Check RFLink setup."}</p><div class="actions"><button data-action="_checkSetup">Check RFLink setup</button><button class="secondary" data-action="_clearStatus">Clear status</button></div>${this._feedback()}</div><div class="card"><h2>Install RFLink YAML</h2><p class="help">Only use this if RFLink YAML is not found. It adds a conservative top-level <code>rflink:</code> block and makes a backup first.</p><label>Serial port</label><input data-field="port" value="${this._state.port||"/dev/ttyUSB0"}"><div class="actions"><button data-action="_installRflinkYaml">Install RFLink YAML</button></div><p class="help">After install, restart Home Assistant Core. This does not edit Lovelace dashboards.</p></div></div>`;}
  _body(){if(this._state.tab==="captured")return this._capturedView();if(this._state.tab==="teach")return this._teachView();if(this._state.tab==="firmware")return this._firmwareView();if(this._state.tab==="debug")return this._debugView();if(this._state.tab==="setup")return this._setupView();return this._sendView();}
  _render(){this.innerHTML=`<style>:host{display:block;padding:24px;min-height:100vh;color:var(--primary-text-color);background:var(--primary-background-color);box-sizing:border-box}.header{display:flex;justify-content:space-between;gap:18px;align-items:center;margin-bottom:18px}.brand{display:flex;align-items:center;gap:16px}.logo{width:72px;height:72px;border-radius:14px;object-fit:contain}h1{margin:0;font-size:34px}h2{margin:0 0 14px;font-size:24px}p{color:var(--secondary-text-color);line-height:1.45}.badge{border:1px solid var(--divider-color);border-radius:999px;padding:8px 12px;font-weight:800;white-space:nowrap}.ok{color:#4caf50}.warn{color:#ff9800}.bad{color:#ff6b6b}.tabs{display:flex;gap:6px;margin:14px 0 22px;flex-wrap:wrap;padding:6px;border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:18px;width:max-content;max-width:100%;box-sizing:border-box}.tab,button{border:0;border-radius:12px;padding:11px 16px;font-weight:800;cursor:pointer;background:var(--primary-color);color:var(--text-primary-color,#fff)}.tab{background:transparent;color:var(--secondary-text-color);border:1px solid transparent;box-shadow:none}.tab.active{background:var(--primary-color);color:var(--text-primary-color,#fff);border-color:var(--primary-color);box-shadow:none}.tab:active{filter:brightness(.95)}.tab:not(.active):hover{background:var(--secondary-background-color);color:var(--primary-text-color);border-color:var(--divider-color)}.secondary{background:var(--secondary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color)}.tiny{padding:6px 10px;font-size:12px;margin-right:8px}.grid{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(300px,.85fr);gap:18px;align-items:start}.card{border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:18px;padding:22px;box-sizing:border-box}label{display:block;font-weight:800;margin:14px 0 8px}textarea,input,select{width:100%;box-sizing:border-box;background:var(--secondary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color);border-radius:12px;padding:14px;font:inherit}textarea{min-height:108px;font-family:monospace}.row{display:grid;grid-template-columns:1fr 1fr;gap:14px}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.message,.error{border-radius:14px;padding:14px 16px;margin-top:16px;font-weight:800}.message{background:rgba(76,175,80,.16);color:#81c784}.error{background:rgba(244,67,54,.18);color:#ff8a80}.example,.log-line{border:1px solid var(--divider-color);border-radius:12px;padding:12px;margin:10px 0;background:var(--secondary-background-color);font-family:monospace}.help{color:var(--secondary-text-color)}.toggle-row{display:flex;align-items:center;justify-content:space-between;gap:16px;border:1px solid var(--divider-color);background:var(--secondary-background-color);border-radius:16px;padding:16px;margin:12px 0}.toggle-title{font-weight:900}.toggle-help{color:var(--secondary-text-color);font-size:13px;margin-top:4px}.switch{position:relative;display:inline-block;width:54px;height:30px;margin:0;flex:0 0 auto}.switch input{opacity:0;width:0;height:0}.slider{position:absolute;cursor:pointer;inset:0;background:var(--divider-color);transition:.2s;border-radius:999px}.slider:before{position:absolute;content:"";height:22px;width:22px;left:4px;bottom:4px;background:white;transition:.2s;border-radius:50%}.switch input:checked+.slider{background:var(--primary-color)}.switch input:checked+.slider:before{transform:translateX(24px)}table{width:100%;border-collapse:collapse;margin-top:10px}th,td{text-align:left;padding:8px;border-bottom:1px solid var(--divider-color);vertical-align:top}code,pre{font-family:monospace}pre{white-space:pre-wrap;color:var(--secondary-text-color);margin:8px 0 0}.captured-layout{display:grid;gap:18px;max-width:1320px}.hero-card{padding:24px}.hero-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:20px;align-items:start}.stat-row{display:grid;grid-template-columns:repeat(3,minmax(92px,1fr));gap:10px;min-width:330px}.stat{border:1px solid var(--divider-color);border-radius:14px;background:var(--secondary-background-color);padding:12px;text-align:center}.stat b{display:block;font-size:24px;line-height:1.1;color:var(--primary-text-color)}.stat span{display:block;color:var(--secondary-text-color);font-size:12px;margin-top:4px}.captured-columns{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(340px,.85fr);gap:18px;align-items:start}.section-heading{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.entity-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:12px;margin-top:14px}.entity-card{border:1px solid var(--divider-color);border-radius:16px;background:var(--secondary-background-color);padding:14px;display:grid;gap:10px;min-width:0}.entity-card.can-send{border-color:color-mix(in srgb,var(--primary-color) 42%,var(--divider-color));box-shadow:inset 3px 0 0 var(--primary-color)}.entity-card.read-only{opacity:.86}.entity-top{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:start}.entity-title{font-weight:900;font-size:15px;line-height:1.25;word-break:break-word}.entity-id{display:block;margin-top:4px;color:var(--secondary-text-color);white-space:normal;word-break:break-word;font-size:12px}.state-pill{border:1px solid var(--divider-color);border-radius:999px;padding:5px 9px;font-size:12px;color:var(--secondary-text-color);white-space:nowrap;background:var(--card-background-color)}.entity-meta{display:flex;flex-wrap:wrap;gap:7px}.entity-meta span{border:1px solid var(--divider-color);border-radius:999px;padding:5px 8px;font-size:12px;color:var(--secondary-text-color);background:var(--card-background-color)}.device-key{color:var(--secondary-text-color);font-size:12px;word-break:break-word}.command-box{display:grid;gap:8px}.command-row,.candidate-send{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center}.command-row code,.raw-block code{display:block;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:10px;padding:8px;white-space:normal;word-break:break-word;font-size:12px}.no-command{color:var(--secondary-text-color);font-size:13px}.raw-panel{position:sticky;top:18px}.raw-card,.alias-card{border:1px solid var(--divider-color);border-radius:16px;background:var(--secondary-background-color);padding:14px;margin:12px 0}.raw-block{margin:8px 0}.label{font-size:12px;font-weight:900;color:var(--secondary-text-color);margin-bottom:6px;text-transform:uppercase;letter-spacing:.04em}.empty-state{border:1px dashed var(--divider-color);border-radius:16px;padding:18px;background:var(--secondary-background-color);display:grid;gap:6px;color:var(--secondary-text-color)}.empty-state b{color:var(--primary-text-color)}.muted-card pre{max-height:180px;overflow:auto}@media(max-width:900px){:host{padding:16px}.grid,.row,.captured-columns,.hero-row{grid-template-columns:1fr}.header{align-items:flex-start;flex-direction:column}h1{font-size:28px}.stat-row{grid-template-columns:repeat(3,1fr);min-width:0;width:100%}.entity-grid{grid-template-columns:1fr}.raw-panel{position:static}.command-row,.candidate-send{grid-template-columns:1fr}.tabs{width:100%}.tab{flex:1 1 auto}}</style><div class="header"><div class="brand"><img class="logo" src="/api/rflink_raw/static/logo.png" alt="RFLink Raw Tools"><div><h1>RFLink Raw Tools</h1><p class="help">Capture RFLink devices, inspect raw log lines, and send learned commands.</p></div></div><div id="status-badge">${this._statusBadge()}</div></div><div class="tabs"><button class="tab ${this._state.tab==="send"?"active":""}" data-tab="send">Send</button><button class="tab ${this._state.tab==="captured"?"active":""}" data-tab="captured">Captured</button><button class="tab ${this._state.tab==='teach'?'active':''}" data-tab="teach">Teach</button><button class="tab ${this._state.tab==='firmware'?'active':''}" data-tab="firmware">Firmware Lab</button><button class="tab ${this._state.tab==="debug"?"active":""}" data-tab="debug">Debug</button><button class="tab ${this._state.tab==="setup"?"active":""}" data-tab="setup">Setup</button></div><main id="body"></main>`;this._bind();this._update();}
  _bind(){this.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>this._setTab(b.dataset.tab)));}
  _updateStatusBadge(){const badge=this.querySelector('#status-badge');if(badge)badge.innerHTML=this._statusBadge();}
  _updateTabs(){this.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===this._state.tab));}
  _update(){if(!this._rendered)return;this._updateTabs();this._updateStatusBadge();const body=this.querySelector('#body');if(!body)return;body.innerHTML=this._body();body.querySelectorAll('[data-action]').forEach(el=>el.addEventListener('click',()=>this[el.dataset.action]&&this[el.dataset.action]()));body.querySelectorAll('[data-tablink]').forEach(el=>el.addEventListener('click',()=>this._setTab(el.dataset.tablink)));body.querySelectorAll('[data-copy-command]').forEach(el=>el.addEventListener('click',()=>this._copyCommand(el.dataset.copyCommand)));body.querySelectorAll('[data-field]').forEach(el=>el.addEventListener('input',e=>this._input(el.dataset.field,el.type==='number'?Number(e.target.value):e.target.value)));body.querySelectorAll('[data-toggle-debug]').forEach(el=>el.addEventListener('change',e=>this._setDebug(el.dataset.toggleDebug,Boolean(e.target.checked))));body.querySelectorAll('[data-teach-field]').forEach(el=>el.addEventListener('input',e=>this._setTeachField(el.dataset.teachField,e.target.value)));body.querySelectorAll('select[data-teach-field]').forEach(el=>el.addEventListener('change',e=>this._setTeachField(el.dataset.teachField,e.target.value)));body.querySelectorAll('[data-teach-entity]').forEach(el=>el.addEventListener('click',()=>this._teachFromEntity(el.dataset.teachEntity)));body.querySelectorAll('[data-teach-log]').forEach(el=>el.addEventListener('click',()=>this._teachFromLog(el.dataset.teachLog)));body.querySelectorAll('[data-delete-alias]').forEach(el=>el.addEventListener('click',()=>this._deleteAlias(el.dataset.deleteAlias)));body.querySelectorAll('[data-edit-alias]').forEach(el=>el.addEventListener('click',()=>this._editAlias(el.dataset.editAlias)));body.querySelectorAll('[data-alias-test]').forEach(el=>el.addEventListener('click',()=>this._testAliasCommand(el.dataset.aliasTest)));body.querySelectorAll('[data-lab-field]').forEach(el=>el.addEventListener('input',e=>this._setLabField(el.dataset.labField,e.target.value)));body.querySelectorAll('[data-firmware-field]').forEach(el=>el.addEventListener('input',e=>this._setFirmwareField(el.dataset.firmwareField,e.target.value)));body.querySelectorAll('[data-delete-firmware-capture]').forEach(el=>el.addEventListener('click',()=>this._deleteFirmwareCapture(el.dataset.deleteFirmwareCapture)));}
}
customElements.define('rflink-raw-tools-panel',RFLinkRawToolsPanel);
