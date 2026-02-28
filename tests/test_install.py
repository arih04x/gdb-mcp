import sys

import pytest

from gdb_mcp.install import select_install_targets, update_mcp_config


def test_update_json_config_install() -> None:
    config: dict[str, object] = {}
    changed = update_mcp_config(config, ("mcpServers",), server_name="gdb", uninstall=False)
    assert changed is True
    servers = config["mcpServers"]
    assert isinstance(servers, dict)
    assert "gdb" in servers


def test_update_toml_config_uninstall() -> None:
    config: dict[str, object] = {"mcp_servers": {"gdb": {"command": "python3", "args": ["-m", "gdb_mcp.server"]}}}
    changed = update_mcp_config(config, ("mcp_servers",), server_name="gdb", uninstall=True)
    assert changed is True
    servers = config["mcp_servers"]
    assert isinstance(servers, dict)
    assert "gdb" not in servers


def test_update_config_invalid_nested_type() -> None:
    config: dict[str, object] = {"mcp": "not-a-dict"}
    with pytest.raises(ValueError):
        update_mcp_config(config, ("mcp", "servers"), server_name="gdb", uninstall=False)


def test_select_install_targets_codex_only() -> None:
    selected = select_install_targets(["Codex"])
    assert len(selected) == 1
    assert selected[0].name == "Codex"


def test_select_install_targets_unknown() -> None:
    with pytest.raises(ValueError):
        select_install_targets(["NoSuchClient"])


def test_select_install_targets_linux_matrix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    selected = select_install_targets(None)
    names = {target.name for target in selected}
    assert "Codex" in names
    assert "VS Code" in names
    assert "Claude Code" in names
    assert len(names) >= 20


def test_vscode_uses_nested_keypath(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    vscode = next(target for target in select_install_targets(None) if target.name == "VS Code")
    assert vscode.key_path == ("mcp", "servers")
