import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys

import threading

from i18n import t, AVAILABLE_LANGUAGES
from calculator import encode, decode, parse_encoded_string, format_encoded
from bip39_wordlist import BIP39_INDEX, BIP39_WORDS
from icon import create_icon_image
from portfolio import (load_portfolio, save_portfolio, add_address,
                       remove_address, update_label, total_btc, refresh_all)


# --- Autocomplete Word Entry ---
class WordEntry(tk.Frame):
    """Entry widget with BIP-39 autocomplete dropdown and duplicate detection."""

    MAX_SUGGESTIONS = 8

    def __init__(self, parent, width=13, on_change=None, get_used_words=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_change = on_change        # callback() when value changes
        self._get_used_words = get_used_words  # callback() -> set of used words
        self._autocomplete_open = False
        self._suppress_trace = False

        self._var = tk.StringVar()
        self._var.trace_add("write", self._on_type)

        self._entry = tk.Entry(self, textvariable=self._var,
                               width=width, font=("Helvetica", 10))
        self._entry.pack()

        # Popup listbox (created once, hidden until needed)
        self._popup = None
        self._listbox = None

        self._entry.bind("<Down>", self._on_down)
        self._entry.bind("<Escape>", lambda e: self._close_popup())
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<Return>", self._on_return)
        self._entry.bind("<Tab>", self._on_tab)

    # Public API to match tk.Entry interface used in SPSTab
    def get(self):
        return self._var.get()

    def delete(self, a, b):
        self._entry.delete(a, b)

    def insert(self, pos, value):
        self._suppress_trace = True
        self._entry.delete(0, tk.END)
        self._entry.insert(pos, value)
        self._suppress_trace = False

    def config(self, **kwargs):
        self._entry.config(**kwargs)

    def configure(self, **kwargs):
        self._entry.configure(**kwargs)

    def bind(self, sequence, func, add=None):
        self._entry.bind(sequence, func, add)

    # --- Autocomplete logic ---
    def _on_type(self, *_):
        if self._suppress_trace:
            return
        word = self._var.get().strip().lower()
        if self._on_change:
            self._on_change()
        if len(word) < 1:
            self._close_popup()
            return
        used = self._get_used_words() if self._get_used_words else set()
        matches = [w for w in BIP39_WORDS
                   if w.startswith(word) and w not in used][:self.MAX_SUGGESTIONS]
        if not matches or (len(matches) == 1 and matches[0] == word):
            self._close_popup()
            return
        self._show_popup(matches)

    def _show_popup(self, matches):
        if self._popup is None:
            self._popup = tk.Toplevel(self)
            self._popup.wm_overrideredirect(True)
            self._popup.wm_attributes("-topmost", True)
            frame = tk.Frame(self._popup, relief=tk.SOLID, borderwidth=1)
            frame.pack(fill=tk.BOTH, expand=True)
            self._listbox = tk.Listbox(frame, font=("Helvetica", 10),
                                       selectbackground="#1565c0",
                                       selectforeground="white",
                                       activestyle="none",
                                       height=self.MAX_SUGGESTIONS)
            self._listbox.pack(fill=tk.BOTH, expand=True)
            self._listbox.bind("<ButtonRelease-1>", self._on_select)
            self._listbox.bind("<Return>", self._on_select)
            self._listbox.bind("<Double-Button-1>", self._on_select)
            self._popup.bind("<FocusOut>", self._on_popup_focus_out)

        self._listbox.delete(0, tk.END)
        for w in matches:
            self._listbox.insert(tk.END, w)

        # Position popup below the entry
        self._entry.update_idletasks()
        x = self._entry.winfo_rootx()
        y = self._entry.winfo_rooty() + self._entry.winfo_height()
        w = self._entry.winfo_width()
        row_h = 18
        h = min(len(matches), self.MAX_SUGGESTIONS) * row_h + 4
        self._popup.geometry(f"{w}x{h}+{x}+{y}")
        self._popup.deiconify()
        self._autocomplete_open = True

    def _close_popup(self):
        if self._popup:
            self._popup.withdraw()
        self._autocomplete_open = False

    def _on_select(self, event=None):
        if self._listbox is None:
            return
        sel = self._listbox.curselection()
        if sel:
            word = self._listbox.get(sel[0])
            # Autocomplete list already excludes used words, but double-check
            used = self._get_used_words() if self._get_used_words else set()
            if word in used:
                self._close_popup()
                return
            self._suppress_trace = True
            self._var.set(word)
            self._entry.icursor(tk.END)
            self._suppress_trace = False
            self._close_popup()
            if self._on_change:
                self._on_change()
            self._entry.focus_set()

    def _on_down(self, event):
        if self._autocomplete_open and self._listbox:
            self._listbox.focus_set()
            if self._listbox.size() > 0:
                self._listbox.selection_set(0)
                self._listbox.activate(0)
        return "break"

    def _on_return(self, event):
        if self._autocomplete_open:
            self._on_select()
            return "break"

    def _on_tab(self, event):
        if self._autocomplete_open and self._listbox and self._listbox.size() > 0:
            self._listbox.selection_set(0)
            self._on_select()
            return "break"

    def _on_focus_out(self, event):
        # Delay so click on listbox registers first
        self.after(150, self._close_popup)

    def _on_popup_focus_out(self, event):
        self.after(150, self._close_popup)

# --- Config file path ---
def get_config_path():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    config_dir = os.path.join(base, "MyBitcoinWorld")
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
        self.minsize(800, 580)

        # Center window
        self.update_idletasks()
        w, h = 960, 700
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Set icon
        try:
            self._icon = create_icon_image(self)
            if self._icon:
                self.iconphoto(True, self._icon)
        except Exception:
            pass

        self._show_splash()

    def _show_splash(self):
        """Show splash image inside the main window, build UI after 3 seconds."""
        try:
            img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mbw.png")
            self._splash_img = tk.PhotoImage(file=img_path)
            # Scale down if too large (tk.PhotoImage supports subsample)
            w, h = self._splash_img.width(), self._splash_img.height()
            factor = max(1, w // 580, h // 580)
            if factor > 1:
                self._splash_img = self._splash_img.subsample(factor, factor)
        except Exception as e:
            print("Splash image error:", e)
            self._splash_img = None

        self._splash_frame = tk.Frame(self, bg="#1a1a2e")
        self._splash_frame.pack(fill=tk.BOTH, expand=True)

        if self._splash_img:
            lbl = tk.Label(self._splash_frame, image=self._splash_img,
                           bg="#1a1a2e", bd=0)
            lbl.place(relx=0.5, rely=0.5, anchor="center")
        else:
            tk.Label(self._splash_frame, text="My Bitcoin World",
                     font=("Helvetica", 28, "bold"),
                     fg="white", bg="#1a1a2e").place(relx=0.5, rely=0.5, anchor="center")

        self.after(3000, self._finish_splash)

    def _finish_splash(self):
        self._splash_frame.destroy()
        self._splash_img = None
        self._build_ui()

    def _build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.sps_tab = SPSTab(self.notebook, self.lang, self)
        self.portfolio_tab = PortfolioTab(self.notebook, self.lang, self)
        self.help_tab = HelpTab(self.notebook, self.lang)
        self.settings_tab = SettingsTab(self.notebook, self.lang, self)

        self.notebook.add(self.sps_tab, text=t(self.lang, "tab_sps"))
        self.notebook.add(self.portfolio_tab, text=t(self.lang, "tab_portfolio"))
        self.notebook.add(self.help_tab, text=t(self.lang, "tab_help"))
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
        self._word_count = 0  # tracks how many words entered
        self._build()

    def _build(self):
        lang = self.lang

        title = tk.Label(self, text=t(lang, "sps_title"), font=("Helvetica", 14, "bold"))
        title.pack(pady=(12, 4))

        desc = tk.Label(self, text=t(lang, "sps_description"), justify=tk.LEFT,
                        wraplength=700, font=("Helvetica", 9))
        desc.pack(padx=16, pady=(0, 6))

        # Scrollable area
        outer = tk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True, padx=12)

        self._canvas = tk.Canvas(outer, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self.scroll_frame = tk.Frame(self._canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        )
        self._canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas.bind_all("<MouseWheel>", lambda e: self._canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self._canvas.bind_all("<Button-4>", lambda e: self._canvas.yview_scroll(-1, "units"))
        self._canvas.bind_all("<Button-5>", lambda e: self._canvas.yview_scroll(1, "units"))

        sf = self.scroll_frame

        # --- Seed words ---
        words_lbl = tk.Label(sf, text=t(lang, "label_seed_words"), font=("Helvetica", 10, "bold"))
        words_lbl.grid(row=0, column=0, columnspan=12, sticky="w", pady=(8, 4), padx=4)

        self.word_entries = []
        self.word_status_labels = []

        for i in range(24):
            row = 1 + i // 4
            col = (i % 4) * 3

            num_lbl = tk.Label(sf, text=f"{i+1}.", width=3, anchor="e", font=("Helvetica", 9))
            num_lbl.grid(row=row, column=col, sticky="e", padx=(4, 1))

            entry = WordEntry(sf, width=13,
                              on_change=lambda idx=i: self._on_word_change(idx),
                              get_used_words=lambda idx=i: self._get_used_words(idx))
            entry.grid(row=row, column=col+1, padx=(0, 2), pady=2, sticky="w")

            status_lbl = tk.Label(sf, text="", font=("Helvetica", 8), width=3, anchor="w")
            status_lbl.grid(row=row, column=col+2, sticky="w", padx=(0, 6))

            self.word_entries.append(entry)
            self.word_status_labels.append(status_lbl)

        # Initially only first entry is enabled
        self._update_entry_states()

        # --- Passwords ---
        pass_row = 8

        p1_lbl = tk.Label(sf, text=t(lang, "label_password1"), font=("Helvetica", 10, "bold"))
        p1_lbl.grid(row=pass_row, column=0, columnspan=12, sticky="w", pady=(14, 2), padx=4)

        pass1_frame = tk.Frame(sf)
        pass1_frame.grid(row=pass_row+1, column=0, columnspan=12, sticky="w", padx=4, pady=2)
        self.pass1_cells = self._build_pass_cells(pass1_frame, 1)

        self.pass1_counter = tk.Label(sf, text="", font=("Helvetica", 9),
                                      fg="#888888", anchor="w")
        self.pass1_counter.grid(row=pass_row+2, column=0, columnspan=12, sticky="w", padx=4)

        p2_lbl = tk.Label(sf, text=t(lang, "label_password2"), font=("Helvetica", 10, "bold"))
        p2_lbl.grid(row=pass_row+3, column=0, columnspan=12, sticky="w", pady=(8, 2), padx=4)

        pass2_frame = tk.Frame(sf)
        pass2_frame.grid(row=pass_row+4, column=0, columnspan=12, sticky="w", padx=4, pady=2)
        self.pass2_cells = self._build_pass_cells(pass2_frame, 2)

        self.pass2_counter = tk.Label(sf, text="", font=("Helvetica", 9),
                                      fg="#888888", anchor="w")
        self.pass2_counter.grid(row=pass_row+5, column=0, columnspan=12, sticky="w", padx=4)

        # --- Encoded input ---
        enc_lbl = tk.Label(sf, text=t(lang, "label_encoded_input"), font=("Helvetica", 10, "bold"))
        enc_lbl.grid(row=pass_row+6, column=0, columnspan=4, sticky="w", pady=(14, 2), padx=4)

        self.encoded_entry = tk.Entry(sf, width=60, font=("Helvetica", 10))
        self.encoded_entry.grid(row=pass_row+7, column=0, columnspan=11, sticky="ew", padx=4, pady=2)

        # --- Buttons ---
        btn_frame = tk.Frame(sf)
        btn_frame.grid(row=pass_row+8, column=0, columnspan=12, pady=14)

        tk.Button(btn_frame, text=t(lang, "btn_encode"),
                  font=("Helvetica", 10, "bold"),
                  bg="#2e7d32", fg="white", padx=14, pady=7,
                  cursor="hand2",
                  command=self._do_encode).pack(side=tk.LEFT, padx=6)

        tk.Button(btn_frame, text=t(lang, "btn_decode"),
                  font=("Helvetica", 10, "bold"),
                  bg="#1565c0", fg="white", padx=14, pady=7,
                  cursor="hand2",
                  command=self._do_decode).pack(side=tk.LEFT, padx=6)

        tk.Button(btn_frame, text=t(lang, "btn_clear"),
                  font=("Helvetica", 10),
                  bg="#c62828", fg="white", padx=14, pady=7,
                  cursor="hand2",
                  command=self._do_clear).pack(side=tk.LEFT, padx=6)

        # --- Result ---
        tk.Label(sf, text=t(lang, "label_result"),
                 font=("Helvetica", 10, "bold")).grid(
            row=pass_row+9, column=0, columnspan=4, sticky="w", pady=(4, 2), padx=4)

        result_frame = tk.Frame(sf)
        result_frame.grid(row=pass_row+10, column=0, columnspan=12, sticky="ew", padx=4, pady=2)

        self.result_text = tk.Text(result_frame, height=4, font=("Courier", 10),
                                   state=tk.DISABLED, wrap=tk.WORD,
                                   bg="#f0f4f8", relief=tk.SUNKEN)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        self.copy_btn = tk.Button(sf, text=t(lang, "copy_result"),
                                  font=("Helvetica", 9), cursor="hand2",
                                  command=self._copy_result)
        self.copy_btn.grid(row=pass_row+11, column=0, columnspan=4, sticky="w", padx=4, pady=6)

        for c in range(0, 12, 3):
            sf.columnconfigure(c+1, weight=1)

    def _build_pass_cells(self, parent: tk.Frame, which: int) -> list:
        """Builds 24 single-character letter cells in a single row."""
        cells = []
        vcmd = self.register(lambda new_val, ch, w=which: self._pass_cell_validate(new_val, ch, w))
        for i in range(24):
            cell = tk.Entry(parent, width=2, font=("Helvetica", 11, "bold"),
                            justify="center", relief=tk.SOLID, bd=1,
                            bg="#f8f8f8")
            cell.config(validate="key", validatecommand=(vcmd, "%P", "%S"))
            cell.bind("<KeyRelease>", lambda e, w=which: self._on_pass_cell_key(e, w))
            cell.bind("<BackSpace>", lambda e, w=which: self._on_pass_cell_backspace(e, w))
            cell.grid(row=0, column=i, padx=1, pady=1)
            cells.append(cell)
        return cells

    def _pass_cell_validate(self, new_val: str, char: str, which: int) -> bool:
        """Allow only 1 ASCII letter per cell."""
        if char == "":
            return True
        if not (char.isalpha() and char.isascii()):
            return False
        # max 1 char
        return len(new_val) <= 1

    def _on_pass_cell_key(self, event, which: int):
        """After typing a letter in a cell, move focus to next cell."""
        cells = self.pass1_cells if which == 1 else self.pass2_cells
        widget = event.widget
        if widget not in cells:
            return
        idx = cells.index(widget)
        val = widget.get()
        if val and idx < len(cells) - 1:
            cells[idx + 1].focus_set()
            cells[idx + 1].selection_range(0, tk.END)
        self._update_pass_counter(which)

    def _on_pass_cell_backspace(self, event, which: int):
        """On backspace in empty cell, move to previous cell."""
        cells = self.pass1_cells if which == 1 else self.pass2_cells
        widget = event.widget
        if widget not in cells:
            return
        idx = cells.index(widget)
        if not widget.get() and idx > 0:
            cells[idx - 1].focus_set()
            cells[idx - 1].delete(0, tk.END)
        self._update_pass_counter(which)

    def _get_pass(self, which: int) -> str:
        """Returns password string from cells."""
        cells = self.pass1_cells if which == 1 else self.pass2_cells
        return "".join(c.get() for c in cells)

    def _get_used_words(self, exclude_idx: int) -> set:
        """Returns set of valid BIP-39 words already entered, excluding entry at exclude_idx."""
        used = set()
        for i, e in enumerate(self.word_entries):
            if i == exclude_idx:
                continue
            w = e.get().strip().lower()
            if w in BIP39_INDEX:
                used.add(w)
        return used

    # --- Sequential entry control ---
    def _on_word_change(self, idx: int):
        """Called on every keystroke in a word entry."""
        entry = self.word_entries[idx]
        word = entry.get().strip().lower()
        # If typed word is valid BIP-39 AND already used elsewhere → clear it
        if word in BIP39_INDEX and word in self._get_used_words(idx):
            entry.insert(0, "")
            entry.config(bg="white")
            self.word_status_labels[idx].config(text="")
            self._update_entry_states()
            return
        self._validate_word(idx)
        self._update_entry_states()

    def _update_entry_states(self):
        """Enable only filled entries + the next empty one. Lock the rest."""
        # Find how many consecutive valid words we have from the start
        first_empty = 0
        for i, entry in enumerate(self.word_entries):
            if entry.get().strip():
                first_empty = i + 1
            else:
                first_empty = i
                break

        for i, entry in enumerate(self.word_entries):
            if i <= first_empty:
                # Filled entries + next empty one: enabled
                entry.config(state=tk.NORMAL, bg=entry._entry.cget("bg"))
                entry._entry.config(state=tk.NORMAL)
            else:
                # Locked
                entry._entry.config(state="disabled", bg="#f0f0f0",
                                    disabledbackground="#f0f0f0",
                                    disabledforeground="#aaaaaa")
                self.word_status_labels[i].config(text="")

    # --- Word validation ---
    def _validate_word(self, idx: int):
        entry = self.word_entries[idx]
        lbl = self.word_status_labels[idx]
        word = entry.get().strip().lower()

        if not word:
            lbl.config(text="", fg="#888888")
            entry.config(bg="white")
        elif word not in BIP39_INDEX:
            lbl.config(text=t(self.lang, "word_invalid"), fg="#c62828")
            entry.config(bg="#fff0f0")
        else:
            lbl.config(text=t(self.lang, "word_valid"), fg="#2e7d32")
            entry.config(bg="#f0fff0")

        self._update_pass_counter(1)
        self._update_pass_counter(2)

    # --- Password counter ---
    def _update_pass_counter(self, which: int):
        word_count = len([e for e in self.word_entries if e.get().strip()])
        if word_count == 0:
            word_count = 12  # default hint

        counter_lbl = self.pass1_counter if which == 1 else self.pass2_counter
        current_len = len(self._get_pass(which))
        remaining = word_count - current_len

        if remaining > 0:
            counter_lbl.config(
                text=t(self.lang, "chars_remaining", n=remaining),
                fg="#e65100"
            )
        elif remaining == 0:
            counter_lbl.config(
                text=t(self.lang, "chars_ok"),
                fg="#2e7d32"
            )
        else:
            counter_lbl.config(
                text=t(self.lang, "chars_remaining", n=remaining),
                fg="#c62828"
            )

    # --- Helpers ---
    def _get_words(self) -> list:
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

    # --- Actions ---
    def _do_encode(self):
        lang = self.lang
        words = self._get_words()
        if not words:
            messagebox.showerror(t(lang, "app_title"), t(lang, "err_empty_words"))
            return

        pass1 = self._get_pass(1)
        pass2 = self._get_pass(2)
        if not pass1 or not pass2:
            messagebox.showerror(t(lang, "app_title"), t(lang, "err_empty_passwords"))
            return

        result, err = encode(words, pass1, pass2)
        if err:
            messagebox.showerror(t(lang, "app_title"), self._parse_error(err))
            return

        self._show_result(format_encoded(result))

    def _do_decode(self):
        lang = self.lang
        encoded_str = self.encoded_entry.get().strip()
        if not encoded_str:
            messagebox.showerror(t(lang, "app_title"), t(lang, "err_empty_encoded"))
            return

        pass1 = self._get_pass(1)
        pass2 = self._get_pass(2)
        if not pass1 or not pass2:
            messagebox.showerror(t(lang, "app_title"), t(lang, "err_empty_passwords"))
            return

        numbers, err = parse_encoded_string(encoded_str)
        if err:
            messagebox.showerror(t(lang, "app_title"), self._parse_error(err))
            return

        words, err = decode(numbers, pass1, pass2)
        if err:
            messagebox.showerror(t(lang, "app_title"), self._parse_error(err))
            return

        # Unlock all entries before filling
        for entry in self.word_entries:
            entry._entry.config(state=tk.NORMAL)

        for i, entry in enumerate(self.word_entries):
            entry.insert(0, "")
            if i < len(words):
                entry.insert(0, words[i])
            self._validate_word(i)

        self._update_entry_states()
        self._show_result(" ".join(words))

    def _do_clear(self):
        for i, entry in enumerate(self.word_entries):
            entry._entry.config(state=tk.NORMAL)
            entry.insert(0, "")
            entry.config(bg="white")
            self.word_status_labels[i].config(text="")
        self._update_entry_states()
        for c in self.pass1_cells:
            c.delete(0, tk.END)
        for c in self.pass2_cells:
            c.delete(0, tk.END)
        self.pass1_counter.config(text="")
        self.pass2_counter.config(text="")
        self.encoded_entry.delete(0, tk.END)
        self._show_result("")


# --- Portfolio Tab ---
class PortfolioTab(tk.Frame):

    ACCORDION_BG       = "#1e2a3a"
    ACCORDION_FG       = "#ffffff"
    ACCORDION_HOVER    = "#2a3a50"
    ACCORDION_OPEN_BG  = "#f0f4f8"
    ROW_EVEN           = "#f7f9fc"
    ROW_ODD            = "#edf1f7"
    GOLD               = "#f0a500"
    GREEN              = "#2e7d32"
    RED                = "#c62828"

    def __init__(self, parent, lang: str, app: SPSApp):
        super().__init__(parent)
        self.lang = lang
        self.app = app
        self._data = load_portfolio()
        self._accordion_open = {}   # address -> bool
        self._add_form_visible = False
        self._build()
        # Auto-refresh on open if we have addresses
        if self._data["addresses"]:
            self.after(300, self._do_refresh)

    # ------------------------------------------------------------------ build
    def _build(self):
        lang = self.lang

        # ── Top bar ──────────────────────────────────────────────────────────
        top = tk.Frame(self, bg="#0d1b2a")
        top.pack(fill=tk.X)

        tk.Label(top, text=t(lang, "portfolio_title"),
                 font=("Helvetica", 14, "bold"),
                 bg="#0d1b2a", fg="#f0a500").pack(side=tk.LEFT, padx=16, pady=10)

        self._refresh_btn = tk.Button(
            top, text=t(lang, "btn_refresh"),
            font=("Helvetica", 10, "bold"),
            bg="#f0a500", fg="#0d1b2a", padx=10, pady=4,
            relief=tk.FLAT, cursor="hand2",
            command=self._do_refresh)
        self._refresh_btn.pack(side=tk.RIGHT, padx=12, pady=8)

        tk.Button(top, text=t(lang, "btn_add_address"),
                  font=("Helvetica", 10),
                  bg="#2e7d32", fg="white", padx=10, pady=4,
                  relief=tk.FLAT, cursor="hand2",
                  command=self._toggle_add_form).pack(side=tk.RIGHT, padx=4, pady=8)

        # ── Summary bar ──────────────────────────────────────────────────────
        summary = tk.Frame(self, bg="#162232")
        summary.pack(fill=tk.X)

        self._total_lbl = tk.Label(summary, text="", font=("Helvetica", 11, "bold"),
                                   bg="#162232", fg="#ffffff")
        self._total_lbl.pack(side=tk.LEFT, padx=16, pady=6)

        self._price_lbl = tk.Label(summary, text="", font=("Helvetica", 10),
                                   bg="#162232", fg="#aaaaaa")
        self._price_lbl.pack(side=tk.LEFT, padx=16, pady=6)

        self._status_lbl = tk.Label(summary, text="", font=("Helvetica", 9),
                                    bg="#162232", fg="#888888")
        self._status_lbl.pack(side=tk.RIGHT, padx=16, pady=6)

        # ── Add-address form (hidden by default) ─────────────────────────────
        self._add_frame = tk.Frame(self, bg="#eaf4ea", relief=tk.GROOVE, bd=1)
        # Will be packed/unpacked by _toggle_add_form - do NOT pack here

        form_inner = tk.Frame(self._add_frame, bg="#eaf4ea")
        form_inner.pack(padx=16, pady=10, fill=tk.X)

        tk.Label(form_inner, text=t(lang, "label_address"),
                 font=("Helvetica", 10, "bold"), bg="#eaf4ea").grid(
            row=0, column=0, sticky="w", pady=4, padx=(0, 8))
        self._addr_entry = tk.Entry(form_inner, width=52, font=("Helvetica", 10))
        self._addr_entry.grid(row=0, column=1, sticky="ew", pady=4)

        tk.Label(form_inner, text=t(lang, "label_addr_label"),
                 font=("Helvetica", 10, "bold"), bg="#eaf4ea").grid(
            row=1, column=0, sticky="w", pady=4, padx=(0, 8))
        self._label_entry = tk.Entry(form_inner, width=52, font=("Helvetica", 10))
        self._label_entry.grid(row=1, column=1, sticky="ew", pady=4)

        form_btns = tk.Frame(self._add_frame, bg="#eaf4ea")
        form_btns.pack(pady=(0, 10))
        tk.Button(form_btns, text=t(lang, "btn_save_address"),
                  font=("Helvetica", 10, "bold"),
                  bg="#2e7d32", fg="white", padx=14, pady=4,
                  cursor="hand2", command=self._do_add).pack(side=tk.LEFT, padx=6)
        tk.Button(form_btns, text=t(lang, "btn_cancel"),
                  font=("Helvetica", 10),
                  bg="#888888", fg="white", padx=14, pady=4,
                  cursor="hand2", command=self._toggle_add_form).pack(side=tk.LEFT, padx=6)

        form_inner.columnconfigure(1, weight=1)

        # ── Scrollable accordion list ─────────────────────────────────────────
        self._list_outer = list_outer = tk.Frame(self)
        list_outer.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self._canvas = tk.Canvas(list_outer, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_outer, orient="vertical",
                                  command=self._canvas.yview)
        self._list_frame = tk.Frame(self._canvas)

        self._list_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0, 0), window=self._list_frame, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas.bind_all("<Button-4>",
            lambda e: self._canvas.yview_scroll(-1, "units"))
        self._canvas.bind_all("<Button-5>",
            lambda e: self._canvas.yview_scroll(1, "units"))
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._refresh_summary()
        self._rebuild_list()

    # ---------------------------------------------------------------- summary
    def _refresh_summary(self):
        lang = self.lang
        btc = total_btc(self._data)
        price = self._data.get("btc_usd")
        updated = self._data.get("btc_usd_updated")

        if price:
            usd = btc * price
            self._total_lbl.config(
                text=f"{t(lang, 'portfolio_total')}  {btc:.8f} BTC  ≈  ${usd:,.2f}")
            self._price_lbl.config(
                text=f"{t(lang, 'portfolio_btc_price')}  ${price:,.2f}")
        else:
            self._total_lbl.config(
                text=f"{t(lang, 'portfolio_total')}  {btc:.8f} BTC")
            self._price_lbl.config(
                text=f"{t(lang, 'portfolio_btc_price')}  {t(lang, 'portfolio_offline')}")

        upd_text = updated or t(lang, "portfolio_never")
        self._status_lbl.config(
            text=f"{t(lang, 'portfolio_last_updated')} {upd_text}")

    # ----------------------------------------------------------- accordion list
    def _rebuild_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

        addresses = self._data.get("addresses", [])

        if not addresses:
            tk.Label(self._list_frame,
                     text=t(self.lang, "portfolio_no_addresses"),
                     font=("Helvetica", 10), fg="#888888",
                     wraplength=600).pack(pady=40)
            return

        for i, entry in enumerate(addresses):
            self._build_accordion_row(i, entry)

    def _build_accordion_row(self, idx: int, entry: dict):
        addr = entry["address"]
        label = entry.get("label", addr[:16] + "...")
        balance = entry.get("balance_btc")
        price = self._data.get("btc_usd")
        is_open = self._accordion_open.get(addr, False)

        row_bg = self.ROW_EVEN if idx % 2 == 0 else self.ROW_ODD

        # ── Header row (always visible) ───────────────────────────────────────
        header = tk.Frame(self._list_frame, bg=self.ACCORDION_BG, cursor="hand2")
        header.pack(fill=tk.X, padx=0, pady=(0, 1))

        arrow = "▼" if is_open else "▶"
        tk.Label(header, text=arrow, font=("Helvetica", 10),
                 bg=self.ACCORDION_BG, fg=self.GOLD, width=2).pack(side=tk.LEFT, padx=(10, 4))

        tk.Label(header, text=label, font=("Helvetica", 10, "bold"),
                 bg=self.ACCORDION_BG, fg=self.ACCORDION_FG,
                 anchor="w").pack(side=tk.LEFT, padx=4, pady=8)

        # Balance preview on the right
        if balance is not None:
            bal_text = f"{balance:.8f} BTC"
            if price:
                bal_text += f"  ≈  ${balance * price:,.2f}"
            bal_color = self.GOLD
        else:
            bal_text = t(self.lang, "portfolio_balance_unknown")
            bal_color = "#888888"

        tk.Label(header, text=bal_text, font=("Helvetica", 10),
                 bg=self.ACCORDION_BG, fg=bal_color).pack(side=tk.RIGHT, padx=16)

        # Click anywhere on header to toggle
        def toggle(e, a=addr):
            self._accordion_open[a] = not self._accordion_open.get(a, False)
            self._rebuild_list()

        for child in header.winfo_children():
            child.bind("<Button-1>", toggle)
        header.bind("<Button-1>", toggle)

        # Hover effect
        def on_enter(e, h=header):
            h.config(bg=self.ACCORDION_HOVER)
            for c in h.winfo_children():
                try:
                    c.config(bg=self.ACCORDION_HOVER)
                except Exception:
                    pass
        def on_leave(e, h=header):
            h.config(bg=self.ACCORDION_BG)
            for c in h.winfo_children():
                try:
                    c.config(bg=self.ACCORDION_BG)
                except Exception:
                    pass
        header.bind("<Enter>", on_enter)
        header.bind("<Leave>", on_leave)
        for child in header.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)

        # ── Expanded content ──────────────────────────────────────────────────
        if is_open:
            body = tk.Frame(self._list_frame, bg=self.ACCORDION_OPEN_BG,
                            relief=tk.FLAT, bd=0)
            body.pack(fill=tk.X, padx=0, pady=(0, 2))

            # Address
            tk.Label(body, text="Address:", font=("Helvetica", 9, "bold"),
                     bg=self.ACCORDION_OPEN_BG, fg="#555555").grid(
                row=0, column=0, sticky="w", padx=(20, 8), pady=(10, 4))

            addr_var = tk.StringVar(value=addr)
            addr_lbl = tk.Entry(body, textvariable=addr_var,
                                font=("Courier", 9), state="readonly",
                                readonlybackground=self.ACCORDION_OPEN_BG,
                                relief=tk.FLAT, width=50)
            addr_lbl.grid(row=0, column=1, sticky="w", pady=(10, 4))

            # Copy address button
            def copy_addr(a=addr):
                self.clipboard_clear()
                self.clipboard_append(a)
            tk.Button(body, text="📋", font=("Helvetica", 9),
                      relief=tk.FLAT, bg=self.ACCORDION_OPEN_BG,
                      cursor="hand2", command=copy_addr).grid(
                row=0, column=2, padx=4, pady=(10, 4))

            # Balance detail
            tk.Label(body, text="Balance:", font=("Helvetica", 9, "bold"),
                     bg=self.ACCORDION_OPEN_BG, fg="#555555").grid(
                row=1, column=0, sticky="w", padx=(20, 8), pady=4)

            if balance is not None:
                bal_detail = f"{balance:.8f} BTC"
                if price:
                    bal_detail += f"   ≈   ${balance * price:,.2f} USD"
                bal_fg = "#1a6b1a"
            else:
                bal_detail = t(self.lang, "portfolio_balance_unknown")
                bal_fg = "#888888"

            tk.Label(body, text=bal_detail, font=("Helvetica", 10, "bold"),
                     bg=self.ACCORDION_OPEN_BG, fg=bal_fg).grid(
                row=1, column=1, sticky="w", pady=4)

            # Last updated
            upd = entry.get("last_updated") or t(self.lang, "portfolio_never")
            tk.Label(body,
                     text=f"{t(self.lang, 'portfolio_last_updated')} {upd}",
                     font=("Helvetica", 8), bg=self.ACCORDION_OPEN_BG,
                     fg="#aaaaaa").grid(
                row=2, column=1, sticky="w", pady=(0, 4))

            # Remove button
            def do_remove(a=addr, lb=label):
                if messagebox.askyesno(
                        t(self.lang, "app_title"),
                        t(self.lang, "confirm_remove", label=lb)):
                    self._data = remove_address(self._data, a)
                    save_portfolio(self._data)
                    self._accordion_open.pop(a, None)
                    self._refresh_summary()
                    self._rebuild_list()

            tk.Button(body, text=t(self.lang, "btn_remove_address"),
                      font=("Helvetica", 9),
                      bg=self.RED, fg="white", padx=10, pady=3,
                      relief=tk.FLAT, cursor="hand2",
                      command=do_remove).grid(
                row=3, column=1, sticky="w", padx=0, pady=(4, 12))

    # ------------------------------------------------------------ add form
    def _toggle_add_form(self):
        if self._add_form_visible:
            self._add_frame.pack_forget()
            self._add_form_visible = False
            self._addr_entry.delete(0, tk.END)
            self._label_entry.delete(0, tk.END)
        else:
            # Pack between summary bar and the list - use the list_outer as reference
            self._add_frame.pack(fill=tk.X, before=self._list_outer)
            self._add_form_visible = True
            self._addr_entry.focus_set()

    def _do_add(self):
        lang = self.lang
        address = self._addr_entry.get().strip()
        label = self._label_entry.get().strip()

        self._data, err = add_address(self._data, address, label)
        if err:
            key = f"err_{err}"
            messagebox.showerror(t(lang, "app_title"), t(lang, key))
            return

        save_portfolio(self._data)
        self._toggle_add_form()
        self._refresh_summary()
        self._rebuild_list()

        # Fetch balance for the new address immediately
        new_addr = self._data["addresses"][-1]
        self._status_lbl.config(text=t(lang, "portfolio_refreshing"))
        self._refresh_btn.config(state=tk.DISABLED)

        def fetch():
            from portfolio import fetch_address_balance, fetch_btc_price
            if self._data.get("btc_usd") is None:
                price, _ = fetch_btc_price()
                if price:
                    self._data["btc_usd"] = price
                    from datetime import datetime
                    self._data["btc_usd_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            bal, err = fetch_address_balance(new_addr["address"])
            if bal is not None:
                new_addr["balance_btc"] = bal
                from datetime import datetime
                new_addr["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_portfolio(self._data)
            self.after(0, self._on_refresh_done, [err] if err else [])

        threading.Thread(target=fetch, daemon=True).start()

    # ------------------------------------------------------------ refresh
    def _do_refresh(self):
        lang = self.lang
        self._status_lbl.config(text=t(lang, "portfolio_refreshing"), fg="#f0a500")
        self._refresh_btn.config(state=tk.DISABLED)

        def run():
            updated, errors = refresh_all(self._data)
            self._data = updated
            save_portfolio(self._data)
            self.after(0, self._on_refresh_done, errors)

        threading.Thread(target=run, daemon=True).start()

    def _on_refresh_done(self, errors: list):
        lang = self.lang
        self._refresh_btn.config(state=tk.NORMAL)
        self._refresh_summary()
        self._rebuild_list()
        if errors:
            self._status_lbl.config(
                text=t(lang, "portfolio_refresh_errors",
                       errors="\n".join(errors)), fg=self.RED)
        else:
            self._status_lbl.config(
                text=t(lang, "portfolio_refresh_done"), fg=self.GREEN)
            self.after(3000, lambda: self._status_lbl.config(
                text="", fg="#888888"))


# --- Help Tab ---
class HelpTab(tk.Frame):
    def __init__(self, parent, lang: str):
        super().__init__(parent)
        self.lang = lang
        self._bip39_loaded = False
        self._build()
        # Load BIP39 list only when this tab is first shown
        self.bind("<Visibility>", self._on_visible)

    def _build(self):
        lang = self.lang

        # Scrollable area
        outer = tk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._canvas = tk.Canvas(outer, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._inner = tk.Frame(self._canvas)

        self._inner.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas.bind_all("<MouseWheel>", lambda e: self._canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self._canvas.bind_all("<Button-4>", lambda e: self._canvas.yview_scroll(-1, "units"))
        self._canvas.bind_all("<Button-5>", lambda e: self._canvas.yview_scroll(1, "units"))

        inner = self._inner

        # --- Algorithm section ---
        tk.Label(inner, text=t(lang, "label_algorithm"),
                 font=("Helvetica", 12, "bold")).pack(anchor="w", padx=8, pady=(12, 4))

        algo_text = tk.Text(inner, font=("Courier", 9), height=22,
                            state=tk.NORMAL, wrap=tk.WORD,
                            bg="#f5f5f5", relief=tk.FLAT, bd=0,
                            padx=10, pady=6)
        algo_text.insert(tk.END, t(lang, "text_algorithm"))
        algo_text.config(state=tk.DISABLED)
        algo_text.pack(fill=tk.X, padx=8, pady=(0, 16))

        # --- BIP39 word list header ---
        tk.Label(inner, text=t(lang, "label_bip39_list"),
                 font=("Helvetica", 12, "bold")).pack(anchor="w", padx=8, pady=(4, 4))

        tk.Label(inner, text=t(lang, "desc_bip39_list"),
                 font=("Helvetica", 9), fg="#555555").pack(anchor="w", padx=8, pady=(0, 6))

        # Button to load BIP39 list on demand
        self._load_btn = tk.Button(inner, text=t(lang, "btn_show_bip39"),
                                   font=("Helvetica", 10), cursor="hand2",
                                   bg="#1565c0", fg="white", padx=12, pady=6,
                                   command=self._load_bip39)
        self._load_btn.pack(anchor="w", padx=8, pady=(0, 16))

        self._status_lbl = tk.Label(inner, text="", font=("Helvetica", 9), fg="#888888")
        self._status_lbl.pack(anchor="w", padx=8)

    def _on_visible(self, event=None):
        pass  # loading is now triggered by button only

    def _load_bip39(self):
        if self._bip39_loaded:
            return
        self._bip39_loaded = True

        self._load_btn.config(state=tk.DISABLED, text="...")
        self._status_lbl.config(text=t(self.lang, "bip39_loading"))
        self.update()

        from bip39_wordlist import BIP39_WORDS

        list_frame = tk.Frame(self._inner, bg="#f9f9f9", relief=tk.SUNKEN, bd=1)
        list_frame.pack(fill=tk.BOTH, padx=8, pady=(0, 16))

        cols = 4
        for i, word in enumerate(BIP39_WORDS):
            r = i // cols
            c = i % cols
            tk.Label(list_frame,
                     text=f"{i+1:4d}. {word}",
                     font=("Courier", 9), anchor="w", bg="#f9f9f9",
                     width=20).grid(row=r, column=c, sticky="w", padx=4, pady=0)

        self._load_btn.destroy()
        self._status_lbl.destroy()


# --- Settings Tab ---
class SettingsTab(tk.Frame):
    def __init__(self, parent, lang: str, app: SPSApp):
        super().__init__(parent)
        self.lang = lang
        self.app = app
        self._build()

    def _build(self):
        lang = self.lang

        tk.Label(self, text=t(lang, "settings_title"),
                 font=("Helvetica", 14, "bold")).pack(pady=(24, 16))

        form = tk.Frame(self)
        form.pack(padx=40, pady=8, anchor="w")

        tk.Label(form, text=t(lang, "label_language"),
                 font=("Helvetica", 11)).grid(row=0, column=0, sticky="w", padx=(0, 16), pady=8)

        lang_codes = list(AVAILABLE_LANGUAGES.keys())
        display_names = [t(lang, f"lang_{code}") for code in lang_codes]
        current_display = t(lang, f"lang_{self.app.lang}")

        self.lang_var_display = tk.StringVar(value=current_display)
        self._lang_codes = lang_codes

        ttk.Combobox(form, textvariable=self.lang_var_display,
                     values=display_names, state="readonly", width=20).grid(
            row=0, column=1, sticky="w")

        tk.Button(self, text=t(lang, "btn_save_settings"),
                  font=("Helvetica", 10, "bold"),
                  bg="#1565c0", fg="white", padx=14, pady=6,
                  cursor="hand2",
                  command=self._save).pack(pady=16)

        self.status_lbl = tk.Label(self, text="", font=("Helvetica", 9), fg="green")
        self.status_lbl.pack()

        # --- Import / Export ---
        tk.Frame(self, height=1, bg="#cccccc").pack(fill=tk.X, padx=40, pady=(20, 12))

        tk.Label(self, text=t(lang, "label_backup"),
                 font=("Helvetica", 11, "bold")).pack(anchor="w", padx=40)

        tk.Label(self, text=t(lang, "desc_backup"),
                 font=("Helvetica", 9), fg="#555555",
                 wraplength=500, justify=tk.LEFT).pack(anchor="w", padx=40, pady=(4, 12))

        btn_row = tk.Frame(self)
        btn_row.pack(anchor="w", padx=40)

        tk.Button(btn_row, text=t(lang, "btn_export"),
                  font=("Helvetica", 10), bg="#2e7d32", fg="white",
                  padx=14, pady=6, cursor="hand2",
                  command=self._export).pack(side=tk.LEFT, padx=(0, 12))

        tk.Button(btn_row, text=t(lang, "btn_import"),
                  font=("Helvetica", 10), bg="#e65100", fg="white",
                  padx=14, pady=6, cursor="hand2",
                  command=self._import).pack(side=tk.LEFT)

    def _save(self):
        selected_display = self.lang_var_display.get()
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

    def _export(self):
        from tkinter import filedialog
        data = {
            "settings": load_settings(),
            "portfolio": load_portfolio(),
        }

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON файл", "*.json"), ("Всички файлове", "*.*")],
            initialfile="mbw_backup.json",
            title=t(self.lang, "btn_export"),
        )
        if not path:
            return

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.status_lbl.config(text=t(self.lang, "export_ok"), fg="green")
        self.after(3000, lambda: self.status_lbl.config(text=""))

    def _import(self):
        from tkinter import filedialog, messagebox
        from portfolio import save_portfolio

        path = filedialog.askopenfilename(
            filetypes=[("JSON файл", "*.json"), ("Всички файлове", "*.*")],
            title=t(self.lang, "btn_import"),
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            messagebox.showerror(t(self.lang, "app_title"), t(self.lang, "import_err_format"))
            return

        if "settings" not in data or "portfolio" not in data:
            messagebox.showerror(t(self.lang, "app_title"), t(self.lang, "import_err_format"))
            return

        if not messagebox.askyesno(t(self.lang, "app_title"), t(self.lang, "import_confirm")):
            return

        save_settings(data["settings"])
        save_portfolio(data["portfolio"])

        self.status_lbl.config(text=t(self.lang, "import_ok"), fg="green")
        self.after(500, lambda: self.app.change_language(data["settings"].get("language", "en")))


if __name__ == "__main__":
    app = SPSApp()
    app.mainloop()
