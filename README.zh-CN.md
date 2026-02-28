# gdb-mcp

[English](README.md) | 简体中文

<div align="center">
  <img src="asset/gdb.svg" alt="gdb-mcp logo" width="140"/>
  <h3>面向 AI 调试流程的 GDB MCP Server</h3>
  <p>将常用 GDB 能力封装为 MCP 工具，便于助手调用和自动化集成。</p>

  <p>
    <img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-blue.svg" />
    <img alt="GDB" src="https://img.shields.io/badge/GDB-required-red.svg" />
    <img alt="MCP" src="https://img.shields.io/badge/MCP-enabled-green.svg" />
    <img alt="License MIT" src="https://img.shields.io/badge/license-MIT-lightgrey.svg" />
  </p>
</div>

## 项目简介

`gdb-mcp` 是一个 Python 实现的 MCP Server，将常见 GDB 调试操作暴露为 MCP 工具。
适用于：

- AI 辅助的交互式调试
- 可复用的本地调试流程
- 与 MCP 客户端的轻量集成

## 核心能力

- 多会话 GDB 管理
- 加载程序 / 附加进程 / 加载 core dump
- 断点全生命周期与执行控制（`set/list/toggle/delete`、`continue` / `step` / `next`）
- 运行时信息查看：回溯帧、寄存器、内存、表达式（含结构化字段）
- 轻量接入 `pygdbmi` 做 GDB/MI 解析（`gdb_command` 在存在 MI 输出时返回 `miRecords`）
- MCP 配置安装（`gdb-mcp install`）

结构化优先返回策略：
- 当结构化解析成功（如 `miRecords` / `frames` / `registers` / `breakpoints`）时，不再返回对应原始文本字段。
- 仅在结构化解析无有效结果时，才保留原始文本作为兜底。

## 快速开始

环境要求：

- Python 3.11+
- `uv`
- `gdb`

安装并启动：

```bash
uv sync --extra dev
uv run gdb-mcp
```

## 运行模式与配置

`gdb-mcp` 运行时配置读取顺序：

1. `GDB_MCP_CONFIG`（支持相对路径）
2. 项目根目录默认 `./config.json`

环境变量可覆盖配置文件中的值：

- `GDB_MODE=default|advanced`
- `GDB_MCP_MAX_OUTPUT_CHARS=<int>`

可通过 `gdb_get_capabilities` 查看当前生效能力与策略。
`default` 模式下高级工具不会出现在 `tools/list`。

模式定位：

- `default`：提供稳定、常用的基础调试能力，足以覆盖大多数日常调试任务。
- `advanced`：在 `default` 基础上提供可定制的深度分析流程，服务复杂问题与更深层的 Pwn 场景需求。

## CLI 命令

```bash
uv run gdb-mcp doctor
uv run gdb-mcp install
uv run gdb-mcp install --client Codex
uv run gdb-mcp config
uv run gdb-mcp uninstall
```

`install` 现已支持三平台全客户端矩阵（风格对齐 arida-pro-mcp），并可通过 `--client` 只安装指定客户端。

## 工具列表

- `gdb_start`
- `gdb_get_capabilities`
- `gdb_load`
- `gdb_command`
- `gdb_terminate`
- `gdb_list_sessions`
- `gdb_set_breakpoint`
- `gdb_list_breakpoints`
- `gdb_delete_breakpoints`
- `gdb_toggle_breakpoints`
- `gdb_continue`
- `gdb_step`
- `gdb_next`
- `gdb_backtrace`
- `gdb_print`
- `gdb_examine`
- `gdb_info_registers`
- `gdb_attach`（仅 advanced）
- `gdb_load_core`（仅 advanced）
- `gdb_set_watchpoint`（仅 advanced）
- `gdb_info_threads`（仅 advanced）
- `gdb_thread_select`（仅 advanced）
- `gdb_frame_select`（仅 advanced）
- `gdb_collect_crash_report`（仅 advanced）

## 示例

见 [examples/USAGE.md](examples/USAGE.md)。

构建示例程序：

```bash
cd examples
gcc -g -O0 crash.c -o crash
```

## 测试

```bash
uv run pytest -q
```

## 常见问题

- 找不到 `gdb`：先执行 `uv run gdb-mcp doctor`，安装 `gdb` 后再运行。
- 工具调用失败：检查目标路径和 `sessionId` 是否正确。
- 客户端未生效：执行 `gdb-mcp install` 后重启 MCP 客户端。
