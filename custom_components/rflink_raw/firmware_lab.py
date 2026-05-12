"""Firmware/protocol lab helpers for RFLink Raw Tools."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

LAB_FILE = "rflink_raw_firmware_lab.json"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(LAB_FILE))


def _default_lab() -> dict[str, Any]:
    return {
        "project_name": "",
        "notes": "",
        "active": False,
        "started_at": "",
        "updated_at": "",
        "captures": [],
    }


def _read(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _default_lab()
    try:
        data = json.loads(path.read_text())
    except Exception:
        return _default_lab()
    if not isinstance(data, dict):
        return _default_lab()

    lab = _default_lab()
    lab.update(data)
    if not isinstance(lab.get("captures"), list):
        lab["captures"] = []
    return lab


def _write(path: Path, lab: dict[str, Any]) -> None:
    lab["updated_at"] = _now()
    path.write_text(json.dumps(lab, indent=2, sort_keys=True) + "\n")


def _looks_like_firmware_capture_line(line: str) -> bool:
    lower = line.lower()
    if "rflink" in lower and ("debug" in lower or "pulse" in lower or "20;" in line or "10;" in line):
        return True
    if "20;" in line and ("debug" in lower or "pulse" in lower or "pulses" in lower):
        return True
    if "pulses(usec)" in lower or "pulses=" in lower or "pulses(" in lower:
        return True
    return False


def _read_recent_capture_lines(hass: HomeAssistant, max_lines: int = 220) -> list[str]:
    log_path = Path(hass.config.path("home-assistant.log"))
    if not log_path.exists():
        return []

    lines: list[str] = []
    for line in log_path.read_text(errors="ignore").splitlines()[-8000:]:
        if _looks_like_firmware_capture_line(line):
            lines.append(line[-1200:])
    return lines[-max_lines:]


def _capture_summary(lines: list[str]) -> dict[str, Any]:
    raw_packets = [line for line in lines if "20;" in line or "10;" in line]
    pulse_lines = [line for line in lines if "pulse" in line.lower()]
    protocols = []
    for line in lines:
        match = re.search(r"\b20;[^;]+;([^;]+);", line)
        if match:
            protocols.append(match.group(1))
    return {
        "line_count": len(lines),
        "raw_packet_count": len(raw_packets),
        "pulse_line_count": len(pulse_lines),
        "protocols": sorted(set(protocols)),
    }


async def async_get_firmware_lab(hass: HomeAssistant) -> dict[str, Any]:
    return await hass.async_add_executor_job(_read, _path(hass))


async def async_update_firmware_lab(hass: HomeAssistant, updates: dict[str, Any]) -> dict[str, Any]:
    def _update() -> dict[str, Any]:
        path = _path(hass)
        lab = _read(path)
        for key in ("project_name", "notes"):
            if key in updates:
                lab[key] = str(updates.get(key) or "")
        _write(path, lab)
        return lab

    return await hass.async_add_executor_job(_update)


async def async_start_firmware_lab(hass: HomeAssistant, project_name: str = "", notes: str = "", reset: bool = False) -> dict[str, Any]:
    def _start() -> dict[str, Any]:
        path = _path(hass)
        lab = _default_lab() if reset else _read(path)
        if project_name:
            lab["project_name"] = str(project_name)
        if notes:
            lab["notes"] = str(notes)
        lab["active"] = True
        lab["started_at"] = _now()
        _write(path, lab)
        return lab

    return await hass.async_add_executor_job(_start)


async def async_stop_firmware_lab(hass: HomeAssistant) -> dict[str, Any]:
    def _stop() -> dict[str, Any]:
        path = _path(hass)
        lab = _read(path)
        lab["active"] = False
        _write(path, lab)
        return lab

    return await hass.async_add_executor_job(_stop)


async def async_clear_firmware_lab(hass: HomeAssistant) -> dict[str, Any]:
    def _clear() -> dict[str, Any]:
        lab = _default_lab()
        _write(_path(hass), lab)
        return lab

    return await hass.async_add_executor_job(_clear)


async def async_capture_firmware_button(hass: HomeAssistant, label: str, notes: str = "") -> dict[str, Any]:
    label = str(label or "").strip() or "Unnamed capture"
    notes = str(notes or "").strip()

    lines = await hass.async_add_executor_job(_read_recent_capture_lines, hass)
    capture = {
        "id": re.sub(r"[^a-zA-Z0-9_]+", "_", f"{label}_{_now()}").strip("_").lower(),
        "label": label,
        "notes": notes,
        "captured_at": _now(),
        "lines": lines,
        "summary": _capture_summary(lines),
    }

    def _save() -> dict[str, Any]:
        path = _path(hass)
        lab = _read(path)
        lab["captures"].append(capture)
        _write(path, lab)
        return lab

    return await hass.async_add_executor_job(_save)


async def async_delete_firmware_capture(hass: HomeAssistant, capture_id: str) -> dict[str, Any]:
    clean = str(capture_id or "")

    def _delete() -> dict[str, Any]:
        path = _path(hass)
        lab = _read(path)
        lab["captures"] = [item for item in lab.get("captures", []) if item.get("id") != clean]
        _write(path, lab)
        return lab

    return await hass.async_add_executor_job(_delete)


def export_firmware_lab_report(lab: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# RFLink Unsupported Device / Firmware Lab Report")
    lines.append("")
    lines.append(f"Project: {lab.get('project_name') or 'Untitled'}")
    lines.append(f"Started: {lab.get('started_at') or 'Not recorded'}")
    lines.append(f"Updated: {lab.get('updated_at') or 'Not recorded'}")
    lines.append("")
    lines.append("## Notes")
    lines.append(lab.get("notes") or "(none)")
    lines.append("")
    lines.append("## Captures")
    captures = lab.get("captures") or []
    if not captures:
        lines.append("(none)")
    for capture in captures:
        lines.append("")
        lines.append(f"### {capture.get('label') or 'Unnamed capture'}")
        lines.append(f"Captured at: {capture.get('captured_at') or ''}")
        if capture.get("notes"):
            lines.append(f"Notes: {capture.get('notes')}")
        summary = capture.get("summary") or {}
        lines.append(f"Line count: {summary.get('line_count', 0)}")
        lines.append(f"Raw packet lines: {summary.get('raw_packet_count', 0)}")
        lines.append(f"Pulse lines: {summary.get('pulse_line_count', 0)}")
        protocols = summary.get("protocols") or []
        if protocols:
            lines.append(f"Decoded protocols: {', '.join(protocols)}")
        lines.append("")
        lines.append("```text")
        for line in capture.get("lines") or []:
            lines.append(str(line))
        lines.append("```")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("If the capture has decoded protocol packets, create a Home Assistant/RFLink Raw Tools alias from the derived device id.")
    lines.append("If the capture only has pulse/debug lines, RFLink firmware support is probably needed before Home Assistant can send this protocol.")
    return "\n".join(lines) + "\n"
