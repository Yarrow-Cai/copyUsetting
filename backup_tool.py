#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""开发工具配置备份工具"""

from __future__ import annotations

import json
import os
import shutil
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

USER_CONFIG_FILE = "backup_config.json"
DEFAULT_CONFIG_FILE = "backup_config.example.json"
TOOL_LABELS = {
    "claude_code": "Claude Code",
    "codex": "Codex",
    "zed": "Zed",
    "cliproxyapi": "CLIProxyAPI",
    "opencode": "OpenCode",
    "kimi": "Kimi",
    "copyusersetting": "copyUSetting",
}


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", app_root()))
    return base_path / relative_path


def find_config_path() -> Path:
    for candidate in (USER_CONFIG_FILE, DEFAULT_CONFIG_FILE):
        for config_path in (app_root() / candidate, resource_path(candidate)):
            if config_path.exists():
                return config_path
    return app_root() / USER_CONFIG_FILE


def expand_path(raw_path: str) -> str:
    expanded = raw_path
    custom_vars = {
        "%APP_ROOT%": str(app_root()),
        "%COPYUSETTING_ROOT%": str(app_root()),
    }
    for placeholder, actual in custom_vars.items():
        expanded = expanded.replace(placeholder, actual)
    return os.path.normpath(os.path.expanduser(os.path.expandvars(expanded)))


def default_backup_dir() -> str:
    one_drive_dir = Path.home() / "OneDrive" / "附件" / "bf"
    if (Path.home() / "OneDrive").exists():
        return str(one_drive_dir)
    return str(Path.home() / "bf")


