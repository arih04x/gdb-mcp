from gdb_mcp.parsing import parse_backtrace_frames, parse_breakpoints, parse_mi_records, parse_mi_streams, parse_registers


def test_parse_backtrace_frames() -> None:
    output = """#0  function_that_crashes () at /tmp/crash.c:7
#1  0x000055671aafd1e4 in function_with_args (a=15, b=30) at /tmp/crash.c:13"""
    frames = parse_backtrace_frames(output)
    assert len(frames) == 2
    assert frames[0]["index"] == 0
    assert frames[0]["function"] == "function_that_crashes"
    assert frames[0]["file"] == "/tmp/crash.c"
    assert frames[0]["line"] == 7
    assert frames[1]["address"] == "0x000055671aafd1e4"


def test_parse_registers() -> None:
    output = """rip            0x555f6bb57151      0x555f6bb57151 <main+8>
rax            0x0                 0"""
    registers = parse_registers(output)
    assert registers["rip"]["value"] == "0x555f6bb57151"
    assert "<main+8>" in registers["rip"]["detail"]
    assert registers["rax"]["value"] == "0x0"


def test_parse_registers_with_underscore_names() -> None:
    output = """fs_base        0x7f3068c39740      139845892806464
gs_base        0x0                 0"""
    registers = parse_registers(output)
    assert registers["fs_base"]["value"] == "0x7f3068c39740"
    assert registers["gs_base"]["detail"] == "0"


def test_parse_breakpoints() -> None:
    output = """Num     Type           Disp Enb Address            What
1       breakpoint     keep y   0x000055671aafd1fa in main at /tmp/crash.c:18
2       breakpoint     keep n   0x000055671aafd191 in function_that_crashes at /tmp/crash.c:6"""
    items = parse_breakpoints(output)
    assert len(items) == 2
    assert items[0]["number"] == 1
    assert items[0]["enabled"] is True
    assert items[0]["file"] == "/tmp/crash.c"
    assert items[1]["enabled"] is False


def test_parse_breakpoints_empty() -> None:
    assert parse_breakpoints("No breakpoints or watchpoints.") == []


def test_parse_breakpoints_wrapped_location() -> None:
    output = """Num     Type           Disp Enb Address            What
1       breakpoint     keep y   0x000056317a1e91b8 in function_with_args
                                                   at /tmp/crash.c:11"""
    items = parse_breakpoints(output)
    assert len(items) == 1
    assert items[0]["number"] == 1
    assert items[0]["file"] == "/tmp/crash.c"
    assert items[0]["line"] == 11


def test_parse_breakpoints_with_hit_count_suffix() -> None:
    output = """Num     Type           Disp Enb Address            What
1       breakpoint     keep y   0x0000560ebf5991fa in main at /tmp/crash.c:18 breakpoint already hit 1 time"""
    items = parse_breakpoints(output)
    assert len(items) == 1
    assert items[0]["number"] == 1
    assert items[0]["file"] == "/tmp/crash.c"
    assert items[0]["line"] == 18


def test_parse_mi_records_with_result_and_notify() -> None:
    output = """=thread-group-added,id="i1"
^done,bkpt={number="1",type="breakpoint"}"""
    records = parse_mi_records(output)
    assert len(records) == 2
    assert records[0]["type"] == "notify"
    assert records[0]["message"] == "thread-group-added"
    assert records[1]["type"] == "result"
    assert records[1]["message"] == "done"
    assert records[1]["payload"]["bkpt"]["number"] == "1"


def test_parse_mi_records_ignores_non_mi_lines() -> None:
    output = """Reading symbols from a.out...
(gdb)
Breakpoint 1 at 0x401136: file test.c, line 5."""
    assert parse_mi_records(output) == []


def test_parse_mi_records_excludes_streams() -> None:
    output = '~"GNU gdb\\n"\n^done'
    records = parse_mi_records(output)
    assert len(records) == 1
    assert records[0]["type"] == "result"


def test_parse_mi_streams_only_stream_records() -> None:
    output = '~"GNU gdb\\n"\n&"warning\\n"\n^done'
    streams = parse_mi_streams(output)
    assert len(streams) == 2
    assert streams[0]["type"] == "console"
    assert streams[1]["type"] == "log"


def test_parse_mi_streams_merges_adjacent_same_type_records() -> None:
    output = '~"GNU gdb\\n"\n~"Copyright\\n"\n^done'
    streams = parse_mi_streams(output)
    assert len(streams) == 1
    assert streams[0]["type"] == "console"
    assert streams[0]["payload"] == "GNU gdb\nCopyright\n"
