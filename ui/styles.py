"""Konfigurasi tema & style ttk untuk aplikasi.

Dipindah apa adanya dari create_styles() monolit asli.
"""

import tkinter as tk
from tkinter import ttk


def create_styles():
    """Terapkan tema clam + semua style kustom. Mengembalikan objek Style."""
    style = ttk.Style()

    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TFrame", background="#F4F6FA")
    style.configure("Card.TFrame", background="#FFFFFF")

    style.configure(
        "TLabel",
        background="#FFFFFF",
        foreground="#172033",
        font=("Segoe UI", 9),
    )
    style.configure(
        "Title.TLabel",
        background="#F4F6FA",
        foreground="#172033",
        font=("Segoe UI", 23, "bold"),
    )
    style.configure(
        "Subtitle.TLabel",
        background="#F4F6FA",
        foreground="#6B7280",
        font=("Segoe UI", 10),
    )
    style.configure(
        "Section.TLabel",
        background="#FFFFFF",
        foreground="#172033",
        font=("Segoe UI", 11, "bold"),
    )
    style.configure(
        "Muted.TLabel",
        background="#FFFFFF",
        foreground="#7A8496",
        font=("Segoe UI", 8),
    )
    style.configure(
        "Main.TButton",
        font=("Segoe UI", 8, "bold"),
        padding=(7, 6),
    )
    style.configure("TEntry", font=("Segoe UI", 9))
    style.configure(
        "Process.TButton",
        font=("Segoe UI", 10, "bold"),
        padding=(16, 9),
        background="#5656D9",
        foreground="#FFFFFF",
        borderwidth=0,
    )
    style.map(
        "Process.TButton",
        background=[
            ("active", "#4646C4"),
            ("disabled", "#B7B7E6"),
        ],
        foreground=[("disabled", "#F0F0FA")],
    )

    style.configure(
        "Treeview",
        background="#FFFFFF",
        fieldbackground="#FFFFFF",
        foreground="#172033",
        rowheight=29,
        borderwidth=0,
        font=("Segoe UI", 8),
    )
    style.configure(
        "Treeview.Heading",
        background="#F3F5F9",
        foreground="#5C6678",
        font=("Segoe UI", 8, "bold"),
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", "#E8E8FF")],
        foreground=[("selected", "#3535A0")],
    )
    style.configure(
        "Horizontal.TProgressbar",
        troughcolor="#E7EAF1",
        background="#5656D9",
        borderwidth=0,
        thickness=8,
    )

    return style
