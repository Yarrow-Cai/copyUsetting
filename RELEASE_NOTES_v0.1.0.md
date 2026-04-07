# DevToolsBackup v0.1.0 Release Notes

发布日期：2026-04-07

## 本次发布亮点

### 1. 全面重构 GUI 布局
- 主界面调整为“顶部控制区 + 全宽配置表 + 详情面板”结构
- 优先保证配置文件路径可见，不再被侧栏严重挤压
- 工具筛选、备份目录和操作按钮会根据窗口宽度自动换行

### 2. 小屏可用性明显提升
- 配置管理页新增整页纵向滚动条
- 支持鼠标滚轮滚动整个配置页
- 配置表保留横向滚动条，便于查看超长路径

### 3. 配置查看与复制体验增强
- 列表直接展示：工具 / 源配置文件 / 备份路径 / 状态
- 选中项后，下方详情面板显示完整路径
- 支持直接选择文本和一键复制路径

### 4. 日志与运行体验优化
- 运行日志移到独立标签页，不再占用主操作区域
- 备份/恢复过程的进度与状态展示更清晰
- 修复后台线程直接更新 Tk UI 的隐患，提升稳定性

### 5. 发布构建更安全
- `build.bat` 默认使用 `backup_config.example.json` 打包
- 避免发布 EXE 时误带入本地私有 `backup_config.json`
- 如需打包本地私有配置，需显式使用 `build.bat --local-config`

## 发布内容
- `DevToolsBackup.exe`
- `backup_config.example.json`
- 本说明文档

## 使用说明
1. 下载并解压 zip 包
2. 运行 `DevToolsBackup.exe`
3. 如需自定义备份项，可复制 `backup_config.example.json` 为 `backup_config.json` 后再修改

## 适用场景
- Windows 开发工具配置备份与恢复
- 小屏幕设备上的配置文件选择与查看
- Claude Code / Codex / Zed / CLIProxyAPI / OpenCode / Kimi / copyUSetting 配置管理
