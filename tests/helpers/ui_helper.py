from __future__ import annotations

import gc
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
from typing import Any


class UiAppHelper:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.temp_dir: Path | None = None
        self.previous_cwd: str | None = None
        self.app: Any = None
        self._messagebox_originals: dict[str, Any] = {}
        self._simpledialog_originals: dict[str, Any] = {}
        self._filedialog_originals: dict[str, Any] = {}
        self.messages: list[tuple[str, str, str]] = []
        self.dialog_response = "automation-test"
        self.save_path: str | None = None
        self.step_delay = float(os.getenv("UI_STEP_DELAY", "0") or "0")
        self.test_id = os.getenv("CURRENT_TEST_ID", "")
        self.test_steps = json.loads(os.getenv("CURRENT_TEST_STEPS", "[]") or "[]")
        self.step_index = int(os.getenv("CURRENT_TEST_STEP_INDEX", "0") or "0")

    def __enter__(self) -> "UiAppHelper":
        if str(self.repo_root) not in sys.path:
            sys.path.insert(0, str(self.repo_root))

        self.temp_dir = Path(tempfile.mkdtemp(prefix="uth_portal_ui_test_"))
        self.previous_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        from main import MainApp
        from tests.fixtures.import_seed_data import import_seed_data

        self._patch_messagebox()
        self.app = MainApp()
        import_seed_data(self.db_path)
        self.pump()
        self.step()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self.app is not None:
            try:
                self.app.destroy()
            except tk.TclError:
                pass
            self.app = None

        self._restore_messagebox()
        self._restore_simpledialog()
        self._restore_filedialog()

        if self.previous_cwd:
            os.chdir(self.previous_cwd)

        if self.temp_dir and self.temp_dir.exists():
            for attempt in range(5):
                try:
                    gc.collect()
                    shutil.rmtree(self.temp_dir)
                    break
                except PermissionError:
                    if attempt == 4:
                        shutil.rmtree(self.temp_dir, ignore_errors=True)
                    else:
                        time.sleep(0.1)

    @property
    def db_path(self) -> Path:
        if self.temp_dir is None:
            raise RuntimeError("UiAppHelper must be used as a context manager.")
        return self.temp_dir / "uth_portal_final.db"

    def pump(self, delay: float = 0.05) -> None:
        self.app.update_idletasks()
        self.app.update()
        wait_time = delay
        if wait_time:
            time.sleep(wait_time)
            self.app.update_idletasks()
            self.app.update()

    def step(self) -> None:
        if self.step_index < len(self.test_steps):
            step_text = self.test_steps[self.step_index]
        else:
            step_text = f"Step {self.step_index + 1}"
        self.step_index += 1
        os.environ["CURRENT_TEST_STEP_INDEX"] = str(self.step_index)
        print(f"[PROCESSING] {self.test_id} - STEP {self.step_index} - {step_text}", flush=True)
        self.app.update_idletasks()
        self.app.update()
        if self.step_delay > 0:
            time.sleep(self.step_delay)
            self.app.update_idletasks()
            self.app.update()

    def _patch_messagebox(self) -> None:
        def capture(kind: str):
            def inner(title: str, message: str, *args: Any, **kwargs: Any) -> str:
                self.messages.append((kind, title, message))
                return "ok"

            return inner

        for name in ("showinfo", "showerror", "showwarning"):
            self._messagebox_originals[name] = getattr(messagebox, name)
            setattr(messagebox, name, capture(name))
        self._messagebox_originals["askyesno"] = messagebox.askyesno
        messagebox.askyesno = lambda title, message, *args, **kwargs: True
        self._simpledialog_originals["askstring"] = simpledialog.askstring
        simpledialog.askstring = lambda title, prompt, *args, **kwargs: self.dialog_response
        self._filedialog_originals["asksaveasfilename"] = filedialog.asksaveasfilename
        filedialog.asksaveasfilename = lambda *args, **kwargs: self.save_path or str(self.db_path.with_suffix(".csv"))

    def _restore_messagebox(self) -> None:
        for name, original in self._messagebox_originals.items():
            setattr(messagebox, name, original)
        self._messagebox_originals.clear()

    def _restore_simpledialog(self) -> None:
        for name, original in self._simpledialog_originals.items():
            setattr(simpledialog, name, original)
        self._simpledialog_originals.clear()

    def _restore_filedialog(self) -> None:
        for name, original in self._filedialog_originals.items():
            setattr(filedialog, name, original)
        self._filedialog_originals.clear()

    def set_dialog_response(self, value: str) -> None:
        self.dialog_response = value

    def set_save_path(self, value: Path | str) -> None:
        self.save_path = str(value)

    def show_login(self) -> Any:
        self.step()
        self.app.show_frame("LoginView")
        self.pump()
        return self.app.frames["LoginView"]

    def login(self, role: str, username: str, password: str, detailed: bool = False) -> None:
        if detailed:
            login_view = self.show_login()
            self.step()
            login_view.switch_role(role)
            self.step()
        else:
            self.step()
            self.app.show_frame("LoginView")
            self.pump()
            login_view = self.app.frames["LoginView"]
            login_view.switch_role(role)

        login_view.e_usr.delete(0, tk.END)
        login_view.e_usr.insert(0, username)
        login_view.e_pwd.delete(0, tk.END)
        login_view.e_pwd.insert(0, password)
        self.pump()
        if detailed:
            self.step()
        login_view.do_login()
        self.pump()

    def buttons_under(self, widget: tk.Widget) -> list[tk.Button]:
        buttons: list[tk.Button] = []
        for child in widget.winfo_children():
            if isinstance(child, tk.Button):
                buttons.append(child)
            buttons.extend(self.buttons_under(child))
        return buttons

    def labels_under(self, widget: tk.Widget) -> list[tk.Label]:
        labels: list[tk.Label] = []
        for child in widget.winfo_children():
            if isinstance(child, tk.Label):
                labels.append(child)
            labels.extend(self.labels_under(child))
        return labels

    def entries_under(self, widget: tk.Widget) -> list[tk.Entry]:
        entries: list[tk.Entry] = []
        for child in widget.winfo_children():
            if isinstance(child, tk.Entry):
                entries.append(child)
            entries.extend(self.entries_under(child))
        return entries

    def button_texts(self, widget: tk.Widget) -> list[str]:
        return [str(button.cget("text")) for button in self.buttons_under(widget)]

    def button_containing(self, widget: tk.Widget, text: str) -> tk.Button:
        for button in self.buttons_under(widget):
            if text in str(button.cget("text")):
                return button
        raise AssertionError(f"Expected button containing {text!r}, got {self.button_texts(widget)}")

    def top_level_buttons(self) -> list[tk.Button]:
        buttons: list[tk.Button] = []
        for child in self._walk_widgets(self.app):
            if isinstance(child, tk.Toplevel):
                buttons.extend(self.buttons_under(child))
        return buttons

    def _walk_widgets(self, widget: tk.Widget) -> list[tk.Widget]:
        widgets: list[tk.Widget] = []
        for child in widget.winfo_children():
            widgets.append(child)
            widgets.extend(self._walk_widgets(child))
        return widgets

    def top_level_button_containing(self, text: str) -> tk.Button:
        buttons = self.top_level_buttons()
        for button in buttons:
            if text in str(button.cget("text")):
                return button
        labels = [str(button.cget("text")) for button in buttons]
        raise AssertionError(f"Expected top-level button containing {text!r}, got {labels}")

    def label_texts(self, widget: tk.Widget) -> list[str]:
        return [str(label.cget("text")) for label in self.labels_under(widget)]

    def scalar(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(sql, params)
            conn.commit()
        finally:
            conn.close()
