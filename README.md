# JSON文件复制工具

根据JSON配置文件自动复制文件到目标文件夹，支持替换复制（覆盖已存在的文件）。

## 使用方法

### 基本用法

```bash
python file_copier.py config.json
```

### 试运行模式（只显示操作，不实际复制）

```bash
python file_copier.py config.json --dry-run
```

### 指定默认输出目录

当使用简单列表格式时，需要指定输出目录：

```bash
python file_copier.py config.json --output-dir D:/backup
```

## JSON配置格式

支持三种格式：

### 1. 对象列表格式（推荐）

```json
[
    {"src": "C:/path/to/file1.txt", "dst": "D:/backup/file1.txt"},
    {"src": "C:/path/to/file2.txt", "dst": "D:/backup/file2.txt"}
]
```

### 2. 键值对格式

```json
{
    "C:/path/to/file1.txt": "D:/backup/file1.txt",
    "C:/path/to/file2.txt": "D:/backup/file2.txt"
}
```

### 3. 简单列表格式

```json
[
    "C:/path/to/file1.txt",
    "C:/path/to/file2.txt"
]
```

> 使用此格式时需要配合 `--output-dir` 参数，文件名会保持不变。

## 功能特点

- ✅ 自动创建目标目录
- ✅ 支持替换复制（覆盖已有文件）
- ✅ 试运行模式（--dry-run）
- ✅ 详细的操作日志
- ✅ 支持相对路径和绝对路径
- ✅ 支持多种JSON配置格式

## 开发工具备份工具配置

仓库中的 `backup_config.json` 视为**本地私有配置**，已加入 `.gitignore`，不会提交到仓库。

如果你要自定义 `backup_tool.py` / `DevToolsBackup.exe` 的备份清单，可先复制示例模板：

```bat
copy backup_config.example.json backup_config.json
```

程序会优先加载本地 `backup_config.json`；如果不存在，则自动回退到仓库内的 `backup_config.example.json`。

当前示例模板已包含 Claude Code、Codex、Zed、CLIProxyAPI、OpenCode、Kimi 以及 `copyUSetting` 自身配置的备份项。

其中 `copyUSetting` 配置支持使用 `%APP_ROOT%`（或 `%COPYUSETTING_ROOT%`）指向当前程序所在目录，用于备份同目录下的 `backup_config.json`。

## 示例

### 复制Windows系统文件到备份目录

```bash
python file_copier.py example_config.json
```

### 查看将要执行的操作（不实际复制）

```bash
python file_copier.py config.json --dry-run
```
