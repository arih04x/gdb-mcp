"""Helpers for parsing textual GDB output into machine-friendly structures."""

from __future__ import annotations

import re
from typing import Any, Optional

from pygdbmi.gdbmiparser import parse_response

_BACKTRACE_LINE_RE = re.compile(
    r"^#(?P<index>\d+)\s+(?:(?P<address>0x[0-9a-fA-F]+)\s+in\s+)?(?P<function>[^\s(]+)"
)
_BACKTRACE_LOCATION_RE = re.compile(r"\s+at\s+(?P<file>.+?):(?P<line>\d+)\s*$")
_REGISTER_LINE_RE = re.compile(r"^(?P<name>[a-zA-Z][a-zA-Z0-9_.]*)\s+(?P<value>\S+)(?:\s+(?P<detail>.*))?$")
_BREAKPOINT_LINE_RE = re.compile(r"^\s*(?P<number>\d+)\s+")
_HEX_RE = re.compile(r"0x[0-9a-fA-F]+")
_SOURCE_AT_RE = re.compile(r"\bat\s(?P<file>.+?):(?P<line>\d+)(?=\s|$)")
_MI_RECORD_RE = re.compile(r"^\d*[\^*=~&@]")
_MI_STRUCTURED_TYPES = {"result", "notify", "exec", "status"}
_MI_STREAM_TYPES = {"console", "log", "target"}


def parse_backtrace_frames(output: str) -> list[dict[str, str | int]]:
    """Parse `backtrace` textual output into structured frame objects."""
    frames: list[dict[str, str | int]] = []
    for raw in output.splitlines():
        line = raw.strip()
        if not line.startswith("#"):
            continue
        match = _BACKTRACE_LINE_RE.match(line)
        if not match:
            continue

        frame: dict[str, str | int] = {
            "index": int(match.group("index")),
            "function": match.group("function"),
            "raw": line,
        }
        address = match.group("address")
        if address:
            frame["address"] = address

        location = _BACKTRACE_LOCATION_RE.search(line)
        if location:
            frame["file"] = location.group("file")
            frame["line"] = int(location.group("line"))

        frames.append(frame)
    return frames


def parse_registers(output: str) -> dict[str, dict[str, str]]:
    """Parse `info registers` output into a register map."""
    registers: dict[str, dict[str, str]] = {}
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = _REGISTER_LINE_RE.match(line)
        if not match:
            continue
        detail = match.group("detail") or ""
        registers[match.group("name")] = {
            "value": match.group("value"),
            "detail": detail.strip(),
        }
    return registers


def parse_breakpoints(output: str) -> list[dict[str, str | int | bool]]:
    """Parse `info breakpoints` output into lightweight breakpoint records."""
    grouped_lines: list[tuple[str, list[str]]] = []
    current_head: str | None = None
    current_tail: list[str] = []

    for raw in output.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if _BREAKPOINT_LINE_RE.match(line):
            if current_head is not None:
                grouped_lines.append((current_head, current_tail))
            current_head = line
            current_tail = []
            continue
        if current_head is not None:
            current_tail.append(line)

    if current_head is not None:
        grouped_lines.append((current_head, current_tail))

    items: list[dict[str, str | int | bool]] = []
    for head, tail in grouped_lines:
        line = head
        combined = " ".join(part.strip() for part in [head, *tail] if part.strip())

        number = int(line.split()[0])
        item: dict[str, str | int | bool] = {"number": number, "raw": combined}

        lowered = f" {line.lower()} "
        if " breakpoint " in lowered:
            item["kind"] = "breakpoint"
        elif " watchpoint " in lowered:
            item["kind"] = "watchpoint"
        elif " catchpoint " in lowered:
            item["kind"] = "catchpoint"

        item["enabled"] = " y " in lowered

        address = _HEX_RE.search(line)
        if address:
            item["address"] = address.group(0)

        location = _SOURCE_AT_RE.search(combined)
        if location:
            item["file"] = location.group("file")
            item["line"] = int(location.group("line"))

        items.append(item)
    return items


def _collect_mi_records(output: str) -> list[dict[str, Any]]:
    """Parse all GDB/MI lines from mixed command output."""
    records: list[dict[str, Any]] = []
    for raw in output.splitlines():
        line = raw.strip()
        if not line or line == "(gdb)":
            continue
        if not _MI_RECORD_RE.match(line):
            continue
        parsed = parse_response(line)
        if parsed.get("type") == "output" and parsed.get("payload") == line:
            continue
        records.append(parsed)
    return records


def parse_mi_records(output: str) -> list[dict[str, Any]]:
    """Parse MI result/notify/exec/status lines from mixed output."""
    return [record for record in _collect_mi_records(output) if record.get("type") in _MI_STRUCTURED_TYPES]


def parse_mi_streams(output: str) -> list[dict[str, Any]]:
    """Parse MI console/log/target stream lines from mixed output."""
    streams = [record for record in _collect_mi_records(output) if record.get("type") in _MI_STREAM_TYPES]
    if not streams:
        return []

    merged: list[dict[str, Any]] = []
    for record in streams:
        if not merged:
            merged.append(record)
            continue

        previous = merged[-1]
        if record.get("type") != previous.get("type") or record.get("message") != previous.get("message"):
            merged.append(record)
            continue

        current_payload = previous.get("payload")
        next_payload = record.get("payload")
        if isinstance(current_payload, str) and isinstance(next_payload, str):
            previous["payload"] = f"{current_payload}{next_payload}"
        else:
            merged.append(record)
    return merged
