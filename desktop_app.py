import os
import platform
import queue
import runpy
import subprocess
import sys
import threading
import tkinter as tk
from math import sqrt
from datetime import datetime
from pathlib import Path
from tkinter import BooleanVar, StringVar, Tk, filedialog, messagebox
from tkinter import scrolledtext, ttk


if getattr(sys, "frozen", False):
    PROJECT_DIR = Path(sys.executable).resolve().parent
else:
    PROJECT_DIR = Path(__file__).resolve().parent
BOT_SCRIPT_NAME = "main02.py"
BOT_SCRIPT = PROJECT_DIR / BOT_SCRIPT_NAME
BOT_RUNNER_ARG = "--bot-runner"
EXCEL_EXTENSIONS = {".xlsx", ".xls", ".csv"}

BG_COLOR = "#f4f7fb"
PANEL_COLOR = "#ffffff"
TEXT_COLOR = "#172033"
MUTED_COLOR = "#667085"
ACCENT_COLOR = "#5b5ce2"
ACCENT_HOVER = "#4849c7"
BLUE_COLOR = "#1570ef"
GREEN_COLOR = "#079455"
DANGER_COLOR = "#d92d20"
LOG_BG = "#101828"
LOG_FG = "#e6edf7"


class GradientButton(tk.Canvas):
    def __init__(
        self,
        parent,
        icon,
        title,
        subtitle,
        command,
        start_color,
        end_color,
        hover_color,
        state="normal",
    ):
        super().__init__(parent, height=78, bg=PANEL_COLOR, highlightthickness=0, bd=0, cursor="hand2")
        self.icon = icon
        self.title = title
        self.subtitle = subtitle
        self.command = command
        self.start_color = start_color
        self.end_color = end_color
        self.hover_color = hover_color
        self.button_state = state
        self.hovered = False
        self.radius = 12

        self.bind("<Configure>", lambda _event: self.draw())
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)
        state = kwargs.pop("state", None)
        if state is not None:
            self.button_state = state
            self.configure(cursor="arrow" if state == "disabled" else "hand2")
            self.draw()
        if kwargs:
            super().configure(**kwargs)

    config = configure

    def on_enter(self, _event):
        if self.button_state == "disabled":
            return
        self.hovered = True
        self.draw()

    def on_leave(self, _event):
        self.hovered = False
        self.draw()

    def on_click(self, _event):
        if self.button_state != "disabled" and self.command:
            self.command()

    def hex_to_rgb(self, color):
        color = color.lstrip("#")
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def blend(self, color_a, color_b, ratio):
        a = self.hex_to_rgb(color_a)
        b = self.hex_to_rgb(color_b)
        return self.rgb_to_hex(tuple(int(a[i] + (b[i] - a[i]) * ratio) for i in range(3)))

    def draw_rounded_gradient(self, x1, y1, x2, y2, radius, start_color, end_color):
        width = max(1, int(x2 - x1))
        height = max(1, int(y2 - y1))
        for i in range(width):
            ratio = i / max(1, width - 1)
            color = self.blend(start_color, end_color, ratio)
            x = x1 + i
            if i < radius:
                dx = radius - i
                inset = radius - sqrt(max(0, radius * radius - dx * dx))
                top = y1 + inset
                bottom = y2 - inset
            elif i > width - radius:
                dx = i - (width - radius)
                inset = radius - sqrt(max(0, radius * radius - dx * dx))
                top = y1 + inset
                bottom = y2 - inset
            else:
                top = y1
                bottom = y2
            self.create_line(x, top, x, bottom, fill=color)

    def draw(self):
        self.delete("all")
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        x1, y1 = 4, 4
        x2, y2 = width - 4, height - 4

        if self.button_state == "disabled":
            start_color = "#eef2f6"
            end_color = "#e4e7ec"
            text_color = "#98a2b3"
        elif self.hovered:
            start_color = self.hover_color
            end_color = self.hover_color
            text_color = "#ffffff"
        else:
            start_color = self.start_color
            end_color = self.end_color
            text_color = "#ffffff"

        self.draw_rounded_gradient(x1, y1, x2, y2, self.radius, start_color, end_color)
        self.create_text(
            width / 2,
            height / 2 - 9,
            text=f"{self.icon}  {self.title}",
            fill=text_color,
            font=("Segoe UI", 14, "bold"),
        )
        self.create_text(
            width / 2,
            height / 2 + 15,
            text=self.subtitle,
            fill=text_color,
            font=("Segoe UI", 10, "bold"),
        )


class LuckyNumbersBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lucky Numbers Bot")
        self.root.geometry("1440x860")
        self.root.minsize(1120, 760)

        self.bot_process = None
        self.chrome_process = None
        self.log_queue = queue.Queue()

        self.script_var = StringVar(value=self.default_bot_script_label())
        self.input_file_var = StringVar(value=str(self.default_input_file()))
        self.stake_var = StringVar(value="1")
        self.mode_var = StringVar(value="Real submit - Multiple row")
        self.start_mode_var = StringVar(value="Start from beginning")
        self.start_row_var = StringVar(value="")
        self.login_wait_var = StringVar(value="900")
        self.error_retries_var = StringVar(value="3")
        self.game_data_retries_var = StringVar(value="3")
        self.clear_logs_on_start_var = BooleanVar(value=True)
        self.auto_scroll_var = BooleanVar(value=True)
        self.clock_var = StringVar(value="")

        self.configure_style()
        self.build_ui()
        self.root.after(150, self.drain_log_queue)
        self.root.after(500, self.update_clock)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def configure_style(self):
        self.root.configure(bg=BG_COLOR)
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        default_font = ("Segoe UI", 10)
        heading_font = ("Segoe UI", 20, "bold")
        section_font = ("Segoe UI", 11, "bold")

        style.configure(".", font=default_font, background=BG_COLOR, foreground=TEXT_COLOR)
        style.configure("App.TFrame", background=BG_COLOR)
        style.configure("Header.TFrame", background=TEXT_COLOR)
        style.configure("Panel.TFrame", background=PANEL_COLOR, relief="flat")
        style.configure("Toolbar.TFrame", background=BG_COLOR)

        style.configure("Title.TLabel", background=TEXT_COLOR, foreground="#ffffff", font=heading_font)
        style.configure("Subtitle.TLabel", background=TEXT_COLOR, foreground="#c8d2e4", font=("Segoe UI", 10))
        style.configure("Section.TLabel", background=PANEL_COLOR, foreground=TEXT_COLOR, font=section_font)
        style.configure("Muted.TLabel", background=PANEL_COLOR, foreground=MUTED_COLOR)
        style.configure("Status.TLabel", background=BG_COLOR, foreground=ACCENT_COLOR, font=("Segoe UI", 10, "bold"))

        style.configure(
            "TEntry",
            fieldbackground="#ffffff",
            bordercolor="#c8d7ea",
            lightcolor="#edf4ff",
            darkcolor="#c8d7ea",
            padding=(10, 7),
            relief="flat",
        )
        style.configure(
            "TCombobox",
            fieldbackground="#ffffff",
            background="#ffffff",
            bordercolor="#c8d7ea",
            lightcolor="#edf4ff",
            darkcolor="#c8d7ea",
            arrowcolor=ACCENT_COLOR,
            padding=(10, 7),
            relief="flat",
        )
        style.map("TCombobox", fieldbackground=[("readonly", "#ffffff")])

        style.configure("TButton", padding=(14, 9), background="#eef4ff", foreground=TEXT_COLOR, borderwidth=0, relief="flat")
        style.map("TButton", background=[("active", "#e2e8f0")])
        style.configure("Accent.TButton", background=ACCENT_COLOR, foreground="#ffffff", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", ACCENT_HOVER), ("disabled", "#b9baf3")])
        style.configure("Danger.TButton", background="#fee4e2", foreground=DANGER_COLOR, font=("Segoe UI", 10, "bold"))
        style.map("Danger.TButton", background=[("active", "#fecdca"), ("disabled", "#f2f4f7")])
        style.configure("Secondary.TButton", background="#eef2ff", foreground=ACCENT_COLOR, font=("Segoe UI", 10, "bold"))
        style.map("Secondary.TButton", background=[("active", "#e0e7ff")])

        style.configure("TLabelframe", background=PANEL_COLOR, bordercolor="#e4ecf7", relief="flat")
        style.configure("TLabelframe.Label", background=PANEL_COLOR, foreground=TEXT_COLOR, font=section_font)
        style.configure("TCheckbutton", background=PANEL_COLOR, foreground=TEXT_COLOR)

    def bundled_bot_script(self):
        if getattr(sys, "frozen", False):
            return Path(getattr(sys, "_MEIPASS", PROJECT_DIR)) / BOT_SCRIPT_NAME
        return BOT_SCRIPT

    def default_bot_script_label(self):
        if getattr(sys, "frozen", False):
            return f"Bundled: {BOT_SCRIPT_NAME}"
        return str(BOT_SCRIPT)

    def default_input_file(self):
        for name in ("file.xlsx", "1sample_file_main.xlsx", "1sample_file.xlsx", "sample_file.xlsx"):
            path = PROJECT_DIR / name
            if path.exists():
                return path
        return PROJECT_DIR

    def card(self, parent, row, column, title, subtitle, step_text=None, columnspan=1):
        frame = tk.Frame(parent, bg=PANEL_COLOR, bd=0, relief="flat", highlightthickness=1, highlightbackground="#edf3fb")
        frame.grid(row=row, column=column, columnspan=columnspan, sticky="nsew", padx=8, pady=8)
        frame.columnconfigure(1, weight=0)

        if step_text:
            step = tk.Canvas(frame, width=58, height=58, bg=PANEL_COLOR, highlightthickness=0)
            step_color = BLUE_COLOR if step_text == "1" else "#7a35dc"
            step.create_oval(4, 4, 54, 54, fill=step_color, outline=step_color)
            step.create_text(29, 29, text=step_text, fill="#ffffff", font=("Segoe UI", 18, "bold"))
            step.grid(row=0, column=0, rowspan=2, padx=(18, 14), pady=(18, 10), sticky="n")
            title_col = 1
        else:
            title_col = 0

        tk.Label(frame, text=title, bg=PANEL_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 14, "bold")).grid(
            row=0,
            column=title_col,
            columnspan=3 if step_text else 1,
            sticky="w",
            padx=(18 if not step_text else 0, 18),
            pady=(18, 0),
        )
        tk.Label(frame, text=subtitle, bg=PANEL_COLOR, fg="#405993", font=("Segoe UI", 9)).grid(
            row=1,
            column=title_col,
            columnspan=3 if step_text else 1,
            sticky="w",
            padx=(18 if not step_text else 0, 18),
            pady=(3, 12),
        )
        return frame

    def header_logo(self, parent):
        canvas = tk.Canvas(parent, width=56, height=56, bg="#eef6ff", highlightthickness=0)
        green = "#22c55e"
        dark = "#16a34a"
        canvas.create_oval(20, 2, 36, 22, fill=green, outline=dark)
        canvas.create_oval(34, 18, 54, 34, fill=green, outline=dark)
        canvas.create_oval(20, 32, 36, 54, fill=green, outline=dark)
        canvas.create_oval(2, 18, 22, 34, fill=green, outline=dark)
        canvas.create_line(29, 29, 44, 48, fill=dark, width=4)
        return canvas

    def icon_label(self, parent, kind, color, row):
        canvas = tk.Canvas(parent, width=52, height=52, bg=PANEL_COLOR, highlightthickness=0)
        canvas.grid(row=row, column=0, padx=(18, 12), pady=10, sticky="n")
        canvas.create_rectangle(3, 3, 49, 49, fill="#f1f7ff", outline="#e4ecf7")

        if kind == "python":
            canvas.create_oval(10, 9, 32, 31, fill="#1570ef", outline="")
            canvas.create_oval(20, 20, 42, 42, fill="#fdb022", outline="")
            canvas.create_text(26, 26, text="PY", fill="#ffffff", font=("Segoe UI", 11, "bold"))
        elif kind == "excel":
            canvas.create_rectangle(11, 9, 41, 43, fill="#12b76a", outline="#039855")
            canvas.create_rectangle(18, 9, 41, 43, fill="#32d583", outline="#039855")
            canvas.create_text(24, 26, text="X", fill="#ffffff", font=("Segoe UI", 18, "bold"))
        elif kind == "stake":
            canvas.create_text(26, 26, text="#", fill=color, font=("Segoe UI", 25, "bold"))
        elif kind == "rows":
            for y in (17, 26, 35):
                canvas.create_oval(11, y - 3, 17, y + 3, fill=color, outline="")
                canvas.create_line(23, y, 41, y, fill=color, width=3)
        elif kind == "log":
            canvas.create_rectangle(15, 10, 38, 42, fill=color, outline="")
            canvas.create_line(21, 20, 32, 20, fill="#ffffff", width=2)
            canvas.create_line(21, 27, 32, 27, fill="#ffffff", width=2)
            canvas.create_line(21, 34, 29, 34, fill="#ffffff", width=2)
        return canvas

    def field_hint(self, parent, text, row, column):
        tk.Label(parent, text=text, bg=PANEL_COLOR, fg="#405993", font=("Segoe UI", 8)).grid(
            row=row, column=column, sticky="w", pady=(0, 6)
        )

    def create_action_button(
        self,
        parent,
        icon,
        title,
        subtitle,
        command,
        start_color,
        end_color,
        hover_color,
        column,
        state="normal",
    ):
        button = GradientButton(
            parent,
            icon=icon,
            title=title,
            subtitle=subtitle,
            command=command,
            start_color=start_color,
            end_color=end_color,
            hover_color=hover_color,
            state=state,
        )
        button.grid(row=0, column=column, sticky="ew", padx=6, pady=10)
        return button

    def build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

        header = tk.Frame(self.root, bg="#eef6ff", height=86, highlightthickness=1, highlightbackground="#deebfb")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

        brand = tk.Frame(header, bg="#eef6ff")
        brand.grid(row=0, column=0, sticky="w", padx=22, pady=14)
        tk.Label(brand, text="Lucky Numbers Bot", bg="#eef6ff", fg="#06175a", font=("Segoe UI", 20, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        tk.Label(
            brand,
            text="Automate your Excel-based Lucky Numbers task",
            bg="#eef6ff",
            fg="#405993",
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w")

        right_header = tk.Frame(header, bg="#eef6ff")
        right_header.grid(row=0, column=1, sticky="e", padx=22, pady=14)
        status = tk.Frame(right_header, bg="#d1fadf", highlightthickness=0)
        status.grid(row=0, column=0, padx=(0, 24))
        tk.Label(status, text="●", bg="#d1fadf", fg="#039855", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, rowspan=2, padx=(16, 10), pady=8
        )
        self.status_var = StringVar(value="Ready")
        tk.Label(status, textvariable=self.status_var, bg="#d1fadf", fg="#05603a", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=1, sticky="w", padx=(0, 18), pady=(7, 0)
        )
        self.status_detail_var = StringVar(value="No process running")
        tk.Label(status, textvariable=self.status_detail_var, bg="#d1fadf", fg="#05603a", font=("Segoe UI", 8)).grid(
            row=1, column=1, sticky="w", padx=(0, 18), pady=(0, 7)
        )
        tk.Label(right_header, textvariable=self.clock_var, bg="#eef6ff", fg="#06175a", font=("Segoe UI", 10)).grid(
            row=0, column=1, sticky="e"
        )

        content = tk.Frame(self.root, bg=BG_COLOR)
        content.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 0))
        content.columnconfigure(0, weight=7)
        content.columnconfigure(1, weight=5)

        files_card = self.card(
            content,
            0,
            0,
            "Files & Script",
            "Select the automation script and the Excel/CSV file.",
            step_text="1",
        )
        files_card.columnconfigure(2, weight=1)
        files_card.columnconfigure(3, weight=0)

        self.icon_label(files_card, "python", "#fdb022", 2)
        tk.Label(files_card, text="Bot Script", bg=PANEL_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 9, "bold")).grid(
            row=2, column=1, sticky="w", padx=(0, 10), pady=(8, 0)
        )
        self.script_entry = ttk.Entry(files_card, textvariable=self.script_var, state="readonly")
        self.script_entry.grid(
            row=2, column=2, columnspan=2, sticky="ew", pady=(8, 0), padx=(0, 18)
        )
        self.field_hint(files_card, "Final automation file used by the desktop app", 3, 2)

        self.icon_label(files_card, "excel", "#12b76a", 4)
        tk.Label(files_card, text="Input File", bg=PANEL_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 9, "bold")).grid(
            row=4, column=1, sticky="w", padx=(0, 10), pady=(8, 0)
        )
        self.input_entry = ttk.Entry(files_card, textvariable=self.input_file_var)
        self.input_entry.grid(row=4, column=2, sticky="ew", pady=(8, 0), padx=(0, 10))
        ttk.Button(files_card, text="Browse", command=self.browse_input_file, style="Secondary.TButton", width=14).grid(
            row=4, column=3, sticky="ew", padx=(0, 18), pady=(8, 0)
        )
        self.field_hint(files_card, "Select the client's Excel or CSV betting file", 5, 2)

        config_card = self.card(
            content,
            0,
            1,
            "Run Configuration",
            "Configure how you want to run the bot.",
            step_text="2",
        )
        config_card.columnconfigure(2, weight=1)
        config_card.columnconfigure(5, weight=1)

        self.icon_label(config_card, "stake", BLUE_COLOR, 2)
        tk.Label(config_card, text="Stake", bg=PANEL_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 9, "bold")).grid(
            row=2, column=1, sticky="w", padx=(0, 10), pady=(8, 0)
        )
        ttk.Entry(config_card, textvariable=self.stake_var, width=18).grid(row=2, column=2, sticky="ew", pady=(8, 0))
        self.field_hint(config_card, "Value used in the process", 3, 2)

        tk.Label(config_card, text="Run Mode", bg=PANEL_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 9, "bold")).grid(
            row=2, column=4, sticky="w", padx=(24, 10), pady=(8, 0)
        )
        mode_combo = ttk.Combobox(
            config_card,
            textvariable=self.mode_var,
            state="readonly",
            values=[
                "Dry run - Single",
                "Dry run - Multiple row",
                "Real submit - Single",
                "Real submit - Multiple row",
                "Add only - No submit",
            ],
            width=28,
        )
        mode_combo.grid(row=2, column=5, sticky="ew", padx=(0, 18), pady=(8, 0))
        self.field_hint(config_card, "Choose how to run the bot", 3, 5)

        self.icon_label(config_card, "rows", BLUE_COLOR, 4)
        tk.Label(config_card, text="Start Rows", bg=PANEL_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 9, "bold")).grid(
            row=4, column=1, sticky="w", padx=(0, 10), pady=(8, 0)
        )
        start_combo = ttk.Combobox(
            config_card,
            textvariable=self.start_mode_var,
            state="readonly",
            values=[
                "Start from beginning",
                "Resume from latest result",
                "Specific row",
            ],
            width=30,
        )
        start_combo.grid(row=4, column=2, sticky="ew", pady=(8, 0))
        start_combo.bind("<<ComboboxSelected>>", lambda _event: self.update_start_row_state())
        self.field_hint(config_card, "Where to start processing", 5, 2)

        tk.Label(config_card, text="Row Number", bg=PANEL_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 9, "bold")).grid(
            row=4, column=4, sticky="w", padx=(24, 10), pady=(8, 0)
        )
        self.start_row_entry = ttk.Entry(config_card, textvariable=self.start_row_var, width=18, state="disabled")
        self.start_row_entry.grid(row=4, column=5, sticky="ew", padx=(0, 18), pady=(8, 0))
        self.field_hint(config_card, "Optional. Used only for specific row", 5, 5)

        advanced = ttk.LabelFrame(config_card, text="Advanced", padding=(12, 8, 12, 8))
        advanced.grid(row=6, column=0, columnspan=6, sticky="ew", padx=18, pady=(12, 18))

        ttk.Label(advanced, text="Login wait").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(advanced, textvariable=self.login_wait_var, width=10).grid(row=0, column=1, sticky="w", pady=4)
        ttk.Label(advanced, text="Site retries").grid(row=0, column=2, sticky="w", padx=(16, 8), pady=5)
        ttk.Entry(advanced, textvariable=self.error_retries_var, width=10).grid(row=0, column=3, sticky="w", pady=4)
        ttk.Label(advanced, text="Game data retries").grid(row=0, column=4, sticky="w", padx=(16, 8), pady=5)
        ttk.Entry(advanced, textvariable=self.game_data_retries_var, width=10).grid(row=0, column=5, sticky="w", pady=4)
        ttk.Checkbutton(advanced, text="Clear logs on start", variable=self.clear_logs_on_start_var).grid(
            row=0, column=6, sticky="w", padx=(16, 0), pady=4
        )

        action_area = tk.Frame(self.root, bg=BG_COLOR)
        action_area.grid(row=2, column=0, sticky="ew", padx=14, pady=(2, 0))
        action_area.columnconfigure(0, weight=3)
        action_area.columnconfigure(1, weight=1)

        primary_actions = tk.Frame(action_area, bg=PANEL_COLOR, bd=0, relief="flat", highlightthickness=1, highlightbackground="#edf3fb")
        primary_actions.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        primary_actions.columnconfigure(0, weight=1)
        primary_actions.columnconfigure(1, weight=1)
        primary_actions.columnconfigure(2, weight=1)

        self.start_chrome_btn = self.create_action_button(
            primary_actions,
            "◉",
            "Start Chrome",
            "Open Chrome browser",
            self.start_chrome,
            "#4F8DF7",
            "#2563EB",
            "#3B82F6",
            0,
        )
        self.start_bot_btn = self.create_action_button(
            primary_actions,
            "▶",
            "Start Bot",
            "Begin automation",
            self.start_bot,
            "#34C759",
            "#16A34A",
            "#22B653",
            1,
        )
        self.stop_bot_btn = self.create_action_button(
            primary_actions,
            "■",
            "Stop Bot",
            "Stop running process",
            self.stop_bot,
            "#FF6B6B",
            "#DC3545",
            "#EF4444",
            2,
            state="disabled",
        )

        utility_actions = tk.Frame(action_area, bg=PANEL_COLOR, bd=0, relief="flat", highlightthickness=1, highlightbackground="#edf3fb")
        utility_actions.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        utility_actions.columnconfigure(0, weight=1)
        utility_actions.columnconfigure(1, weight=1)
        ttk.Button(utility_actions, text="Open Project Folder", command=self.open_project_folder).grid(
            row=0, column=0, sticky="ew", padx=(18, 8), pady=28
        )
        ttk.Button(utility_actions, text="Clear Logs", command=self.clear_logs).grid(
            row=0, column=1, sticky="ew", padx=(8, 18), pady=28
        )

        log_card = tk.Frame(self.root, bg=PANEL_COLOR, bd=0, relief="flat", highlightthickness=1, highlightbackground="#edf3fb")
        log_card.grid(row=3, column=0, sticky="nsew", padx=22, pady=(8, 18))
        log_card.columnconfigure(1, weight=1)
        log_card.rowconfigure(2, weight=1)

        self.icon_label(log_card, "log", "#7a35dc", 0)
        tk.Label(log_card, text="Live Logs", bg=PANEL_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 14, "bold")).grid(
            row=0, column=1, sticky="w", pady=(16, 0)
        )
        tk.Label(
            log_card,
            text="Real-time progress and messages will appear here.",
            bg=PANEL_COLOR,
            fg="#405993",
            font=("Segoe UI", 9),
        ).grid(row=1, column=1, sticky="w", pady=(3, 8))

        ttk.Checkbutton(log_card, text="Auto-scroll", variable=self.auto_scroll_var).grid(
            row=0, column=2, rowspan=2, sticky="e", padx=(0, 12), pady=18
        )
        ttk.Button(log_card, text="Copy Logs", command=self.copy_logs).grid(row=0, column=3, rowspan=2, sticky="e", padx=(0, 18), pady=18)

        self.log_text = scrolledtext.ScrolledText(
            log_card,
            wrap="word",
            height=20,
            font=("Consolas", 10),
            bg=LOG_BG,
            fg=LOG_FG,
            insertbackground=LOG_FG,
            relief="flat",
            borderwidth=0,
            padx=12,
            pady=10,
        )
        self.log_text.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=18, pady=(0, 18))
        self.log_text.tag_configure("system", foreground="#69e1ff")
        self.log_text.tag_configure("success", foreground="#47cd89")
        self.log_text.tag_configure("warning", foreground="#fdb022")
        self.log_text.tag_configure("error", foreground="#ff6b6b")
        self.log_text.tag_configure("info", foreground=LOG_FG)
        self.log_text.tag_configure("time", foreground="#6ce9a6")
        self.log_text.tag_configure("level", foreground="#69e1ff")

        self.append_log("Desktop app ready.")
        self.append_log(f"Project folder: {PROJECT_DIR}")
        self.append_log(f"Bot script: {self.script_var.get()}")
        self.root.after(100, self.reset_path_views)

    def update_start_row_state(self):
        if self.start_mode_var.get() == "Specific row":
            self.start_row_entry.configure(state="normal")
        else:
            self.start_row_entry.configure(state="disabled")

    def reset_path_views(self):
        self.script_entry.xview_moveto(0)
        self.input_entry.xview_moveto(0)

    def browse_input_file(self):
        path = filedialog.askopenfilename(
            initialdir=PROJECT_DIR,
            title="Select input Excel or CSV",
            filetypes=[
                ("Excel/CSV files", "*.xlsx *.xls *.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.input_file_var.set(path)
            self.root.after(50, self.reset_path_views)

    def build_bot_env(self):
        env = os.environ.copy()
        mode = self.mode_var.get()

        if mode == "Dry run - Single":
            env["DRY_RUN"] = "1"
            env["SUBMIT_EACH_BET"] = "0"
            env["USE_MULTIPLE"] = "0"
        elif mode == "Dry run - Multiple row":
            env["DRY_RUN"] = "1"
            env["SUBMIT_EACH_BET"] = "0"
            env["USE_MULTIPLE"] = "1"
        elif mode == "Real submit - Single":
            env["DRY_RUN"] = "0"
            env["SUBMIT_EACH_BET"] = "1"
            env["USE_MULTIPLE"] = "0"
        elif mode == "Real submit - Multiple row":
            env["DRY_RUN"] = "0"
            env["SUBMIT_EACH_BET"] = "1"
            env["USE_MULTIPLE"] = "1"
        else:
            env["DRY_RUN"] = "0"
            env["SUBMIT_EACH_BET"] = "0"
            env["USE_MULTIPLE"] = "0"

        env["INPUT_FILE"] = self.input_file_var.get().strip()
        env["STAKE"] = self.stake_var.get().strip()
        env["REQUIRE_LOGIN"] = "1"
        env["LOGIN_WAIT"] = self.login_wait_var.get().strip() or "900"
        env["ERROR_RETRIES"] = self.error_retries_var.get().strip() or "3"
        env["GAME_DATA_RETRIES"] = self.game_data_retries_var.get().strip() or "3"

        start_mode = self.start_mode_var.get()
        env.pop("START_ROW", None)
        if start_mode == "Resume from latest result":
            env["START_MODE"] = "resume"
        elif start_mode == "Specific row":
            env["START_ROW"] = self.start_row_var.get().strip()
            env.pop("START_MODE", None)
        else:
            env["START_MODE"] = "start"

        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        return env

    def validate_form(self):
        input_file = Path(self.input_file_var.get().strip())

        if not getattr(sys, "frozen", False) and not BOT_SCRIPT.exists():
            messagebox.showerror("Missing bot script", f"{BOT_SCRIPT_NAME} was not found in the project folder.")
            return False

        if not input_file.exists() or input_file.suffix.lower() not in EXCEL_EXTENSIONS:
            messagebox.showerror("Invalid input file", "Please select a valid .xlsx, .xls, or .csv input file.")
            return False

        if not self.stake_var.get().strip():
            messagebox.showerror("Missing stake", "Please enter a stake amount.")
            return False

        numeric_fields = [
            ("Login wait", self.login_wait_var.get()),
            ("Site retries", self.error_retries_var.get()),
            ("Game data retries", self.game_data_retries_var.get()),
        ]
        for label, value in numeric_fields:
            try:
                if int(value) < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid value", f"{label} must be a positive number.")
                return False

        if self.start_mode_var.get() == "Specific row":
            try:
                if int(self.start_row_var.get()) <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid row", "Start row must be a positive number.")
                return False

        if self.mode_var.get().startswith("Real submit"):
            return messagebox.askyesno(
                "Confirm real submit",
                "This mode can click final Submit on the betting site.\n\nDo you want to continue?",
            )

        return True

    def start_chrome(self):
        if self.chrome_process and self.chrome_process.poll() is None:
            self.append_log("Chrome already started from this app.")
            return

        system = platform.system().lower()
        if system == "windows":
            chrome_paths = [
                Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            ]
            chrome = next((path for path in chrome_paths if path.exists()), None)
            if not chrome:
                messagebox.showerror("Chrome not found", "Google Chrome was not found in Program Files.")
                return
            user_data_dir = str(Path(os.environ.get("TEMP", str(PROJECT_DIR))) / "chrome-debug")
            cmd = [str(chrome), "--remote-debugging-port=9222", f"--user-data-dir={user_data_dir}"]
        elif system == "darwin":
            cmd = [
                "open",
                "-na",
                "Google Chrome",
                "--args",
                "--remote-debugging-port=9222",
                f"--user-data-dir={Path.home() / 'chrome-debug'}",
            ]
        else:
            cmd = ["google-chrome", "--remote-debugging-port=9222", "--user-data-dir=/tmp/chrome-debug"]

        try:
            self.chrome_process = subprocess.Popen(cmd, cwd=PROJECT_DIR)
            self.append_log("Chrome started with remote debugging on port 9222.")
            self.append_log("Complete Cloudflare/login manually in Chrome before starting the bot.")
            self.status_detail_var.set("Chrome is open. Complete login manually.")
        except Exception as exc:
            messagebox.showerror("Chrome start failed", str(exc))
            self.append_log(f"Chrome start failed: {exc}")

    def start_bot(self):
        if self.bot_process and self.bot_process.poll() is None:
            messagebox.showinfo("Bot already running", "The bot is already running.")
            return

        if not self.validate_form():
            return

        if self.clear_logs_on_start_var.get():
            self.clear_logs()

        env = self.build_bot_env()
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, BOT_RUNNER_ARG]
        else:
            cmd = [sys.executable, str(BOT_SCRIPT)]

        self.append_log("Starting bot...")
        self.append_log(f"Mode: {self.mode_var.get()}")
        self.append_log(f"Input file: {env['INPUT_FILE']}")

        try:
            self.bot_process = subprocess.Popen(
                cmd,
                cwd=PROJECT_DIR,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except Exception as exc:
            messagebox.showerror("Bot start failed", str(exc))
            self.append_log(f"Bot start failed: {exc}")
            return

        self.start_bot_btn.configure(state="disabled")
        self.stop_bot_btn.configure(state="normal")
        self.status_var.set("Bot running")
        self.status_detail_var.set("Automation is processing rows.")

        thread = threading.Thread(target=self.read_bot_output, daemon=True)
        thread.start()

    def read_bot_output(self):
        try:
            for line in self.bot_process.stdout:
                self.log_queue.put(line.rstrip())
            return_code = self.bot_process.wait()
            self.log_queue.put(f"Bot finished with exit code {return_code}.")
        except Exception as exc:
            self.log_queue.put(f"Bot output reader failed: {exc}")
        finally:
            self.log_queue.put("__BOT_DONE__")

    def stop_bot(self):
        if not self.bot_process or self.bot_process.poll() is not None:
            return

        if not messagebox.askyesno("Stop bot", "Do you want to stop the running bot?"):
            return

        self.append_log("Stopping bot...")
        self.bot_process.terminate()
        self.root.after(5000, self.kill_bot_if_needed)

    def kill_bot_if_needed(self):
        if self.bot_process and self.bot_process.poll() is None:
            self.append_log("Bot did not stop in time. Killing process.")
            self.bot_process.kill()

    def drain_log_queue(self):
        while True:
            try:
                item = self.log_queue.get_nowait()
            except queue.Empty:
                break

            if item == "__BOT_DONE__":
                self.start_bot_btn.configure(state="normal")
                self.stop_bot_btn.configure(state="disabled")
                self.status_var.set("Ready")
                self.status_detail_var.set("No process running")
            else:
                self.append_log(item)

        self.root.after(150, self.drain_log_queue)

    def update_clock(self):
        self.clock_var.set(datetime.now().strftime("%b %d, %Y   %H:%M"))
        self.root.after(30000, self.update_clock)

    def copy_logs(self):
        text = self.log_text.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.append_log("Logs copied to clipboard.")

    def log_level_for_message(self, message):
        lower = message.lower()
        if "error" in lower or "failed" in lower or "traceback" in lower or "❌" in message:
            return "Error", "error"
        if "warning" in lower or "skipping" in lower or "⚠" in message:
            return "Warning", "warning"
        if "success" in lower or "submitted" in lower or "completed successfully" in lower or "✅" in message or "✔" in message:
            return "Success", "success"
        if "desktop app" in lower or "project folder" in lower or "bot script" in lower or "starting bot" in lower:
            return "System", "system"
        return "Info", "info"

    def append_log(self, message):
        level, tag = self.log_level_for_message(message)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] ", ("time",))
        self.log_text.insert("end", f"{level:<8} ", (tag,))
        self.log_text.insert("end", f"{message}\n", (tag,))
        if self.auto_scroll_var.get():
            self.log_text.see("end")

    def clear_logs(self):
        self.log_text.delete("1.0", "end")

    def open_project_folder(self):
        system = platform.system().lower()
        try:
            if system == "windows":
                os.startfile(PROJECT_DIR)
            elif system == "darwin":
                subprocess.Popen(["open", str(PROJECT_DIR)])
            else:
                subprocess.Popen(["xdg-open", str(PROJECT_DIR)])
        except Exception as exc:
            messagebox.showerror("Open folder failed", str(exc))

    def on_close(self):
        if self.bot_process and self.bot_process.poll() is None:
            if not messagebox.askyesno("Bot running", "The bot is still running. Stop it and close the app?"):
                return
            self.bot_process.terminate()
        self.root.destroy()


def main():
    root = Tk()
    app = LuckyNumbersBotApp(root)
    app.update_start_row_state()
    root.mainloop()


if __name__ == "__main__":
    if BOT_RUNNER_ARG in sys.argv:
        runpy.run_path(str(Path(getattr(sys, "_MEIPASS", PROJECT_DIR)) / BOT_SCRIPT_NAME), run_name="__main__")
    else:
        main()
