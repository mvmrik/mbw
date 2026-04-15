import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys

from i18n import t, AVAILABLE_LANGUAGES
from calculator import encode, decode, parse_encoded_string, format_encoded, validate_password

# --- Config file path ---
def get_config_path():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    config_dir = os.path.join(base, "SPSApp")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "settings.json")

def load_settings():
    try:
        with open(get_config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"language": "en"}

def save_settings(settings: dict):
    with open(get_config_path(), "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


# --- Main App ---
class SPSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.lang = self.settings.get("language", "en")

        self.title(t(self.lang, "app_title"))
        self.resizable(True, True)
        self.minsize(700, 550)

        # Center window
        self.update_idletasks()
        w, h = 800, 650
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.sps_tab = SPSTab(self.notebook, self.lang, self)
        self.settings_tab = SettingsTab(self.notebook, self.lang, self)

        self.notebook.add(self.sps_tab, text=t(self.lang, "tab_sps"))
        self.notebook.add(self.settings_tab, text=t(self.lang, "tab_settings"))

    def change_language(self, new_lang: str):
        self.lang = new_lang
        self.settings["language"] = new_lang
        save_settings(self.settings)
        self.title(t(self.lang, "app_title"))
        self._build_ui()


# --- SPS Tab ---
class SPSTab(tk.Frame):
    def __init__(self, parent, lang: str, app: SPSApp):
        super().__init__(parent)
        self.lang = lang
        self.app = app
        self._build()

    def _build(self):
        lang = self.lang

        # Title
        title = tk.Label(self, text=t(lang, "sps_title"), font=("Helvetica", 14, "bold"))
        title.pack(pady=(12, 4))

        desc = tk.Label(self, text=t(lang, "sps_description"), justify=tk.LEFT,
                        wraplength=680, font=("Helvetica", 9))
        desc.pack(padx=16, pady=(0, 8))

        # Main frame with scrollbar
        outer = tk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True, padx=12)

        canvas = tk.Canvas(outer, borderwidth=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mousewheel scroll
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        sf = self.scroll_frame

        # --- Seed words section ---
        words_lbl = tk.Label(sf, text=t(lang, "label_seed_words"), font=("Helvetica", 10, "bold"))
        words_lbl.grid(row=0, column=0, columnspan=8, sticky="w", pady=(8, 4))

        self.word_entries = []
        for i in range(24):
            row = 1 + i // 4
            col = (i % 4) * 2
            num_lbl = tk.Label(sf, text=f"{i+1}.", width=3, anchor="e")
            num_lbl.grid(row=row, column=col, sticky="e", padx=(4, 2))
            entry = tk.Entry(sf, width=14, font=("Helvetica", 10))
            entry.grid(row=row, column=col+1, padx=(0, 8), pady=2, sticky="w")
            self.word_entries.append(entry)

        # --- Passwords section ---
        pass_row = 8

        p1_lbl = tk.Label(sf, text=t(lang, "label_password1"), font=("Helvetica", 10, "bold"))
        p1_lbl.grid(row=pass_row, column=0, columnspan=2, sticky="w", pady=(12, 2))

        self.pass1_entry = tk.Entry(sf, width=50, font=("Helvetica", 10))
        self.pass1_entry.grid(row=pass_row+1, column=0, columnspan=7, sticky="ew", padx=4, pady=2)

        p2_lbl = tk.Label(sf, text=t(lang, "label_password2"), font=("Helvetica", 10, "bold"))
        p2_lbl.grid(row=pass_row+2, column=0, columnspan=2, sticky="w", pady=(8, 2))

        self.pass2_entry = tk.Entry(sf, width=50, font=("Helvetica", 10))
        self.pass2_entry.grid(row=pass_row+3, column=0, columnspan=7, sticky="ew", padx=4, pady=2)

        # --- Encoded input section (for decode) ---
        enc_lbl = tk.Label(sf, text=t(lang, "label_encoded_input"), font=("Helvetica", 10, "bold"))
        enc_lbl.grid(row=pass_row+4, column=0, columnspan=2, sticky="w", pady=(12, 2))

        self.encoded_entry = tk.Entry(sf, width=50, font=("Helvetica", 10))
        self.encoded_entry.grid(row=pass_row+5, column=0, columnspan=7, sticky="ew", padx=4, pady=2)

        # --- Buttons ---
        btn_frame = tk.Frame(sf)
        btn_frame.grid(row=pass_row+6, column=0, columnspan=8, pady=12)

        encode_btn = tk.Button(btn_frame, text=t(lang, "btn_encode"),
                               font=("Helvetica", 10, "bold"),
                               bg="#2e7d32", fg="white", padx=12, pady=6,
                               command=self._do_encode)
        encode_btn.pack(side=tk.LEFT, padx=6)

        decode_btn = tk.Button(btn_frame, text=t(lang, "btn_decode"),
                               font=("Helvetica", 10, "bold"),
                               bg="#1565c0", fg="white", padx=12, pady=6,
                               command=self._do_decode)
        decode_btn.pack(side=tk.LEFT, padx=6)

        clear_btn = tk.Button(btn_frame, text=t(lang, "btn_clear"),
                              font=("Helvetica", 10),
                              bg="#c62828", fg="white", padx=12, pady=6,
                              command=self._do_clear)
        clear_btn.pack(side=tk.LEFT, padx=6)

        # --- Result section ---
        result_lbl = tk.Label(sf, text=t(lang, "label_result"), font=("Helvetica", 10, "bold"))
        result_lbl.grid(row=pass_row+7, column=0, columnspan=2, sticky="w", pady=(4, 2))

        result_frame = tk.Frame(sf)
        result_frame.grid(row=pass_row+8, column=0, columnspan=8, sticky="ew", padx=4, pady=2)

        self.result_text = tk.Text(result_frame, height=4, font=("Courier", 10),
                                   state=tk.DISABLED, wrap=tk.WORD,
                                   bg="#f5f5f5", relief=tk.SUNKEN)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.copy_btn = tk.Button(sf, text=t(lang, "copy_result"),
                                  font=("Helvetica", 9),
                                  command=self._copy_result)
        self.copy_btn.grid(row=pass_row+9, column=0, columnspan=3, sticky="w", padx=4, pady=4)

        sf.columnconfigure(1, weight=1)
        sf.columnconfigure(3, weight=1)
        sf.columnconfigure(5, weight=1)
        sf.columnconfigure(7, weight=1)

    def _get_words(self) -> list[str]:
        words = []
        for e in self.word_entries:
            w = e.get().strip()
            if w:
                words.append(w)
        return words

    def _show_result(self, text: str):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)

    def _copy_result(self):
        text = self.result_text.get("1.0", tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            orig = self.copy_btn.cget("text")
            self.copy_btn.config(text=t(self.lang, "copied"))
            self.after(1500, lambda: self.copy_btn.config(text=orig))

    def _parse_error(self, err: str) -> str:
        """Convert internal error string to translated message."""
        lang = self.lang
        if not err:
            return ""
        if ":" in err:
            parts = err.split(":")
            key = parts[0]
            kwargs = {}
            for p in parts[1:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    try:
                        kwargs[k] = int(v)
                    except ValueError:
                        kwargs[k] = v
            return t(lang, key, **kwargs)
        return t(lang, err)

    def _do_encode(self):
        lang = self.lang
        words = self._get_words()
        if not words:
            messagebox.showerror("Error", t(lang, "err_empty_words"))
            return

        pass1 = self.pass1_entry.get()
        pass2 = self.pass2_entry.get()
        if not pass1 or not pass2:
            messagebox.showerror("Error", t(lang, "err_empty_passwords"))
            return

        result, err = encode(words, pass1, pass2)
        if err:
            messagebox.showerror("Error", self._parse_error(err))
            return

        self._show_result(format_encoded(result))

    def _do_decode(self):
        lang = self.lang
        encoded_str = self.encoded_entry.get().strip()
        if not encoded_str:
            messagebox.showerror("Error", t(lang, "err_empty_encoded"))
            return

        pass1 = self.pass1_entry.get()
        pass2 = self.pass2_entry.get()
        if not pass1 or not pass2:
            messagebox.showerror("Error", t(lang, "err_empty_passwords"))
            return

        numbers, err = parse_encoded_string(encoded_str)
        if err:
            messagebox.showerror("Error", self._parse_error(err))
            return

        words, err = decode(numbers, pass1, pass2)
        if err:
            messagebox.showerror("Error", self._parse_error(err))
            return

        # Fill word entries with decoded words
        for i, entry in enumerate(self.word_entries):
            entry.delete(0, tk.END)
            if i < len(words):
                entry.insert(0, words[i])

        self._show_result(" ".join(words))

    def _do_clear(self):
        for entry in self.word_entries:
            entry.delete(0, tk.END)
        self.pass1_entry.delete(0, tk.END)
        self.pass2_entry.delete(0, tk.END)
        self.encoded_entry.delete(0, tk.END)
        self._show_result("")


# --- Settings Tab ---
class SettingsTab(tk.Frame):
    def __init__(self, parent, lang: str, app: SPSApp):
        super().__init__(parent)
        self.lang = lang
        self.app = app
        self._build()

    def _build(self):
        lang = self.lang

        title = tk.Label(self, text=t(lang, "settings_title"),
                         font=("Helvetica", 14, "bold"))
        title.pack(pady=(24, 16))

        form = tk.Frame(self)
        form.pack(padx=40, pady=8, anchor="w")

        lang_lbl = tk.Label(form, text=t(lang, "label_language"),
                            font=("Helvetica", 11))
        lang_lbl.grid(row=0, column=0, sticky="w", padx=(0, 16), pady=8)

        self.lang_var = tk.StringVar(value=self.app.lang)
        lang_names = list(AVAILABLE_LANGUAGES.values())
        lang_codes = list(AVAILABLE_LANGUAGES.keys())

        # Display names in dropdown
        display_names = [t(lang, f"lang_{code}") for code in lang_codes]
        current_display = t(lang, f"lang_{self.app.lang}")

        self.lang_var_display = tk.StringVar(value=current_display)
        self._lang_codes = lang_codes
        self._lang_display = display_names

        lang_menu = ttk.Combobox(form, textvariable=self.lang_var_display,
                                 values=display_names, state="readonly", width=20)
        lang_menu.grid(row=0, column=1, sticky="w")

        save_btn = tk.Button(self, text=t(lang, "btn_save_settings"),
                             font=("Helvetica", 10, "bold"),
                             bg="#1565c0", fg="white", padx=14, pady=6,
                             command=self._save)
        save_btn.pack(pady=16)

        self.status_lbl = tk.Label(self, text="", font=("Helvetica", 9), fg="green")
        self.status_lbl.pack()

    def _save(self):
        selected_display = self.lang_var_display.get()
        # Find code from display name
        new_lang = self.app.lang
        for code in self._lang_codes:
            if t(self.lang, f"lang_{code}") == selected_display:
                new_lang = code
                break

        if new_lang != self.app.lang:
            self.app.change_language(new_lang)
        else:
            self.status_lbl.config(text=t(self.lang, "settings_saved"))
            self.after(2000, lambda: self.status_lbl.config(text=""))


if __name__ == "__main__":
    app = SPSApp()
    app.mainloop()
