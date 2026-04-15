import tkinter as tk
import os
import sys


def create_icon_image(root):
    """Load icon from mbw.png next to the executable or script."""
    # Find the icon file - works both when run as script and as PyInstaller bundle
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    icon_path = os.path.join(base_dir, "mbw.png")

    if not os.path.exists(icon_path):
        return None

    try:
        img = tk.PhotoImage(file=icon_path)
        # Resize to 64x64 for window icon
        scale = img.width() // 64
        if scale > 1:
            img = img.subsample(scale, scale)
        return img
    except Exception:
        return None
