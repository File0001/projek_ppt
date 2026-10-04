"""Komponen widget kustom kecil yang dipakai berulang di UI."""

import tkinter as tk


def badge(parent, text, bg="#EBEBFF", fg="#4E4EBC"):
    """Label 'pill' berwarna untuk badge status/informasi."""
    return tk.Label(
        parent,
        text=text,
        bg=bg,
        fg=fg,
        font=("Segoe UI", 8, "bold"),
        padx=9,
        pady=4,
    )


def inline_badge(parent, text, bg="#E5F6EF", fg="#2E8A68"):
    """Badge kecil (padding lebih rapat) untuk header judul."""
    return tk.Label(
        parent,
        text=text,
        bg=bg,
        fg=fg,
        font=("Segoe UI", 8, "bold"),
        padx=4,
        pady=3,
    )
