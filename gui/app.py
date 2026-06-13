"""
OsEasy-ToolKit GUI 主程序
基于原生 Tkinter Notebook 选项卡布局，带详细日志输出
"""

import sys
import os
import threading
import time
import platform
import socket
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# 将上级目录加入路径，确保导入 core
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.toolkit import OsEasyToolKit
from core.system import SystemManager
from core.utils import ServiceInfo, ProcessInfo


class OsEasyGUI:
    """噢易工具箱 GUI 界面（Notebook 选项卡版 + 详细日志）"""

    # 配色方案
    BG_COLOR = "#f0f0f0"
    FG_COLOR = "#333333"
    ACCENT = "#2b82d9"
    SUCCESS = "#27ae60"
    WARNING = "#e67e22"
    DANGER = "#e74c3c"
    CARD_BG = "#ffffff"
    STATUS_RUNNING = "#27ae60"
    STATUS_STOPPED = "#e67e22"
    STATUS_UNKNOWN = "#95a5a6"

    # 日志颜色
    LOG_COLORS = {
        "cmd": "#6c5ce7",      # 紫色 - 命令
        "action": "#0984e3",   # 蓝色 - 操作
        "output": "#b2bec3",   # 灰色 - 输出
        "success": "#00b894",  # 绿色 - 成功
        "error": "#ff7675",    # 红色 - 错误
        "warning": "#fdcb6e",  # 黄色 - 警告
        "info": "#dfe6e9",     # 白色 - 信息
    }

    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("OsEasy-ToolKit - 噢易学生端解锁工具")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        self.root.configure(bg=self.BG_COLOR)

        # 先创建日志组件（因为 SystemManager 需要回调）
        self._build_main_layout()
        
        # 创建 toolkit（传入日志回调）
        self.toolkit = OsEasyToolKit(log_callback=self._log_callback)
        self.sys = self.toolkit.sys_mgr
        
        # 设置窗口居中
        self._center_window()
        
        # 构建各选项卡
        self._build_status_tab()
        self._build_unlock_tab()
        self._build_service_tab()
        self._build_process_tab()
        self._build_about_tab()
        
        # 协议
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # 启动检查
        self.root.after(100, self._init_check)

    def _center_window(self):
        """窗口居中"""
        self.root.update_idletasks()
        w, h = 900, 700
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_main_layout(self):
        """构建主布局（标题 + 选项卡 + 日志）"""
        # ======== 顶部标题栏 ========
        header = tk.Frame(self.root, bg=self.ACCENT, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="OsEasy-ToolKit",
            fg="white", bg=self.ACCENT,
            font=("微软雅黑", 16, "bold")
        ).pack(side="left", padx=20, pady=8)

        tk.Label(
            header, text="v2.0 - 噢易学生端解锁工具",
            fg="#a8d0f7", bg=self.ACCENT,
            font=("微软雅黑", 9)
        ).pack(side="left", pady=8)

        # ======== 选项卡区域 ========
        notebook_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        notebook_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        style = ttk.Style()
        style.configure("TNotebook", background=self.BG_COLOR)
        style.configure("TNotebook.Tab", font=("微软雅黑", 10), padding=(15, 5))

        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill="both", expand=True)

        # 创建选项卡框架
        self.tab_status = tk.Frame(self.notebook, bg=self.BG_COLOR)
        self.tab_unlock = tk.Frame(self.notebook, bg=self.BG_COLOR)
        self.tab_service = tk.Frame(self.notebook, bg=self.BG_COLOR)
        self.tab_process = tk.Frame(self.notebook, bg=self.BG_COLOR)
        self.tab_about = tk.Frame(self.notebook, bg=self.BG_COLOR)

        self.notebook.add(self.tab_status, text="  状态  ")
        self.notebook.add(self.tab_unlock, text="  解锁  ")
        self.notebook.add(self.tab_service, text="  服务管理  ")
        self.notebook.add(self.tab_process, text="  进程管理  ")
        self.notebook.add(self.tab_about, text="  关于  ")

        # ======== 底部日志区域（全局） ========
        log_frame = tk.LabelFrame(
            self.root, text=" 详细日志输出 ", font=("微软雅黑", 10, "bold"),
            bg="#1e1e1e", fg="#dfe6e9", padx=5, pady=5
        )
        log_frame.pack(fill="x", padx=10, pady=5)

        # 日志文本框
        text_frame = tk.Frame(log_frame, bg="#1e1e1e")
        text_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            text_frame, height=10, font=("Consolas", 9),
            bg="#1e1e1e", fg="#dfe6e9",
            relief="flat", borderwidth=0,
            state="disabled", wrap="word"
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(text_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

        # 日志标签配置
        for tag, color in self.LOG_COLORS.items():
            self.log_text.tag_config(tag, foreground=color)

        # ======== 底部状态栏 ========
        status_frame = tk.Frame(self.root, bg="#ddd", height=28)
        status_frame.pack(fill="x")
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(
            status_frame, text="就绪 | 正在初始化...",
            bg="#ddd", fg="#555", font=("微软雅黑", 9),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=15, pady=4)

    # ========== 日志回调 ==========
    def _log_callback(self, message: str, level: str = "info"):
        """日志回调（供 SystemManager 调用）"""
        self.root.after(0, lambda: self._append_log(message, level))

    def _append_log(self, message: str, level: str = "info"):
        """追加日志到文本框"""
        self.log_text.config(state="normal")
        
        # 时间戳
        ts = time.strftime("%H:%M:%S")
        
        # 插入时间戳（灰色）
        self.log_text.insert("end", f"[{ts}] ", "info")
        
        # 插入消息（带颜色标签）
        tag = level if level in self.LOG_COLORS else "info"
        self.log_text.insert("end", f"{message}\n", tag)
        
        # 自动滚动到底部
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def log(self, message: str, level: str = "info"):
        """外部日志接口"""
        self._append_log(message, level)

    def set_status(self, text: str):
        """更新状态栏"""
        self.status_label.config(text=text)

    # ========== 选项卡 1: 状态 ==========
    def _build_status_tab(self):
        """构建状态选项卡"""
        main_frame = tk.Frame(self.tab_status, bg=self.BG_COLOR)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 左栏
        left_frame = tk.Frame(main_frame, bg=self.BG_COLOR)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # 设备信息
        device_card = tk.LabelFrame(
            left_frame, text=" 设备信息 ", font=("微软雅黑", 11, "bold"),
            bg=self.CARD_BG, fg=self.FG_COLOR, padx=12, pady=10
        )
        device_card.pack(fill="x", pady=(0, 10))

        self.device_info_labels = {}
        device_items = [
            ("计算机名", "hostname"),
            ("用户名", "username"),
            ("操作系统", "os"),
            ("系统版本", "version"),
            ("处理器", "cpu"),
            ("IP地址", "ip"),
        ]
        for label_text, key in device_items:
            row = tk.Frame(device_card, bg=self.CARD_BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{label_text}:", width=10, anchor="w",
                     bg=self.CARD_BG, fg="#666", font=("微软雅黑", 9)
                     ).pack(side="left")
            lbl = tk.Label(row, text="获取中...", anchor="w",
                          bg=self.CARD_BG, fg=self.FG_COLOR, font=("微软雅黑", 9))
            lbl.pack(side="left", fill="x", expand=True)
            self.device_info_labels[key] = lbl

        # 学生端状态
        oseasy_card = tk.LabelFrame(
            left_frame, text=" 噢易学生端状态 ", font=("微软雅黑", 11, "bold"),
            bg=self.CARD_BG, fg=self.FG_COLOR, padx=12, pady=10
        )
        oseasy_card.pack(fill="x")

        self.oseasy_status_labels = {}
        oseasy_items = [
            ("Student.exe", "student"),
            ("MultiClient.exe", "multiclient"),
            ("ScreenRender.exe", "screenrender"),
            ("DeviceControl_x64.exe", "devicecontrol"),
        ]
        for label_text, key in oseasy_items:
            row = tk.Frame(oseasy_card, bg=self.CARD_BG)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label_text, width=20, anchor="w",
                     bg=self.CARD_BG, fg=self.FG_COLOR, font=("微软雅黑", 9)
                     ).pack(side="left")
            lbl = tk.Label(row, text="检测中...", width=10, anchor="center",
                          bg="#ecf0f1", fg="#666", font=("微软雅黑", 9, "bold"))
            lbl.pack(side="left")
            self.oseasy_status_labels[key] = lbl

        # 解锁状态
        unlock_row = tk.Frame(oseasy_card, bg=self.CARD_BG)
        unlock_row.pack(fill="x", pady=(10, 0))
        tk.Label(unlock_row, text="整体解锁状态:", font=("微软雅黑", 9, "bold"),
                 bg=self.CARD_BG, fg=self.FG_COLOR).pack(side="left")
        self.unlock_status_label = tk.Label(
            unlock_row, text="未知", font=("微软雅黑", 10, "bold"),
            bg="#ecf0f1", fg="#666", padx=10, pady=2
        )
        self.unlock_status_label.pack(side="left", padx=10)

        tk.Button(
            oseasy_card, text="⟳ 刷新状态", font=("微软雅黑", 9),
            bg=self.ACCENT, fg="white", relief="flat",
            padx=15, pady=3, cursor="hand2",
            command=self._refresh_all_status
        ).pack(pady=(10, 0))

        # 右栏：服务状态
        right_frame = tk.Frame(main_frame, bg=self.BG_COLOR)
        right_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))

        svc_card = tk.LabelFrame(
            right_frame, text=" 服务状态 ", font=("微软雅黑", 11, "bold"),
            bg=self.CARD_BG, fg=self.FG_COLOR, padx=12, pady=10
        )
        svc_card.pack(fill="both", expand=True)

        self.svc_status_labels = {}
        for svc in self.toolkit.SERVICES:
            row = tk.Frame(svc_card, bg=self.CARD_BG)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=svc.name, width=14, anchor="w",
                     bg=self.CARD_BG, fg=self.FG_COLOR, font=("微软雅黑", 9)
                     ).pack(side="left")
            lbl = tk.Label(row, text="检测中...", width=10, anchor="center",
                          bg="#ecf0f1", fg="#666", font=("微软雅黑", 9))
            lbl.pack(side="left")
            self.svc_status_labels[svc.name] = lbl

    # ========== 选项卡 2: 解锁 ==========
    def _build_unlock_tab(self):
        """构建解锁选项卡"""
        all_frame = tk.LabelFrame(
            self.tab_unlock, text=" 一键解锁 ", font=("微软雅黑", 12, "bold"),
            bg=self.CARD_BG, fg=self.FG_COLOR, padx=20, pady=15
        )
        all_frame.pack(fill="x", padx=15, pady=(15, 10))

        tk.Label(
            all_frame, text="同时解锁网络、控屏、键鼠、USB 所有限制",
            bg=self.CARD_BG, fg="#666", font=("微软雅黑", 10)
        ).pack(anchor="w")

        tk.Button(
            all_frame, text="★ 一键解锁所有限制",
            font=("微软雅黑", 14, "bold"), bg=self.SUCCESS, fg="white",
            activebackground="#219a52", activeforeground="white",
            relief="flat", padx=30, pady=12, cursor="hand2",
            command=self._unlock_all
        ).pack(pady=(15, 5))

        single_frame = tk.LabelFrame(
            self.tab_unlock, text=" 单独解锁 ", font=("微软雅黑", 12, "bold"),
            bg=self.CARD_BG, fg=self.FG_COLOR, padx=20, pady=15
        )
        single_frame.pack(fill="both", expand=True, padx=15, pady=10)

        unlock_items = [
            ("解锁网络限制", "停止网络服务 + 终止网络相关进程", self._unlock_network, self.ACCENT),
            ("解锁控屏限制", "终止屏幕广播进程 + 备份控屏程序", self._unlock_screen, self.ACCENT),
            ("解锁键盘鼠标锁", "删除键盘锁驱动 + 终止相关进程", self._unlock_keyboard, self.WARNING),
            ("解锁USB限制", "删除USB管控服务 + 解锁USB设备", self._unlock_usb, self.DANGER),
        ]

        for title, desc, cmd, color in unlock_items:
            card = tk.Frame(single_frame, bg=self.CARD_BG, padx=10, pady=10)
            card.pack(fill="x", pady=5)

            left = tk.Frame(card, bg=self.CARD_BG)
            left.pack(side="left", fill="y")

            tk.Label(left, text=title, font=("微软雅黑", 11, "bold"),
                     bg=self.CARD_BG, fg=self.FG_COLOR).pack(anchor="w")
            tk.Label(left, text=desc, font=("微软雅黑", 9),
                     bg=self.CARD_BG, fg="#888").pack(anchor="w")

            tk.Button(
                card, text="执行解锁", font=("微软雅黑", 10),
                bg=color, fg="white", relief="flat",
                padx=20, pady=6, cursor="hand2",
                command=cmd
            ).pack(side="right")

    # ========== 选项卡 3: 服务管理 ==========
    def _build_service_tab(self):
        """构建服务管理选项卡"""
        tk.Label(
            self.tab_service, text="管理噢易学生端相关服务",
            bg=self.BG_COLOR, fg="#666", font=("微软雅黑", 10)
        ).pack(anchor="w", padx=15, pady=(10, 5))

        list_frame = tk.Frame(self.tab_service, bg=self.BG_COLOR)
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # 表头
        header = tk.Frame(list_frame, bg="#e8e8e8", padx=10, pady=8)
        header.pack(fill="x")
        tk.Label(header, text="服务名称", width=20, anchor="w",
                 bg="#e8e8e8", fg="#333", font=("微软雅黑", 10, "bold")).pack(side="left")
        tk.Label(header, text="描述", width=25, anchor="w",
                 bg="#e8e8e8", fg="#333", font=("微软雅黑", 10, "bold")).pack(side="left")
        tk.Label(header, text="状态", width=12, anchor="center",
                 bg="#e8e8e8", fg="#333", font=("微软雅黑", 10, "bold")).pack(side="left")
        tk.Label(header, text="操作", width=20, anchor="center",
                 bg="#e8e8e8", fg="#333", font=("微软雅黑", 10, "bold")).pack(side="left")

        self.svc_tab_vars = {}
        for svc in self.toolkit.SERVICES:
            row = tk.Frame(list_frame, bg=self.CARD_BG, padx=10, pady=10)
            row.pack(fill="x", pady=2)

            tk.Label(row, text=svc.name, width=20, anchor="w",
                     bg=self.CARD_BG, fg=self.FG_COLOR, font=("微软雅黑", 10)
                     ).pack(side="left")
            tk.Label(row, text=svc.description, width=25, anchor="w",
                     bg=self.CARD_BG, fg="#666", font=("微软雅黑", 9)
                     ).pack(side="left")

            var = tk.StringVar(value="检测中...")
            self.svc_tab_vars[svc.name] = var
            status_lbl = tk.Label(row, textvariable=var, width=12, anchor="center",
                                  bg="#ecf0f1", fg="#666", font=("微软雅黑", 9, "bold"))
            status_lbl.pack(side="left", padx=(0, 10))

            btn_frame = tk.Frame(row, bg=self.CARD_BG)
            btn_frame.pack(side="left")

            tk.Button(btn_frame, text="停止", font=("微软雅黑", 9),
                      bg=self.DANGER, fg="white", relief="flat",
                      padx=12, pady=3, cursor="hand2",
                      command=lambda n=svc.name: self._stop_service(n)
                      ).pack(side="left", padx=2)
            tk.Button(btn_frame, text="启动", font=("微软雅黑", 9),
                      bg=self.SUCCESS, fg="white", relief="flat",
                      padx=12, pady=3, cursor="hand2",
                      command=lambda n=svc.name: self._start_service(n)
                      ).pack(side="left", padx=2)
            tk.Button(btn_frame, text="重启", font=("微软雅黑", 9),
                      bg=self.WARNING, fg="white", relief="flat",
                      padx=12, pady=3, cursor="hand2",
                      command=lambda n=svc.name: self._restart_service(n)
                      ).pack(side="left", padx=2)

        # 批量操作
        batch_frame = tk.Frame(self.tab_service, bg=self.BG_COLOR)
        batch_frame.pack(fill="x", padx=15, pady=15)

        tk.Button(
            batch_frame, text="⟳ 刷新服务状态", font=("微软雅黑", 10),
            bg="#95a5a6", fg="white", relief="flat",
            padx=20, pady=6, cursor="hand2",
            command=self._refresh_service_status
        ).pack(side="left", padx=5)

        tk.Button(
            batch_frame, text="✕ 停止所有服务", font=("微软雅黑", 10),
            bg=self.DANGER, fg="white", relief="flat",
            padx=20, pady=6, cursor="hand2",
            command=self._stop_all_services
        ).pack(side="left", padx=5)

    # ========== 选项卡 4: 进程管理 ==========
    def _build_process_tab(self):
        """构建进程管理选项卡"""
        tk.Label(
            self.tab_process, text="管理噢易学生端相关进程",
            bg=self.BG_COLOR, fg="#666", font=("微软雅黑", 10)
        ).pack(anchor="w", padx=15, pady=(10, 5))

        list_frame = tk.Frame(self.tab_process, bg=self.BG_COLOR)
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # 表头
        header = tk.Frame(list_frame, bg="#e8e8e8", padx=10, pady=8)
        header.pack(fill="x")
        tk.Label(header, text="进程名称", width=25, anchor="w",
                 bg="#e8e8e8", fg="#333", font=("微软雅黑", 10, "bold")).pack(side="left")
        tk.Label(header, text="描述", width=30, anchor="w",
                 bg="#e8e8e8", fg="#333", font=("微软雅黑", 10, "bold")).pack(side="left")
        tk.Label(header, text="状态", width=12, anchor="center",
                 bg="#e8e8e8", fg="#333", font=("微软雅黑", 10, "bold")).pack(side="left")
        tk.Label(header, text="操作", width=15, anchor="center",
                 bg="#e8e8e8", fg="#333", font=("微软雅黑", 10, "bold")).pack(side="left")

        # 滚动区域
        canvas_frame = tk.Frame(list_frame, bg=self.BG_COLOR)
        canvas_frame.pack(fill="both", expand=True, pady=2)

        canvas = tk.Canvas(canvas_frame, bg=self.BG_COLOR, highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self.proc_scroll_frame = tk.Frame(canvas, bg=self.BG_COLOR)

        self.proc_scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.proc_scroll_frame, anchor="nw", width=830)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 进程列表
        self.proc_tab_vars = {}
        for proc in self.toolkit.PROCESSES:
            row = tk.Frame(self.proc_scroll_frame, bg=self.CARD_BG, padx=10, pady=6)
            row.pack(fill="x", pady=1)

            tk.Label(row, text=proc.name, width=25, anchor="w",
                     bg=self.CARD_BG, fg=self.FG_COLOR, font=("微软雅黑", 9)
                     ).pack(side="left")
            tk.Label(row, text=proc.description, width=30, anchor="w",
                     bg=self.CARD_BG, fg="#666", font=("微软雅黑", 9)
                     ).pack(side="left")

            var = tk.StringVar(value="检测中...")
            self.proc_tab_vars[proc.name] = var
            status_lbl = tk.Label(row, textvariable=var, width=12, anchor="center",
                                  bg="#ecf0f1", fg="#666", font=("微软雅黑", 9))
            status_lbl.pack(side="left", padx=(0, 10))

            tk.Button(row, text="终止", font=("微软雅黑", 9),
                      bg=self.DANGER, fg="white", relief="flat",
                      padx=15, pady=2, cursor="hand2",
                      command=lambda n=proc.name: self._kill_process(n)
                      ).pack(side="left")

        # 批量操作
        batch_frame = tk.Frame(self.tab_process, bg=self.BG_COLOR)
        batch_frame.pack(fill="x", padx=15, pady=10)

        tk.Button(
            batch_frame, text="⟳ 刷新进程状态", font=("微软雅黑", 10),
            bg="#95a5a6", fg="white", relief="flat",
            padx=20, pady=6, cursor="hand2",
            command=self._refresh_process_status
        ).pack(side="left", padx=5)

        tk.Button(
            batch_frame, text="✕ 终止所有进程", font=("微软雅黑", 10),
            bg=self.DANGER, fg="white", relief="flat",
            padx=20, pady=6, cursor="hand2",
            command=self._kill_all
        ).pack(side="left", padx=5)

        self.proc_monitor_btn = tk.Button(
            batch_frame, text="▶ 开始持续监控", font=("微软雅黑", 10),
            bg=self.SUCCESS, fg="white", relief="flat",
            padx=20, pady=6, cursor="hand2",
            command=self._toggle_monitor
        )
        self.proc_monitor_btn.pack(side="left", padx=5)

        self.proc_monitor_label = tk.Label(
            batch_frame, text="未启动", font=("微软雅黑", 9),
            bg=self.BG_COLOR, fg="#888"
        )
        self.proc_monitor_label.pack(side="left", padx=10)

        tk.Button(
            batch_frame, text="⏸ 挂起/恢复 Student.exe", font=("微软雅黑", 10),
            bg=self.WARNING, fg="white", relief="flat",
            padx=20, pady=6, cursor="hand2",
            command=self._suspend_student
        ).pack(side="right", padx=5)

    # ========== 选项卡 5: 关于 ==========
    def _build_about_tab(self):
        """构建关于选项卡"""
        container = tk.Frame(self.tab_about, bg=self.BG_COLOR)
        container.pack(expand=True)

        tk.Label(
            container, text="OsEasy-ToolKit",
            font=("微软雅黑", 28, "bold"),
            bg=self.BG_COLOR, fg=self.ACCENT
        ).pack(pady=(30, 5))

        tk.Label(
            container, text="v2.0 - Python Edition",
            font=("微软雅黑", 12),
            bg=self.BG_COLOR, fg="#666"
        ).pack()

        tk.Frame(container, bg="#ccc", height=1, width=400).pack(pady=20)

        intro_text = """一款用于解锁噢易(OsEasy)学生端各类限制的工具
支持解锁网络、控屏、键盘鼠标锁、USB 限制等功能"""
        tk.Label(
            container, text=intro_text,
            font=("微软雅黑", 11),
            bg=self.BG_COLOR, fg="#444", justify="center"
        ).pack()

        features = [
            "✓ 一键解锁所有限制",
            "✓ 服务管理（停止/启动/重启）",
            "✓ 进程管理（终止/监控）",
            "✓ 挂起/恢复 Student.exe",
            "✓ 持续监控模式（防复活）",
            "✓ 设备信息查看",
            "✓ 详细命令执行日志",
        ]
        for feat in features:
            tk.Label(
                container, text=feat,
                font=("微软雅黑", 10),
                bg=self.BG_COLOR, fg="#555"
            ).pack(anchor="w", padx=100, pady=2)

        tk.Frame(container, bg="#ccc", height=1, width=400).pack(pady=20)

        tk.Label(
            container, text="作者: 杰哥",
            font=("微软雅黑", 10),
            bg=self.BG_COLOR, fg="#666"
        ).pack()

        link_frame = tk.Frame(container, bg=self.BG_COLOR)
        link_frame.pack(pady=10)

        tk.Label(
            link_frame, text="GitHub: ",
            font=("微软雅黑", 10),
            bg=self.BG_COLOR, fg="#666"
        ).pack(side="left")

        github_link = tk.Label(
            link_frame, text="github.com/Jlively-ai/OSEasy-ToolKit",
            font=("微软雅黑", 10, "underline"),
            bg=self.BG_COLOR, fg=self.ACCENT, cursor="hand2"
        )
        github_link.pack(side="left")
        github_link.bind("<Button-1>", lambda e: self._open_github())

        tk.Label(
            container,
            text="本工具仅供学习和研究使用，请勿用于非法用途\n使用本工具造成的任何后果由使用者自行承担",
            font=("微软雅黑", 9),
            bg=self.BG_COLOR, fg="#999", justify="center"
        ).pack(pady=(20, 10))

    # ========== 设备信息 ==========
    def _get_device_info(self):
        """获取设备信息"""
        info = {
            "hostname": socket.gethostname(),
            "username": os.getlogin() if hasattr(os, "getlogin") else "Unknown",
            "os": f"{platform.system()} {platform.release()}",
            "version": platform.version(),
            "cpu": platform.processor() or "Unknown",
            "ip": "127.0.0.1",
        }
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info["ip"] = s.getsockname()[0]
            s.close()
        except Exception:
            pass
        return info

    def _update_device_info(self):
        """更新设备信息显示"""
        info = self._get_device_info()
        for key, lbl in self.device_info_labels.items():
            if key in info:
                lbl.config(text=info[key])

    # ========== 状态刷新 ==========
    def _refresh_all_status(self):
        """刷新所有状态"""
        self.log("=" * 50, "info")
        self.log("【刷新状态】正在获取所有状态信息...", "action")
        self._update_device_info()
        self._refresh_service_status()
        self._refresh_process_status()
        self._check_oseasy_status()
        self.log("【刷新完成】状态已更新", "success")

    def _check_oseasy_status(self):
        """检查学生端进程状态"""
        procs = {
            "student": "Student.exe",
            "multiclient": "MultiClient.exe",
            "screenrender": "ScreenRender.exe",
            "devicecontrol": "DeviceControl_x64.exe",
        }
        running_count = 0
        for key, proc_name in procs.items():
            status = self.sys.get_process_status(proc_name)
            lbl = self.oseasy_status_labels.get(key)
            if lbl:
                if status == "运行中":
                    lbl.config(text="运行中", bg=self.STATUS_RUNNING, fg="white")
                    running_count += 1
                else:
                    lbl.config(text="未运行", bg=self.STATUS_STOPPED, fg="white")

        unlock_lbl = self.unlock_status_label
        if running_count == 0:
            unlock_lbl.config(text="已解锁 ✓", bg=self.STATUS_RUNNING, fg="white")
        elif running_count == len(procs):
            unlock_lbl.config(text="未解锁", bg=self.STATUS_STOPPED, fg="white")
        else:
            unlock_lbl.config(text="部分解锁", bg=self.WARNING, fg="white")

    # ========== 解锁操作 ==========
    def _unlock_network(self):
        self.log("=" * 50, "info")
        self.log("【解锁网络】开始执行网络解锁...", "action")
        def task():
            self.toolkit.unlock_network()
            self.root.after(0, self._refresh_service_status)
            self.root.after(0, self._check_oseasy_status)
        self._run_in_thread(task)

    def _unlock_screen(self):
        self.log("=" * 50, "info")
        self.log("【解锁控屏】开始执行控屏解锁...", "action")
        def task():
            self.toolkit.unlock_screen()
            self.root.after(0, self._check_oseasy_status)
        self._run_in_thread(task)

    def _unlock_keyboard(self):
        self.log("=" * 50, "info")
        self.log("【解锁键鼠】开始执行键盘鼠标解锁...", "action")
        def task():
            self.toolkit.unlock_keyboard()
            self.root.after(0, self._check_oseasy_status)
        self._run_in_thread(task)

    def _unlock_usb(self):
        self.log("=" * 50, "info")
        self.log("【解锁USB】开始执行USB解锁...", "action")
        def task():
            self.toolkit.unlock_usb()
            self.root.after(0, self._refresh_service_status)
        self._run_in_thread(task)

    def _unlock_all(self):
        self.log("=" * 50, "info")
        self.log("【一键解锁】开始执行全部解锁操作...", "action")
        def task():
            self.toolkit.unlock_all()
            self.root.after(0, self._refresh_service_status)
            self.root.after(0, self._check_oseasy_status)
        self._run_in_thread(task)

    # ========== 服务操作 ==========
    def _start_service(self, name):
        self.log(f"【服务操作】启动服务: {name}", "action")
        def task():
            self.sys.start_service(name)
            self.root.after(0, self._refresh_service_status)
        self._run_in_thread(task)

    def _stop_service(self, name):
        self.log(f"【服务操作】停止服务: {name}", "action")
        def task():
            self.sys.stop_service(name)
            self.root.after(0, self._refresh_service_status)
        self._run_in_thread(task)

    def _restart_service(self, name):
        self.log(f"【服务操作】重启服务: {name}", "action")
        def task():
            self.sys.stop_service(name)
            time.sleep(1)
            self.sys.start_service(name)
            self.root.after(0, self._refresh_service_status)
        self._run_in_thread(task)

    def _stop_all_services(self):
        self.log("=" * 50, "info")
        self.log("【批量操作】停止所有服务...", "action")
        def task():
            for svc in self.toolkit.SERVICES:
                self.sys.stop_service(svc.name)
            self.root.after(0, self._refresh_service_status)
        self._run_in_thread(task)

    def _refresh_service_status(self):
        """刷新服务状态"""
        def task():
            for svc in self.toolkit.SERVICES:
                status = self.sys.get_service_status(svc.name)
                if svc.name in self.svc_status_labels:
                    lbl = self.svc_status_labels[svc.name]
                    if status == "运行中":
                        lbl.config(text="运行中", bg=self.STATUS_RUNNING, fg="white")
                    elif status == "已停止":
                        lbl.config(text="已停止", bg=self.STATUS_STOPPED, fg="white")
                    else:
                        lbl.config(text="不存在", bg=self.STATUS_UNKNOWN, fg="white")
                if svc.name in self.svc_tab_vars:
                    self.svc_tab_vars[svc.name].set(status)
        self._run_in_thread(task)

    # ========== 进程操作 ==========
    def _kill_process(self, name):
        self.log(f"【进程操作】终止进程: {name}", "action")
        def task():
            self.sys.kill_process(name)
            self.root.after(0, self._refresh_process_status)
            self.root.after(0, self._check_oseasy_status)
        self._run_in_thread(task)

    def _kill_all(self):
        self.log("=" * 50, "info")
        self.log("【批量操作】终止所有学生端进程...", "action")
        def task():
            self.toolkit.kill_all_processes()
            self.root.after(0, self._refresh_process_status)
            self.root.after(0, self._check_oseasy_status)
        self._run_in_thread(task)

    def _refresh_process_status(self):
        """刷新进程状态"""
        def task():
            for proc in self.toolkit.PROCESSES:
                status = self.sys.get_process_status(proc.name)
                if proc.name in self.proc_tab_vars:
                    self.proc_tab_vars[proc.name].set(status)
        self._run_in_thread(task)

    def _suspend_student(self):
        self.log("=" * 50, "info")
        self.log("【挂起/恢复】操作 Student.exe...", "action")
        def task():
            self.toolkit.suspend_student()
            self.root.after(0, self._check_oseasy_status)
        self._run_in_thread(task)

    def _toggle_monitor(self):
        """切换监控模式"""
        if not self.monitoring:
            self.monitoring = True
            self.proc_monitor_btn.config(text="■ 停止监控", bg=self.DANGER)
            self.proc_monitor_label.config(text="监控中...", fg=self.SUCCESS)
            self.log("=" * 50, "info")
            self.log("【监控模式】持续监控已启动 (每2秒检查一次)", "action")
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
        else:
            self.monitoring = False
            self.proc_monitor_btn.config(text="▶ 开始持续监控", bg=self.SUCCESS)
            self.proc_monitor_label.config(text="未启动", fg="#888")
            self.log("【监控模式】持续监控已停止", "action")

    def _monitor_loop(self):
        """监控循环"""
        monitor_procs = ["Student.exe", "MultiClient.exe", "ScreenRender.exe", "DeviceControl_x64.exe"]
        while self.monitoring:
            for proc in monitor_procs:
                if not self.monitoring:
                    break
                self.sys.kill_process(proc)
            time.sleep(2)

    # ========== 其他 ==========
    def _open_github(self):
        """打开 GitHub 链接"""
        import webbrowser
        webbrowser.open("https://github.com/Jlively-ai/OSEasy-ToolKit")

    def _run_in_thread(self, target):
        """在后台线程中执行"""
        def wrapper():
            try:
                target()
            except Exception as e:
                self.root.after(0, self.log, f"【错误】{e}", "error")
        t = threading.Thread(target=wrapper, daemon=True)
        t.start()

    def _init_check(self):
        """初始检查"""
        self.log("=" * 50, "info")
        self.log("OsEasy-ToolKit GUI 已启动", "success")
        self.log("正在初始化系统...", "info")
        
        self._update_device_info()

        if sys.platform != 'win32':
            self.log("警告：当前系统不是 Windows，部分功能可能受限", "warning")
            self.set_status("非 Windows 系统 - 部分功能受限")
        else:
            if self.sys.is_admin():
                self.log("管理员权限检查: 已通过 ✓", "success")
                self.set_status("就绪 | 管理员权限: √")
            else:
                self.log("管理员权限检查: 未通过 ✗ 建议以管理员身份运行", "warning")
                self.set_status("就绪 | 管理员权限: ×")

        self._refresh_service_status()
        self._refresh_process_status()
        self._check_oseasy_status()
        self.log("初始化完成", "success")

    def _on_closing(self):
        """关闭窗口"""
        self.monitoring = False
        self.root.destroy()

    def run(self):
        """启动 GUI"""
        self.root.mainloop()


def main():
    app = OsEasyGUI()
    app.run()


if __name__ == "__main__":
    main()