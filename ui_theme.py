import tkinter as tk
from tkinter import ttk

COLORS = {
    "background": "#F7F9FC",
    "card": "#FFFFFF",
    "primary": "#4C8DF6",
    "primary_hover": "#3978E7",
    "text": "#1F2937",
    "muted": "#7A8AA0",
    "border": "#E4EAF2",
    "disabled": "#EEF2F7",
    "success": "#16A34A",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "selected": "#EEF5FF",
}

FONT_FAMILY = "맑은 고딕"


def get_font(size, weight="normal"):
    return (FONT_FAMILY, size, weight)


def configure_styles(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("App.TFrame", background=COLORS["background"])
    style.configure("Card.TFrame", background=COLORS["card"], bordercolor=COLORS["border"], relief="solid", borderwidth=1)
    style.configure("Header.TFrame", background=COLORS["card"])
    style.configure("Title.TLabel", background=COLORS["card"], foreground=COLORS["text"], font=get_font(21, "bold"))
    style.configure("Subtitle.TLabel", background=COLORS["card"], foreground=COLORS["muted"], font=get_font(11))
    style.configure("CardTitle.TLabel", background=COLORS["card"], foreground=COLORS["text"], font=get_font(12, "bold"))
    style.configure("Body.TLabel", background=COLORS["card"], foreground=COLORS["text"], font=get_font(11))
    style.configure("Muted.TLabel", background=COLORS["card"], foreground=COLORS["muted"], font=get_font(10))
    style.configure("SummaryValue.TLabel", background=COLORS["card"], foreground=COLORS["text"], font=get_font(13, "bold"))
    style.configure("SummaryLabel.TLabel", background=COLORS["card"], foreground=COLORS["muted"], font=get_font(11))
    style.configure("Primary.TButton", background=COLORS["primary"], foreground="white", font=get_font(10, "bold"), padding=(16, 9), borderwidth=0)
    style.map("Primary.TButton", background=[("active", COLORS["primary_hover"]), ("disabled", COLORS["disabled"])], foreground=[("disabled", COLORS["muted"])])
    style.configure("Secondary.TButton", background=COLORS["card"], foreground=COLORS["text"], font=get_font(10), padding=(13, 8), bordercolor=COLORS["border"], borderwidth=1)
    style.map("Secondary.TButton", background=[("active", COLORS["disabled"])])
    style.configure("Danger.TButton", background=COLORS["card"], foreground=COLORS["error"], font=get_font(10), padding=(13, 8), bordercolor=COLORS["error"], borderwidth=1)
    style.map("Danger.TButton", background=[("active", "#FFF1F2"), ("disabled", COLORS["disabled"])], foreground=[("disabled", COLORS["muted"])])
    style.configure("Search.TEntry", fieldbackground=COLORS["card"], foreground=COLORS["text"], padding=8)
    style.configure("Horizontal.TProgressbar", troughcolor=COLORS["disabled"], background=COLORS["primary"], borderwidth=0, thickness=7)
    return style


def create_card(parent, padding=16):
    outer = ttk.Frame(parent, style="Card.TFrame", padding=padding)
    return outer


def create_badge(parent, text, color, background):
    return tk.Label(parent, text=text, bg=background, fg=color, font=get_font(9, "bold"), padx=8, pady=3)


def create_count_badge(parent, text):
    return tk.Label(parent, text=text, bg="#EEF4FF", fg=COLORS["primary"], font=get_font(11, "bold"), padx=8, pady=2, height=1)
