"""Helpers for parsing textual GDB output."""

from __future__ import annotations

import re
from typing import Optional

_INFO_LINE_RE = re.compile(r'Line\s+(\d+)\s+of\s+"([^"]+)"')
_INFO_SOURCE_RE = re.compile(r"Current source file is\s+([^\s]+)")
_SOURCE_LINE_RE = re.compile(r"^\s*(\d+)\s+")


def parse_info_line(output: str) -> Optional[tuple[str, int]]:
    """Extract `file` and current line from `info line` output."""
    match = _INFO_LINE_RE.search(output)
    if not match:
        return None
    return (match.group(2), int(match.group(1)))


def parse_info_source(output: str) -> Optional[str]:
    """Extract source path from `info source` output."""
    match = _INFO_SOURCE_RE.search(output)
    if not match:
        return None
    return match.group(1)


def extract_line_range(output: str) -> Optional[tuple[int, int]]:
    """Extract first and last visible source line numbers from `list` output."""
    matches: list[int] = []
    for raw_line in output.splitlines():
        line_match = _SOURCE_LINE_RE.match(raw_line)
        if line_match:
            matches.append(int(line_match.group(1)))
    if not matches:
        return None
    return (matches[0], matches[-1])