class BackupTool:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("开发工具配置备份工具")
        self.root.geometry("980x680")
        self.root.minsize(860, 560)

        self.items: list[dict] = []
        self.visible_ids: list[str] = []
        self.tool_vars: dict[str, tk.BooleanVar] = {}
        self.dest_var = tk.StringVar(value=default_backup_dir())
        self.status_var = tk.StringVar(value="就绪")
        self.config_source = USER_CONFIG_FILE
        self.config_source_label = "本地配置"

        self.load_config()
        self.create_ui()
        self.refresh()
        if self.config_source == DEFAULT_CONFIG_FILE:
            self.log(f"未找到本地 {USER_CONFIG_FILE}，当前使用 {DEFAULT_CONFIG_FILE} 示例模板。")

    def load_config(self) -> None:
        config_path = find_config_path()
        self.config_source = config_path.name
        self.config_source_label = "本地配置" if config_path.name == USER_CONFIG_FILE else "示例模板"
        try:
            with config_path.open("r", encoding="utf-8") as f:
                raw_items = json.load(f)
        except Exception as exc:
            messagebox.showerror("错误", f"加载配置失败:\n{exc}")
            raw_items = []

        normalized = []
        for item in raw_items:
            tool = item.get("tool", "")
            src_template = item.get("src", "")
            dst = item.get("dst", "")
            normalized.append(
                {
                    "tool": tool,
                    "src_template": src_template,
                    "src": expand_path(src_template),
                    "dst": dst.replace("\\", "/"),
                }
            )
        self.items = normalized

    def create_ui(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="开发工具配置备份工具", font=("微软雅黑", 16, "bold")).pack(anchor="center")
        ttk.Label(top, text="备份/恢复 Claude Code、Codex、Zed、CLIProxyAPI、OpenCode、Kimi、copyUSetting 配置", foreground="#666666").pack(anchor="center", pady=(4, 0))

        main = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        main.pack(fill="both", expand=True)

        tools_frame = ttk.LabelFrame(main, text="工具选择", padding=10)
        tools_frame.pack(fill="x", pady=(0, 10))
        for col, tool in enumerate(TOOL_LABELS):
            var = tk.BooleanVar(value=True)
            self.tool_vars[tool] = var
            ttk.Checkbutton(tools_frame, text=TOOL_LABELS[tool], variable=var, command=self.refresh).grid(row=0, column=col, padx=12, sticky="w")

        list_frame = ttk.LabelFrame(main, text="源文件列表", padding=5)
        list_frame.pack(fill="both", expand=True)

        columns = ("tool", "src", "dst", "status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=16)
        self.tree.heading("tool", text="工具")
        self.tree.heading("src", text="源文件")
        self.tree.heading("dst", text="备份相对路径")
        self.tree.heading("status", text="状态")
        self.tree.column("tool", width=120, anchor="center")
        self.tree.column("src", width=470)
        self.tree.column("dst", width=260)
        self.tree.column("status", width=90, anchor="center")

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        bottom = ttk.Frame(main)
        bottom.pack(fill="x", pady=(10, 0))

        dest_frame = ttk.Frame(bottom)
        dest_frame.pack(fill="x")
        ttk.Label(dest_frame, text="备份目录:").pack(side="left")
        ttk.Entry(dest_frame, textvariable=self.dest_var, width=70).pack(side="left", padx=6, fill="x", expand=True)
        ttk.Button(dest_frame, text="浏览", command=self.browse_dest).pack(side="left")

        button_frame = ttk.Frame(bottom)
        button_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(button_frame, text="刷新", command=self.refresh).pack(side="left", padx=(0, 6))
        ttk.Button(button_frame, text="全选", command=self.select_all).pack(side="left", padx=6)
        ttk.Button(button_frame, text="取消选择", command=self.clear_selection).pack(side="left", padx=6)
        ttk.Button(button_frame, text="开始备份", command=self.start_backup).pack(side="left", padx=6)
        ttk.Button(button_frame, text="恢复配置", command=self.start_restore).pack(side="left", padx=6)

        self.progress = ttk.Progressbar(bottom, mode="determinate")
        self.progress.pack(fill="x", pady=(10, 0))

        log_frame = ttk.LabelFrame(bottom, text="日志", padding=5)
        log_frame.pack(fill="both", expand=False, pady=(10, 0))
        self.log_box = scrolledtext.ScrolledText(log_frame, height=8, wrap="word", font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True)

        status = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status.pack(fill="x", side="bottom")

    def browse_dest(self) -> None:
        initial_dir = self.dest_var.get()
        chosen = filedialog.askdirectory(initialdir=initial_dir if initial_dir else str(Path.home()))
        if chosen:
            self.dest_var.set(chosen)

    def selected_tools(self) -> set[str]:
        return {tool for tool, var in self.tool_vars.items() if var.get()}

    def refresh(self) -> None:
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        enabled_tools = self.selected_tools()
        visible_count = 0
        exists_count = 0

        for idx, item in enumerate(self.items):
            if item["tool"] not in enabled_tools:
                continue

            exists = os.path.exists(item["src"])
            status_text = "✓ 存在" if exists else "✗ 缺失"
            tag = "exists" if exists else "missing"
            self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(TOOL_LABELS.get(item["tool"], item["tool"]), item["src"], item["dst"], status_text),
                tags=(tag,),
            )
            visible_count += 1
            if exists:
                exists_count += 1

        self.tree.tag_configure("exists", foreground="green")
        self.tree.tag_configure("missing", foreground="red")
        self.status_var.set(f"已显示 {visible_count} 项，存在 {exists_count} 项，当前配置：{self.config_source_label}")

    def select_all(self) -> None:
        self.tree.selection_set(self.tree.get_children())

    def clear_selection(self) -> None:
        self.tree.selection_remove(self.tree.selection())

    def log(self, text: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{timestamp}] {text}\n")
        self.log_box.see("end")
        self.root.update_idletasks()

    def copy_file(self, src: str, dst: str) -> tuple[bool, str]:
        try:
            if not os.path.isfile(src):
                return False, "源文件不存在"
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return True, "成功"
        except Exception as exc:
            return False, str(exc)

    def start_backup(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要备份的文件。")
            return
        threading.Thread(target=self.do_backup, args=(selected,), daemon=True).start()

    def do_backup(self, selected: tuple[str, ...]) -> None:
        base_dir = self.dest_var.get().strip()
        if not base_dir:
            messagebox.showwarning("提示", "请先选择备份目录。")
            return

        total = len(selected)
        success = 0
        failed = 0
        self.log("开始备份...")

        for i, row_id in enumerate(selected, start=1):
            item = self.items[int(row_id)]
            target = str(Path(base_dir) / Path(item["dst"]))
            ok, msg = self.copy_file(item["src"], target)
            if ok:
                success += 1
                self.log(f"✓ {item['src']} -> {target}")
            else:
                failed += 1
                self.log(f"✗ {item['src']} : {msg}")
            self.progress["value"] = i / total * 100
            self.status_var.set(f"备份中 {i}/{total}")
            self.root.update_idletasks()

        self.progress["value"] = 0
        self.status_var.set(f"备份完成：成功 {success}，失败 {failed}")
        messagebox.showinfo("完成", f"备份完成\n成功: {success}\n失败: {failed}")

    def start_restore(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要恢复的文件。")
            return
        if not messagebox.askyesno("确认", "恢复会覆盖本机现有配置，确定继续吗？"):
            return
        threading.Thread(target=self.do_restore, args=(selected,), daemon=True).start()

    def do_restore(self, selected: tuple[str, ...]) -> None:
        base_dir = self.dest_var.get().strip()
        if not base_dir:
            messagebox.showwarning("提示", "请先选择备份目录。")
            return

        total = len(selected)
        success = 0
        failed = 0
        self.log("开始恢复...")

        for i, row_id in enumerate(selected, start=1):
            item = self.items[int(row_id)]
            backup_file = str(Path(base_dir) / Path(item["dst"]))
            ok, msg = self.copy_file(backup_file, item["src"])
            if ok:
                success += 1
                self.log(f"✓ {backup_file} -> {item['src']}")
            else:
                failed += 1
                self.log(f"✗ {backup_file} : {msg}")
            self.progress["value"] = i / total * 100
            self.status_var.set(f"恢复中 {i}/{total}")
            self.root.update_idletasks()

        self.progress["value"] = 0
        self.status_var.set(f"恢复完成：成功 {success}，失败 {failed}")
        messagebox.showinfo("完成", f"恢复完成\n成功: {success}\n失败: {failed}")


if __name__ == "__main__":
    root = tk.Tk()
    BackupTool(root)
    root.mainloop()
