from gdb_mcp.cli import _build_parser


def test_cli_subcommands() -> None:
    parser = _build_parser()
    action = next(
        a for a in parser._actions if getattr(a, "choices", None) is not None
    )
    subcommands = sorted(action.choices.keys())
    assert subcommands == [
        "config",
        "doctor",
        "install",
        "uninstall",
    ]
