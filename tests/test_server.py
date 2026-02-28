import pytest

from gdb_mcp.server import _normalize_arguments


def test_normalize_arguments_none() -> None:
    assert _normalize_arguments(None) is None


def test_normalize_arguments_list() -> None:
    assert _normalize_arguments(["15", "--flag"]) == ["15", "--flag"]


def test_normalize_arguments_json_string() -> None:
    assert _normalize_arguments('["15","--flag"]') == ["15", "--flag"]


def test_normalize_arguments_shell_string() -> None:
    assert _normalize_arguments('15 "a b"') == ["15", "a b"]


def test_normalize_arguments_numeric_json_scalar() -> None:
    assert _normalize_arguments("15") == ["15"]


def test_normalize_arguments_invalid_json_object() -> None:
    with pytest.raises(ValueError):
        _normalize_arguments('{"a": 1}')
