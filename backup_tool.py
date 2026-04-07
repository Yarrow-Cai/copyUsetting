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

        self.colors = {
            "bg": "#F3F6FB",
            "surface": "#FFFFFF",
            "surface_alt": "#F8FAFC",
            "border": "#D7E0EA",
            "text": "#0F172A",
            "muted": "#64748B",
            "primary": "#2563EB",
            "primary_hover": "#1D4ED8",
            "primary_soft": "#DBEAFE",
            "success": "#15803D",
            "warning": "#D97706",
            "warning_hover": "#B45309",
            "danger": "#B91C1C",
        }

        self.items: list[dict] = []
        self.tool_vars: dict[str, tk.BooleanVar] = {}
        self.tool_buttons: list[ttk.Checkbutton] = []
        self.action_buttons: list[ttk.Button] = []
        self.summary_cards: list[ttk.Frame] = []
        self._layout_job: str | None = None
        self._busy = False
        self.current_detail: dict | None = None

        self.dest_var = tk.StringVar(value=default_backup_dir())
        self.status_var = tk.StringVar(value="就绪")
        self.visible_count_var = tk.StringVar(value="0 项")
        self.exists_count_var = tk.StringVar(value="0 项")
        self.selected_count_var = tk.StringVar(value="0 项")
        self.config_badge_var = tk.StringVar(value="当前配置：-")
        self.config_source_value_var = tk.StringVar(value="-")
        self.detail_hint_var = tk.StringVar(value="请选择配置项，下方会显示完整路径并支持复制。")
        self.detail_tool_var = tk.StringVar(value="-")
        self.detail_status_var = tk.StringVar(value="-")

        self.config_source = USER_CONFIG_FILE
        self.config_source_label = "本地配置"

        self.configure_window()
        self.load_config()
        self.create_ui()
        self.refresh()
        if self.config_source == DEFAULT_CONFIG_FILE:
            self.log(f"未找到本地 {USER_CONFIG_FILE}，当前使用 {DEFAULT_CONFIG_FILE} 示例模板。")

    def configure_window(self) -> None:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        width = max(860, min(1280, screen_w - 120))
        height = max(620, min(860, screen_h - 120))
        pos_x = max(0, (screen_w - width) // 2)
        pos_y = max(0, (screen_h - height) // 2)
        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        self.root.minsize(640, 460)

    def load_config(self) -> None:
        config_path = find_config_path()
        self.config_source = config_path.name
        self.config_source_label = "本地配置" if config_path.name == USER_CONFIG_FILE else "示例模板"
        self.config_badge_var.set(f"当前配置：{self.config_source_label}")
        self.config_source_value_var.set(self.config_source_label)

        try:
            with config_path.open("r", encoding="utf-8") as file:
                raw_items = json.load(file)
        except Exception as exc:
            messagebox.showerror("错误", f"加载配置失败:\n{exc}")
            raw_items = []

        normalized: list[dict] = []
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

    def setup_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        base_font = ("微软雅黑", 10)
        title_font = ("微软雅黑", 18, "bold")
        metric_font = ("微软雅黑", 13, "bold")
        mono_font = ("Consolas", 10)

        self.root.configure(bg=self.colors["bg"])
        style.configure(".", font=base_font)
        style.configure("App.TFrame", background=self.colors["bg"])
        style.configure("Surface.TFrame", background=self.colors["surface"])
        style.configure("Panel.TFrame", background=self.colors["surface_alt"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"])
        style.configure("Surface.TLabel", background=self.colors["surface"], foreground=self.colors["text"])
        style.configure("Panel.TLabel", background=self.colors["surface_alt"], foreground=self.colors["text"])
        style.configure("Title.TLabel", background=self.colors["surface"], foreground=self.colors["text"], font=title_font)
        style.configure("Subtitle.TLabel", background=self.colors["surface"], foreground=self.colors["muted"])
        style.configure("Meta.TLabel", background=self.colors["surface_alt"], foreground=self.colors["muted"], font=("微软雅黑", 9))
        style.configure("Metric.TLabel", background=self.colors["surface_alt"], foreground=self.colors["text"], font=metric_font)
        style.configure("Hint.TLabel", background=self.colors["surface"], foreground=self.colors["muted"], font=("微软雅黑", 9))
        style.configure("Status.TLabel", background=self.colors["bg"], foreground=self.colors["muted"])
        style.configure("Badge.TLabel", background=self.colors["primary_soft"], foreground=self.colors["primary"], padding=(10, 6), font=("微软雅黑", 9, "bold"))
        style.configure("Tool.TCheckbutton", background=self.colors["surface"], foreground=self.colors["text"])
        style.map("Tool.TCheckbutton", background=[("active", self.colors["surface"]), ("selected", self.colors["surface"])])
        style.configure("TLabelframe", background=self.colors["surface"], borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=self.colors["surface"], foreground=self.colors["text"], font=("微软雅黑", 10, "bold"))
        style.configure("TEntry", fieldbackground=self.colors["surface"], padding=8)

        style.configure(
            "Accent.TButton",
            background=self.colors["primary"],
            foreground="#FFFFFF",
            padding=(12, 8),
            borderwidth=0,
        )
        style.map("Accent.TButton", background=[("active", self.colors["primary_hover"]), ("disabled", self.colors["border"])])
        style.configure(
            "Warning.TButton",
            background=self.colors["warning"],
            foreground="#FFFFFF",
            padding=(12, 8),
            borderwidth=0,
        )
        style.map("Warning.TButton", background=[("active", self.colors["warning_hover"]), ("disabled", self.colors["border"])])
        style.configure(
            "Secondary.TButton",
            background=self.colors["surface_alt"],
            foreground=self.colors["text"],
            padding=(12, 8),
            borderwidth=1,
        )
        style.map("Secondary.TButton", background=[("active", "#E8EEF7"), ("disabled", self.colors["surface_alt"])])
        style.configure(
            "Ghost.TButton",
            background=self.colors["surface"],
            foreground=self.colors["primary"],
            padding=(8, 4),
            borderwidth=0,
        )
        style.map("Ghost.TButton", background=[("active", self.colors["primary_soft"])])

        style.configure("TNotebook", background=self.colors["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 8), background=self.colors["surface_alt"], foreground=self.colors["muted"])
        style.map("TNotebook.Tab", background=[("selected", self.colors["surface"]), ("active", self.colors["surface"])], foreground=[("selected", self.colors["text"])])

        style.configure(
            "Treeview",
            background=self.colors["surface"],
            fieldbackground=self.colors["surface"],
            foreground=self.colors["text"],
            rowheight=28,
            borderwidth=0,
            relief="flat",
        )
        style.map("Treeview", background=[("selected", self.colors["primary_soft"])], foreground=[("selected", self.colors["text"])])
        style.configure(
            "Treeview.Heading",
            background="#EAF0F7",
            foreground=self.colors["text"],
            font=("微软雅黑", 10, "bold"),
            padding=(8, 6),
            relief="flat",
        )
        style.map("Treeview.Heading", background=[("active", "#DDE7F3")])
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#E2E8F0",
            background=self.colors["primary"],
            lightcolor=self.colors["primary"],
            darkcolor=self.colors["primary"],
        )

        self.mono_font = mono_font

    def create_ui(self) -> None:
        self.setup_styles()

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        container = ttk.Frame(self.root, style="App.TFrame", padding=16)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        header = ttk.Frame(container, style="Surface.TFrame", padding=(20, 16))
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        title_group = ttk.Frame(header, style="Surface.TFrame")
        title_group.grid(row=0, column=0, sticky="w")
        ttk.Label(title_group, text="开发工具配置备份工具", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_group,
            text="这次改成“顶部控制区 + 全宽配置表 + 详情面板”，优先保证配置文件看得见。",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(header, textvariable=self.config_badge_var, style="Badge.TLabel").grid(row=0, column=1, sticky="ne")

        self.notebook = ttk.Notebook(container)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        self.config_tab = ttk.Frame(self.notebook, style="App.TFrame", padding=12)
        self.log_tab = ttk.Frame(self.notebook, style="App.TFrame", padding=12)
        self.notebook.add(self.config_tab, text="配置管理")
        self.notebook.add(self.log_tab, text="运行日志")

        self.config_tab.columnconfigure(0, weight=1)
        self.config_tab.rowconfigure(0, weight=1)

        self.config_canvas = tk.Canvas(
            self.config_tab,
            background=self.colors["bg"],
            highlightthickness=0,
            relief="flat",
        )
        self.config_scrollbar = ttk.Scrollbar(self.config_tab, orient="vertical", command=self.config_canvas.yview)
        self.config_canvas.configure(yscrollcommand=self.config_scrollbar.set)
        self.config_canvas.grid(row=0, column=0, sticky="nsew")
        self.config_scrollbar.grid(row=0, column=1, sticky="ns")

        self.config_content = ttk.Frame(self.config_canvas, style="App.TFrame", padding=(0, 0, 6, 0))
        self.config_content.columnconfigure(0, weight=1)
        self.config_content.rowconfigure(1, weight=1)
        self.config_canvas_window = self.config_canvas.create_window((0, 0), window=self.config_content, anchor="nw")

        self.create_control_area()
        self.create_workspace_area()
        self.create_log_area()

        self.config_content.bind("<Configure>", self.on_config_content_configure)
        self.config_canvas.bind("<Configure>", self.on_config_canvas_configure)

        footer = ttk.Frame(container, style="App.TFrame", padding=(0, 12, 0, 0))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(footer, mode="determinate")
        self.progress.grid(row=0, column=0, sticky="ew")
        ttk.Label(footer, textvariable=self.status_var, style="Status.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.root.bind("<Configure>", self.on_window_configure)
        self.root.bind_all("<MouseWheel>", self.on_global_mousewheel, add="+")
        self.root.after(0, self.apply_responsive_layout)

    def create_control_area(self) -> None:
        controls = ttk.LabelFrame(self.config_content, text="筛选与操作", padding=12)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        controls.columnconfigure(0, weight=1)
        self.controls_card = controls

        self.summary_grid = ttk.Frame(controls, style="Surface.TFrame")
        self.summary_grid.grid(row=0, column=0, sticky="ew")

        summary_specs = [
            ("已显示", self.visible_count_var),
            ("存在", self.exists_count_var),
            ("已选中", self.selected_count_var),
            ("配置来源", self.config_source_value_var),
        ]
        for title, variable in summary_specs:
            card = ttk.Frame(self.summary_grid, style="Panel.TFrame", padding=(12, 10))
            ttk.Label(card, text=title, style="Meta.TLabel").grid(row=0, column=0, sticky="w")
            ttk.Label(card, textvariable=variable, style="Metric.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 0))
            self.summary_cards.append(card)

        filters_wrap = ttk.Frame(controls, style="Surface.TFrame")
        filters_wrap.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        filters_wrap.columnconfigure(0, weight=1)
        ttk.Label(filters_wrap, text="工具筛选", style="Surface.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(filters_wrap, text="取消勾选即可临时隐藏对应工具的配置项。", style="Hint.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 8))
        self.filters_grid = ttk.Frame(filters_wrap, style="Surface.TFrame")
        self.filters_grid.grid(row=2, column=0, sticky="ew")

        for tool in TOOL_LABELS:
            var = tk.BooleanVar(value=True)
            self.tool_vars[tool] = var
            button = ttk.Checkbutton(
                self.filters_grid,
                text=TOOL_LABELS[tool],
                variable=var,
                command=self.refresh,
                style="Tool.TCheckbutton",
            )
            self.tool_buttons.append(button)

        destination_wrap = ttk.Frame(controls, style="Surface.TFrame")
        destination_wrap.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        destination_wrap.columnconfigure(0, weight=1)
        ttk.Label(destination_wrap, text="备份目录", style="Surface.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(destination_wrap, text="备份会按配置中的相对路径写入到该目录。", style="Hint.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 8))

        self.dest_grid = ttk.Frame(destination_wrap, style="Surface.TFrame")
        self.dest_grid.grid(row=2, column=0, sticky="ew")
        self.dest_entry = ttk.Entry(self.dest_grid, textvariable=self.dest_var)
        self.browse_button = ttk.Button(self.dest_grid, text="浏览目录", command=self.browse_dest, style="Secondary.TButton")

        actions_wrap = ttk.Frame(controls, style="Surface.TFrame")
        actions_wrap.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        actions_wrap.columnconfigure(0, weight=1)
        ttk.Label(actions_wrap, text="常用操作", style="Surface.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(actions_wrap, text="列表保持全宽显示，操作按钮自动换行，不再占掉配置表的主要空间。", style="Hint.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 8))

        self.actions_grid = ttk.Frame(actions_wrap, style="Surface.TFrame")
        self.actions_grid.grid(row=2, column=0, sticky="ew")

        action_specs = [
            ("刷新列表", self.refresh, "Secondary.TButton"),
            ("全选当前列表", self.select_all, "Secondary.TButton"),
            ("取消当前选择", self.clear_selection, "Secondary.TButton"),
            ("开始备份", self.start_backup, "Accent.TButton"),
            ("恢复配置", self.start_restore, "Warning.TButton"),
        ]
        for text, command, style_name in action_specs:
            button = ttk.Button(self.actions_grid, text=text, command=command, style=style_name)
            self.action_buttons.append(button)

    def create_workspace_area(self) -> None:
        workspace = ttk.Frame(self.config_content, style="App.TFrame")
        workspace.grid(row=1, column=0, sticky="nsew")
        workspace.columnconfigure(0, weight=1)
        workspace.rowconfigure(0, weight=1)
        self.workspace = workspace

        list_card = ttk.LabelFrame(workspace, text="配置文件列表", padding=12)
        list_card.grid(row=0, column=0, sticky="nsew")
        list_card.columnconfigure(0, weight=1)
        list_card.rowconfigure(1, weight=1)

        ttk.Label(list_card, text="这里直接展示源配置文件和备份路径；宽度不够可用横向滚动条，高度不够可滚动整页。", style="Hint.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))

        tree_wrap = ttk.Frame(list_card, style="Surface.TFrame")
        tree_wrap.grid(row=1, column=0, sticky="nsew")
        tree_wrap.columnconfigure(0, weight=1)
        tree_wrap.rowconfigure(0, weight=1)

        columns = ("tool", "src", "dst", "status")
        self.tree = ttk.Treeview(tree_wrap, columns=columns, show="headings", selectmode="extended", height=16)
        self.tree.heading("tool", text="工具")
        self.tree.heading("src", text="源配置文件")
        self.tree.heading("dst", text="备份路径")
        self.tree.heading("status", text="状态")
        self.tree.column("tool", width=120, minwidth=90, anchor="center", stretch=False)
        self.tree.column("src", width=620, minwidth=280, anchor="w", stretch=True)
        self.tree.column("dst", width=320, minwidth=180, anchor="w", stretch=True)
        self.tree.column("status", width=90, minwidth=80, anchor="center", stretch=False)

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        detail_card = ttk.LabelFrame(workspace, text="当前选中项详情", padding=12)
        detail_card.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        detail_card.columnconfigure(0, weight=1)
        self.detail_card = detail_card

        ttk.Label(detail_card, textvariable=self.detail_hint_var, style="Hint.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))

        detail_meta = ttk.Frame(detail_card, style="Surface.TFrame")
        detail_meta.grid(row=1, column=0, sticky="ew")
        detail_meta.columnconfigure(1, weight=1)
        detail_meta.columnconfigure(3, weight=1)
        ttk.Label(detail_meta, text="工具", style="Surface.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Label(detail_meta, textvariable=self.detail_tool_var, style="Surface.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(detail_meta, text="状态", style="Surface.TLabel").grid(row=0, column=2, sticky="w", padx=(24, 8))
        ttk.Label(detail_meta, textvariable=self.detail_status_var, style="Surface.TLabel").grid(row=0, column=3, sticky="w")

        self.src_text = self.create_path_view(detail_card, row=2, title="源配置文件完整路径", button_text="复制源路径", copy_label="源路径")
        self.dst_text = self.create_path_view(detail_card, row=5, title="备份相对路径", button_text="复制备份路径", copy_label="备份路径")
        self.clear_details()

    def create_path_view(self, parent: ttk.LabelFrame, row: int, title: str, button_text: str, copy_label: str) -> tk.Text:
        header = ttk.Frame(parent, style="Surface.TFrame")
        header.grid(row=row, column=0, sticky="ew", pady=(12, 6))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text=title, style="Surface.TLabel").grid(row=0, column=0, sticky="w")
        button = ttk.Button(header, text=button_text, style="Ghost.TButton")
        button.grid(row=0, column=1, sticky="e")

        text_frame = ttk.Frame(parent, style="Surface.TFrame")
        text_frame.grid(row=row + 1, column=0, sticky="ew")
        text_frame.columnconfigure(0, weight=1)

        text = tk.Text(
            text_frame,
            height=3,
            wrap="none",
            font=self.mono_font,
            background=self.colors["surface"],
            foreground=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"],
            padx=8,
            pady=8,
            undo=False,
        )
        text.grid(row=0, column=0, sticky="ew")
        xscroll = ttk.Scrollbar(text_frame, orient="horizontal", command=text.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        text.configure(xscrollcommand=xscroll.set)
        text.bind("<Key>", self.block_text_edit)
        text.bind("<<Paste>>", self.block_text_edit)

        if copy_label == "源路径":
            self.copy_src_button = button
        else:
            self.copy_dst_button = button

        button.configure(command=lambda: self.copy_to_clipboard(self.get_text_content(text), copy_label))
        return text

    def create_log_area(self) -> None:
        self.log_tab.columnconfigure(0, weight=1)
        self.log_tab.rowconfigure(0, weight=1)

        log_card = ttk.LabelFrame(self.log_tab, text="运行日志", padding=12)
        log_card.grid(row=0, column=0, sticky="nsew")
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)
        ttk.Label(log_card, text="日志单独放在这里，避免挤压配置列表。", style="Hint.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.log_box = scrolledtext.ScrolledText(
            log_card,
            wrap="word",
            font=self.mono_font,
            background=self.colors["surface"],
            foreground=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=8,
        )
        self.log_box.grid(row=1, column=0, sticky="nsew")

    def block_text_edit(self, _event: tk.Event) -> str:
        return "break"

    def on_config_content_configure(self, _event: tk.Event | None = None) -> None:
        self.config_canvas.configure(scrollregion=self.config_canvas.bbox("all"))

    def on_config_canvas_configure(self, event: tk.Event) -> None:
        self.config_canvas.itemconfigure(self.config_canvas_window, width=event.width)

    def widget_is_descendant(self, widget: tk.Misc | None, ancestor: tk.Misc) -> bool:
        current = widget
        while current is not None:
            if current == ancestor:
                return True
            current = current.master
        return False

    def on_global_mousewheel(self, event: tk.Event) -> None:
        if self.notebook.select() != str(self.config_tab):
            return
        if self.widget_is_descendant(event.widget, self.tree):
            return
        if self.widget_is_descendant(event.widget, self.log_box):
            return
        first, last = self.config_canvas.yview()
        if first <= 0.0 and last >= 1.0:
            return
        delta = int(-event.delta / 120) if getattr(event, "delta", 0) else 0
        if delta:
            self.config_canvas.yview_scroll(delta, "units")

    def set_text_content(self, widget: tk.Text, content: str) -> None:
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.edit_reset()

    def get_text_content(self, widget: tk.Text) -> str:
        return widget.get("1.0", "end-1c")

    def on_window_configure(self, event: tk.Event) -> None:
        if event.widget is not self.root:
            return
        if self._layout_job is not None:
            self.root.after_cancel(self._layout_job)
        self._layout_job = self.root.after(80, self.apply_responsive_layout)

    def apply_responsive_layout(self) -> None:
        self._layout_job = None
        width = self.config_canvas.winfo_width()
        if width <= 1:
            width = self.root.winfo_width()
        if width <= 1:
            return

        summary_columns = 4 if width >= 1100 else 2 if width >= 760 else 1
        filter_columns = 4 if width >= 1200 else 3 if width >= 900 else 2 if width >= 650 else 1
        action_columns = 5 if width >= 1180 else 3 if width >= 820 else 2 if width >= 600 else 1
        inline_destination = width >= 820

        self.layout_summary_cards(summary_columns)
        self.layout_tool_buttons(filter_columns)
        self.layout_action_buttons(action_columns)
        self.layout_destination_controls(inline_destination)
        self.on_config_content_configure()

    def layout_summary_cards(self, columns: int) -> None:
        columns = max(1, columns)
        for col in range(4):
            self.summary_grid.columnconfigure(col, weight=0)
        for card in self.summary_cards:
            card.grid_forget()
        for index, card in enumerate(self.summary_cards):
            row = index // columns
            column = index % columns
            self.summary_grid.columnconfigure(column, weight=1)
            padx = (0, 8) if column < columns - 1 else (0, 0)
            pady = (0, 8) if row == 0 and len(self.summary_cards) > columns else (0, 0)
            card.grid(row=row, column=column, sticky="ew", padx=padx, pady=pady)

    def layout_tool_buttons(self, columns: int) -> None:
        columns = max(1, columns)
        for col in range(4):
            self.filters_grid.columnconfigure(col, weight=0)
        for button in self.tool_buttons:
            button.grid_forget()
        for index, button in enumerate(self.tool_buttons):
            row = index // columns
            column = index % columns
            self.filters_grid.columnconfigure(column, weight=1)
            button.grid(row=row, column=column, sticky="w", padx=(0, 12), pady=4)

    def layout_action_buttons(self, columns: int) -> None:
        columns = max(1, columns)
        for col in range(5):
            self.actions_grid.columnconfigure(col, weight=0)
        for button in self.action_buttons:
            button.grid_forget()
        for index, button in enumerate(self.action_buttons):
            row = index // columns
            column = index % columns
            self.actions_grid.columnconfigure(column, weight=1)
            padx = (0, 8) if column < columns - 1 else (0, 0)
            button.grid(row=row, column=column, sticky="ew", padx=padx, pady=4)

    def layout_destination_controls(self, inline: bool) -> None:
        for col in range(3):
            self.dest_grid.columnconfigure(col, weight=0)
        self.dest_entry.grid_forget()
        self.browse_button.grid_forget()
        if inline:
            self.dest_grid.columnconfigure(0, weight=1)
            self.dest_entry.grid(row=0, column=0, sticky="ew")
            self.browse_button.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        else:
            self.dest_grid.columnconfigure(0, weight=1)
            self.dest_entry.grid(row=0, column=0, sticky="ew")
            self.browse_button.grid(row=1, column=0, sticky="ew", pady=(8, 0))

    def browse_dest(self) -> None:
        initial_dir = self.dest_var.get().strip()
        chosen = filedialog.askdirectory(initialdir=initial_dir if initial_dir else str(Path.home()))
        if chosen:
            self.dest_var.set(chosen)
            self.status_var.set(f"已选择备份目录：{chosen}")

    def selected_tools(self) -> set[str]:
        return {tool for tool, var in self.tool_vars.items() if var.get()}

    def refresh(self) -> None:
        previous_selection = set(self.tree.selection())
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        enabled_tools = self.selected_tools()
        visible_count = 0
        exists_count = 0
        reselection: list[str] = []

        for index, item in enumerate(self.items):
            if item["tool"] not in enabled_tools:
                continue

            exists = os.path.exists(item["src"])
            status_text = "存在" if exists else "缺失"
            zebra_tag = "even" if visible_count % 2 == 0 else "odd"
            row_id = str(index)
            self.tree.insert(
                "",
                "end",
                iid=row_id,
                values=(
                    TOOL_LABELS.get(item["tool"], item["tool"]),
                    item["src"],
                    item["dst"],
                    status_text,
                ),
                tags=(zebra_tag,),
            )
            visible_count += 1
            if exists:
                exists_count += 1
            if row_id in previous_selection:
                reselection.append(row_id)

        self.tree.tag_configure("even", background=self.colors["surface"])
        self.tree.tag_configure("odd", background=self.colors["surface_alt"])

        if reselection:
            self.tree.selection_set(reselection)
        else:
            children = self.tree.get_children()
            if children:
                self.tree.selection_set(children[0])

        self.visible_count_var.set(f"{visible_count} 项")
        self.exists_count_var.set(f"{exists_count} 项")
        self.update_selection_state()
        self.status_var.set(f"已加载 {visible_count} 项，其中存在 {exists_count} 项。")
        self.on_tree_select()

    def update_selection_state(self) -> None:
        self.selected_count_var.set(f"{len(self.tree.selection())} 项")

    def on_tree_select(self, _event: tk.Event | None = None) -> None:
        self.update_selection_state()
        selection = self.tree.selection()
        if not selection:
            self.clear_details()
            return

        item = self.items[int(selection[0])]
        extra_hint = ""
        if len(selection) > 1:
            extra_hint = f" 已选中 {len(selection)} 项，当前只展示第一项详情。"
        self.show_item_details(item, extra_hint)

    def show_item_details(self, item: dict, extra_hint: str = "") -> None:
        exists = os.path.exists(item["src"])
        self.current_detail = item
        self.detail_tool_var.set(TOOL_LABELS.get(item["tool"], item["tool"]))
        self.detail_status_var.set("存在" if exists else "缺失")
        self.detail_hint_var.set(f"下方文本可直接选择、复制；完整路径不再在主列表里被压缩。{extra_hint}".strip())
        self.set_text_content(self.src_text, item["src"])
        self.set_text_content(self.dst_text, item["dst"])
        self.copy_src_button.configure(state="normal")
        self.copy_dst_button.configure(state="normal")

    def clear_details(self) -> None:
        self.current_detail = None
        self.detail_tool_var.set("-")
        self.detail_status_var.set("-")
        self.detail_hint_var.set("请选择配置项，下方会显示完整路径并支持复制。")
        self.set_text_content(self.src_text, "")
        self.set_text_content(self.dst_text, "")
        self.copy_src_button.configure(state="disabled")
        self.copy_dst_button.configure(state="disabled")

    def select_all(self) -> None:
        self.tree.selection_set(self.tree.get_children())
        self.on_tree_select()

    def clear_selection(self) -> None:
        self.tree.selection_remove(self.tree.selection())
        self.on_tree_select()

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        for button in self.action_buttons:
            button.configure(state=state)
        for button in self.tool_buttons:
            button.configure(state=state)
        self.dest_entry.configure(state=state)
        self.browse_button.configure(state=state)

    def log(self, text: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{timestamp}] {text}\n")
        self.log_box.see("end")

    def copy_file(self, src: str, dst: str) -> tuple[bool, str]:
        try:
            if not os.path.isfile(src):
                return False, "源文件不存在"
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return True, "成功"
        except Exception as exc:
            return False, str(exc)

    def copy_to_clipboard(self, value: str, label: str) -> None:
        if not value:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.status_var.set(f"已复制{label}。")

    def ui_call(self, callback, *args) -> None:
        self.root.after(0, lambda: callback(*args))

    def update_progress(self, current: int, total: int, action_text: str) -> None:
        self.progress["value"] = 0 if total == 0 else current / total * 100
        self.status_var.set(f"{action_text} {current}/{total}")

    def finish_operation(self, action_name: str, success: int, failed: int) -> None:
        self.progress["value"] = 0
        self.set_busy(False)
        self.refresh()
        self.status_var.set(f"{action_name}完成：成功 {success}，失败 {failed}")
        messagebox.showinfo("完成", f"{action_name}完成\n成功: {success}\n失败: {failed}")

    def start_backup(self) -> None:
        if self._busy:
            return

        selected = tuple(self.tree.selection())
        if not selected:
            messagebox.showwarning("提示", "请先选择要备份的文件。")
            return

        base_dir = self.dest_var.get().strip()
        if not base_dir:
            messagebox.showwarning("提示", "请先选择备份目录。")
            return

        self.set_busy(True)
        self.progress["value"] = 0
        self.status_var.set(f"准备备份 {len(selected)} 项...")
        self.log(f"开始备份，共 {len(selected)} 项，目标目录：{base_dir}")
        threading.Thread(target=self.do_backup, args=(selected, base_dir), daemon=True).start()

    def do_backup(self, selected: tuple[str, ...], base_dir: str) -> None:
        total = len(selected)
        success = 0
        failed = 0

        for index, row_id in enumerate(selected, start=1):
            item = self.items[int(row_id)]
            target = str(Path(base_dir) / Path(item["dst"]))
            ok, msg = self.copy_file(item["src"], target)
            if ok:
                success += 1
                self.ui_call(self.log, f"✓ {item['src']} -> {target}")
            else:
                failed += 1
                self.ui_call(self.log, f"✗ {item['src']} : {msg}")
            self.ui_call(self.update_progress, index, total, "备份中")

        self.ui_call(self.finish_operation, "备份", success, failed)

    def start_restore(self) -> None:
        if self._busy:
            return

        selected = tuple(self.tree.selection())
        if not selected:
            messagebox.showwarning("提示", "请先选择要恢复的文件。")
            return

        base_dir = self.dest_var.get().strip()
        if not base_dir:
            messagebox.showwarning("提示", "请先选择备份目录。")
            return

        if not messagebox.askyesno("确认", "恢复会覆盖本机现有配置，确定继续吗？"):
            return

        self.set_busy(True)
        self.progress["value"] = 0
        self.status_var.set(f"准备恢复 {len(selected)} 项...")
        self.log(f"开始恢复，共 {len(selected)} 项，来源目录：{base_dir}")
        threading.Thread(target=self.do_restore, args=(selected, base_dir), daemon=True).start()

    def do_restore(self, selected: tuple[str, ...], base_dir: str) -> None:
        total = len(selected)
        success = 0
        failed = 0

        for index, row_id in enumerate(selected, start=1):
            item = self.items[int(row_id)]
            backup_file = str(Path(base_dir) / Path(item["dst"]))
            ok, msg = self.copy_file(backup_file, item["src"])
            if ok:
                success += 1
                self.ui_call(self.log, f"✓ {backup_file} -> {item['src']}")
            else:
                failed += 1
                self.ui_call(self.log, f"✗ {backup_file} : {msg}")
            self.ui_call(self.update_progress, index, total, "恢复中")

        self.ui_call(self.finish_operation, "恢复", success, failed)


if __name__ == "__main__":
    root = tk.Tk()
    BackupTool(root)
    root.mainloop()
