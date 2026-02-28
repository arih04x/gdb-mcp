import pytest

from gdb_mcp.install import update_mcp_config


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
