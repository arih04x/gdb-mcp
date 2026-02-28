from gdb_mcp.parsing import extract_line_range, parse_info_line, parse_info_source


def test_parse_info_line() -> None:
    output = 'Line 17 of "crash.c" starts at address 0x1149 <main+0> and ends at 0x1155 <main+12>.'
    parsed = parse_info_line(output)
    assert parsed == ("crash.c", 17)


def test_parse_info_source() -> None:
    output = "Current source file is /tmp/crash.c\nCompilation directory is /tmp"
    parsed = parse_info_source(output)
    assert parsed == "/tmp/crash.c"


def test_extract_line_range() -> None:
    output = """
10      int number = 5;
11      if (argc > 1) {
12          number = atoi(argv[1]);
13      }
"""
    parsed = extract_line_range(output)
    assert parsed == (10, 13)


def test_extract_line_range_none() -> None:
    assert extract_line_range("No source file available") is None
