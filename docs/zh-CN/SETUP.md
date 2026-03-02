# Windows

本页解决一件事：让 `uv run gdb-mcp doctor` 在 Windows 上能找到可用的 `gdb`。

`gdb-mcp` 支持两种方式定位 gdb：

- **PATH**：系统能 `where gdb` 找到 `gdb.exe`
- **显式路径（推荐）**：在 `config.json` 里配置 `gdb_path`（或设置环境变量 `GDB_MCP_GDB_PATH`）

显式路径的好处：不需要修改系统 PATH，也不会被不同终端/客户端的环境隔离影响。

## 0) 先看 doctor 输出

在项目根目录（`mcp_server/gdb-mcp`）运行：

```powershell
uv run gdb-mcp doctor
```

如果你看到：

- `gdb_resolved: null`

说明当前系统找不到 gdb，需要按下面步骤安装/配置。

## 1) 推荐方案：winget + MSYS2（装 mingw 版 gdb）

### 1.1 安装 MSYS2

```powershell
winget install --id MSYS2.MSYS2 -e --accept-package-agreements --accept-source-agreements
```

默认通常会安装到 `C:\msys64`。

### 1.2 用 MSYS2 安装 gdb

你可以走两种方式：

**方式 A（推荐）：让 doctor 自动安装并写入 config.json**

```powershell
uv run gdb-mcp doctor --fix
```

它会尝试：

- `winget` 安装 MSYS2（如果未安装）
- `pacman` 安装 `mingw-w64-ucrt-x86_64-gdb`
- 自动把 `gdb.exe` 的绝对路径写入 `config.json` 的 `gdb_path`

然后你再运行：

```powershell
uv run gdb-mcp doctor
```

应该能看到 `gdb_resolved` 变成一个 `...\\gdb.exe` 的绝对路径。

**方式 B：手动在 MSYS2 UCRT64 终端执行 pacman**

1) 打开开始菜单的 **MSYS2 UCRT64**（不是 MSYS2 MSYS）

2) 运行：

```bash
pacman -Sy --noconfirm --needed mingw-w64-ucrt-x86_64-gdb
```

3) 然后把 gdb 路径写进 `mcp_server/gdb-mcp/config.json`：

```json
{
	"gdb_path": "C:/msys64/ucrt64/bin/gdb.exe"
}
```

再回到 PowerShell 运行：

```powershell
uv run gdb-mcp doctor
```

## 2) 仅临时覆盖：用环境变量指定 gdb

如果你不想改 `config.json`，也可以临时指定：

```powershell
$env:GDB_MCP_GDB_PATH = "C:\\msys64\\ucrt64\\bin\\gdb.exe"
uv run gdb-mcp doctor
```

这只对当前终端会话有效。

## 3) 常见问题

### 3.1 doctor --fix 安装了 MSYS2，但还是找不到 gdb.exe

可能原因：

- MSYS2 安装目录不是 `C:\msys64`（可设置 `MSYS2_ROOT` 环境变量再重试）
- pacman 需要你先做一次升级/初始化

你可以：

1) 打开 MSYS2 UCRT64 终端
2) 手动执行 `pacman -Sy --needed mingw-w64-ucrt-x86_64-gdb`
3) 把 `gdb_path` 写入 `config.json`

### 3.2 需要改系统 PATH 吗？

不需要。推荐直接用 `config.json:gdb_path` 或 `GDB_MCP_GDB_PATH`。