"""
First Launch Wizard (mandatory until completed).

Shows a 5-step setup flow:
1) Welcome
2) Detect Ableton + Remote Scripts path
3) Install / Update Remote Script (one-click)
4) API Keys setup (encrypted storage)
5) Finish + write setup_complete marker
"""

from __future__ import annotations

import os
import platform
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Optional

# Ensure project root is on path for imports when run directly
if getattr(sys, "frozen", False):
    # In PyInstaller, put resources next to the executable (onedir)
    PROJECT_ROOT = Path(sys.executable).resolve().parent
else:
    PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from Utils.ableton_detector import AbletonDetector, install_remote_script_to_all
except Exception:
    AbletonDetector = None
    install_remote_script_to_all = None

try:
    from Utils.api_key_manager import APIKeyManager
except Exception:
    APIKeyManager = None


def _app_config_dir() -> Path:
    return Path.home() / ".profesor_abelton"


def setup_complete_marker_path() -> Path:
    return _app_config_dir() / "setup_complete"


def is_setup_complete() -> bool:
    return setup_complete_marker_path().exists()


def mark_setup_complete() -> None:
    p = setup_complete_marker_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("ok\n", encoding="utf-8")


class FirstLaunchWizard(tk.Tk):
    def __init__(self, project_root: Path):
        super().__init__()
        self.project_root = project_root

        self.title("Profesor Abelton - First Launch Setup")
        self.geometry("720x520")
        self.minsize(680, 480)

        self.protocol("WM_DELETE_WINDOW", self._on_close_blocked)

        self.detector = AbletonDetector(project_root=project_root) if AbletonDetector else None
        self.api_key_manager = APIKeyManager() if APIKeyManager else None

        self.remote_scripts_dir: Optional[Path] = None
        self.remote_script_name: str = ""
        self.install_success: bool = False

        self.api_keys: Dict[str, str] = {}

        # Styling
        self.configure(bg="#0a0a0a")
        self._style = ttk.Style(self)
        try:
            self._style.theme_use("clam")
        except Exception:
            pass

        self._style.configure("Wizard.TFrame", background="#0a0a0a")
        self._style.configure("WizardHeader.TFrame", background="#1a1a1a")
        self._style.configure("WizardTitle.TLabel", background="#1a1a1a", foreground="white", font=("Segoe UI", 14, "bold"))
        self._style.configure("WizardSub.TLabel", background="#0a0a0a", foreground="#cccccc", font=("Segoe UI", 10))
        self._style.configure("WizardStep.TLabel", background="#0a0a0a", foreground="#00d4ff", font=("Segoe UI", 11, "bold"))

        self._build_ui()
        self._load_initial_state()
        self._show_step(0)

    # ---------- UI shell ----------
    def _build_ui(self) -> None:
        # Header
        header = ttk.Frame(self, style="WizardHeader.TFrame")
        header.pack(side=tk.TOP, fill=tk.X)

        title = ttk.Label(header, text="FIRST LAUNCH SETUP", style="WizardTitle.TLabel")
        title.pack(side=tk.LEFT, padx=18, pady=14)

        self.step_label = ttk.Label(self, text="", style="WizardStep.TLabel")
        self.step_label.pack(side=tk.TOP, anchor="w", padx=18, pady=(14, 6))

        # Body
        self.body = ttk.Frame(self, style="Wizard.TFrame")
        self.body.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=18, pady=10)

        # Footer
        footer = ttk.Frame(self, style="Wizard.TFrame")
        footer.pack(side=tk.BOTTOM, fill=tk.X, padx=18, pady=14)

        self.back_btn = ttk.Button(footer, text="Back", command=self._back)
        self.back_btn.pack(side=tk.LEFT)

        self.next_btn = ttk.Button(footer, text="Next", command=self._next)
        self.next_btn.pack(side=tk.RIGHT)

        self.finish_btn = ttk.Button(footer, text="Finish", command=self._finish)
        self.finish_btn.pack(side=tk.RIGHT, padx=(0, 10))

        # Steps
        self.steps = [
            self._step_welcome,
            self._step_detect,
            self._step_install,
            self._step_api_keys,
            self._step_finish,
        ]
        self._step_frames: list[tk.Frame] = []

    def _clear_body(self) -> None:
        for child in self.body.winfo_children():
            child.destroy()

    # ---------- State ----------
    def _load_initial_state(self) -> None:
        # Ableton detection
        if self.detector:
            self.remote_scripts_dir = self.detector.best_user_remote_scripts_dir()
            self.remote_script_name = self.detector.remote_script_name()
        else:
            self.remote_scripts_dir = None
            self.remote_script_name = "ProfesorAbelton"

        # API keys
        if self.api_key_manager:
            self.api_keys = self.api_key_manager.load_keys()
        else:
            self.api_keys = {}

        # Install status best-effort (if already installed)
        if self.remote_scripts_dir and self.remote_script_name:
            if (self.remote_scripts_dir / self.remote_script_name / "__init__.py").exists():
                self.install_success = True

    # ---------- Navigation ----------
    def _show_step(self, idx: int) -> None:
        self.current_step = idx
        self._clear_body()

        step_names = [
            "Step 1/5 — Welcome",
            "Step 2/5 — Detect Ableton",
            "Step 3/5 — Install Remote Script",
            "Step 4/5 — API Keys",
            "Step 5/5 — Finish",
        ]
        self.step_label.config(text=step_names[idx])

        # Buttons
        self.back_btn.config(state=("disabled" if idx == 0 else "normal"))
        self.next_btn.config(state=("normal" if idx < 4 else "disabled"))
        self.finish_btn.config(state=("normal" if idx == 4 else "disabled"))

        # Render step
        self.steps[idx]()

        # Step-specific gating
        self._refresh_gating()

    def _refresh_gating(self) -> None:
        # Require successful remote script install before proceeding past step 3
        if self.current_step == 2:
            # On install step: Next disabled until install_success
            self.next_btn.config(state=("normal" if self.install_success else "disabled"))
        if self.current_step == 1:
            # Detect: allow Next always (user can proceed to install)
            self.next_btn.config(state="normal")
        if self.current_step == 3:
            # API keys: allow Next always
            self.next_btn.config(state="normal")

    def _persist_api_keys_from_entries(self, show_success: bool = False) -> bool:
        """Persist wizard API keys, even if the user only clicks Next/Finish."""
        if not self.api_key_manager:
            return True
        if self.current_step != 3:
            return True

        entries = getattr(self, "_key_entries", None)
        if not isinstance(entries, dict):
            return True

        keys: Dict[str, str] = {}
        for provider, entry in entries.items():
            try:
                value = entry.get().strip()
            except tk.TclError:
                value = self.api_keys.get(provider, "").strip()
            if value:
                keys[provider] = value

        try:
            self.api_key_manager.save_keys(keys)
            self.api_keys = keys
            if show_success:
                messagebox.showinfo("Saved", "API keys saved securely.")
            return True
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to save keys securely:\n{ex}")
            return False

    def _next(self) -> None:
        if self.current_step == 3 and not self._persist_api_keys_from_entries():
            return
        if self.current_step < 4:
            self._show_step(self.current_step + 1)

    def _back(self) -> None:
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    # ---------- Steps ----------
    def _step_welcome(self) -> None:
        frame = ttk.Frame(self.body, style="Wizard.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Welcome to Profesor Abelton",
            style="WizardSub.TLabel",
            font=("Segoe UI", 16, "bold"),
            foreground="white",
        ).pack(anchor="w", pady=(8, 10))

        text = (
            "This setup wizard will run once and guide you through:\n"
            "- Detecting Ableton Remote Scripts folder\n"
            "- Installing / updating the control surface script\n"
            "- Saving API keys securely (encrypted per-machine)\n\n"
            "You must complete this wizard before using the app."
        )
        ttk.Label(frame, text=text, style="WizardSub.TLabel", justify="left").pack(anchor="w", pady=(0, 12))

        note = (
            "Tip: If Ableton is running, the installer may ask you to close it,\n"
            "then restart Ableton after installation."
        )
        ttk.Label(frame, text=note, style="WizardSub.TLabel", foreground="#00d4ff", justify="left").pack(anchor="w")

        compat = "⚠️  Supported Ableton versions: Live 11 and 12.  Live 10 is not supported."
        ttk.Label(frame, text=compat, style="WizardSub.TLabel", foreground="#ffaa00", justify="left").pack(anchor="w", pady=(10, 0))

    def _step_detect(self) -> None:
        frame = ttk.Frame(self.body, style="Wizard.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Ableton detection", style="WizardSub.TLabel",
                  font=("Segoe UI", 13, "bold"), foreground="white").pack(anchor="w", pady=(6, 6))

        # Show all detected candidate paths
        from Utils.ableton_detector import find_all_user_remote_scripts_dirs, candidate_user_remote_scripts_dirs
        all_dirs = find_all_user_remote_scripts_dirs(create_if_missing=False)
        candidates = candidate_user_remote_scripts_dirs()

        if all_dirs:
            detected_color = "#00ff88"
            detected_text = f"✅ Found {len(all_dirs)} install location(s):"
        else:
            detected_color = "#ffaa00"
            detected_text = "⚠️ No existing Ableton Remote Scripts folder found — will create one automatically."

        ttk.Label(frame, text=detected_color and detected_text, style="WizardSub.TLabel",
                  foreground=detected_color).pack(anchor="w", pady=(4, 2))

        for d in (all_dirs or candidates[:1]):
            ttk.Label(frame, text=f"  • {d}", style="WizardSub.TLabel",
                      foreground="#aaaaaa").pack(anchor="w")

        # Manual override row
        manual_frame = ttk.Frame(frame, style="Wizard.TFrame")
        manual_frame.pack(fill=tk.X, pady=(14, 0))

        ttk.Label(manual_frame, text="Or choose manually:", style="WizardSub.TLabel").pack(side=tk.LEFT)

        manual_var = tk.StringVar(value=str(self.remote_scripts_dir) if self.remote_scripts_dir else "")
        manual_entry = tk.Entry(manual_frame, textvariable=manual_var, width=40,
                                bg="#1e1e1e", fg="white", insertbackground="white")
        manual_entry.pack(side=tk.LEFT, padx=(8, 4), fill=tk.X, expand=True)

        def browse() -> None:
            chosen = filedialog.askdirectory(title="Select Ableton Remote Scripts folder",
                                            initialdir=str(Path.home()))
            if chosen:
                manual_var.set(chosen)
                self.remote_scripts_dir = Path(chosen)

        def apply_manual() -> None:
            p = manual_var.get().strip()
            if p:
                self.remote_scripts_dir = Path(p)
                messagebox.showinfo("Path set", f"Will install to:\n{p}\n\n(Folder will be created if needed.)")

        ttk.Button(manual_frame, text="Browse…", command=browse).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(manual_frame, text="Use this path", command=apply_manual).pack(side=tk.LEFT)

        # Info / Ableton status
        running = self.detector and self.detector.is_ableton_running()
        status_row = ttk.Frame(frame, style="Wizard.TFrame")
        status_row.pack(fill=tk.X, pady=(12, 0))
        ttk.Label(status_row, text="Ableton running:", style="WizardSub.TLabel", width=20).pack(side=tk.LEFT)
        ttk.Label(status_row, text=("⚠️ Yes — please close it before installing" if running else "✅ No"),
                  style="WizardSub.TLabel",
                  foreground=("#ffaa00" if running else "#00ff88")).pack(side=tk.LEFT)

        btns = ttk.Frame(frame, style="Wizard.TFrame")
        btns.pack(anchor="w", pady=(14, 0))

        def refresh() -> None:
            if self.detector:
                self.remote_scripts_dir = self.detector.best_user_remote_scripts_dir()
                self.remote_script_name = self.detector.remote_script_name()
            self._show_step(1)

        ttk.Button(btns, text="Refresh", command=refresh).pack(side=tk.LEFT)

    def _step_install(self) -> None:
        frame = ttk.Frame(self.body, style="Wizard.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Install / Update Remote Script", style="WizardSub.TLabel", font=("Segoe UI", 13, "bold"), foreground="white").pack(anchor="w", pady=(6, 10))

        info = (
            "This will copy the bundled `RemoteScript/` folder into your Ableton Remote Scripts directory.\n"
            "Ableton must be restarted after installation."
        )
        ttk.Label(frame, text=info, style="WizardSub.TLabel", justify="left").pack(anchor="w", pady=(0, 12))

        status_frame = ttk.Frame(frame, style="Wizard.TFrame")
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.install_status = ttk.Label(
            status_frame,
            text=("✅ Installed" if self.install_success else "❌ Not installed yet"),
            style="WizardSub.TLabel",
            foreground=("#00ff88" if self.install_success else "#ff6b35"),
            font=("Segoe UI", 11, "bold"),
        )
        self.install_status.pack(anchor="w")

        def do_install() -> None:
            if not install_remote_script_to_all:
                messagebox.showerror("Error", "Installer module not available.")
                return

            if self.detector and self.detector.is_ableton_running():
                messagebox.showwarning(
                    "Ableton is running",
                    "Ableton Live appears to be running.\n\n"
                    "Please close Ableton, then click Install again.",
                )
                return

            # If user manually selected a path, install there; otherwise auto-detect all
            if self.remote_scripts_dir:
                from Utils.ableton_detector import install_remote_script
                ok, msg = install_remote_script(
                    project_root=self.project_root,
                    target_user_remote_scripts_dir=self.remote_scripts_dir,
                    remote_script_name=self.remote_script_name,
                    overwrite=True,
                )
            else:
                ok, msg = install_remote_script_to_all(
                    project_root=self.project_root,
                    remote_script_name=self.remote_script_name,
                    overwrite=True,
                )

            if ok:
                self.install_success = True
                self.install_status.config(text="✅ Installed — restart Ableton!", foreground="#00ff88")
                messagebox.showinfo(
                    "Installed!",
                    f"{msg}\n\n"
                    f"Next steps in Ableton:\n"
                    f"  Preferences → Link/Tempo/MIDI\n"
                    f"  Control Surface: {self.remote_script_name}\n"
                    f"  Input: None   Output: None\n\n"
                    f"Restart Ableton to activate."
                )
            else:
                self.install_success = False
                self.install_status.config(text="❌ Install failed", foreground="#ff6b35")
                # Build manual instructions using actual detected candidate paths
                from Utils.ableton_detector import candidate_user_remote_scripts_dirs
                all_candidates = candidate_user_remote_scripts_dirs()
                if all_candidates:
                    manual_path = str(all_candidates[0])
                elif platform.system() == "Windows":
                    manual_path = r"Documents\Ableton\User Library\Remote Scripts"
                else:
                    manual_path = "~/Music/Ableton/User Library/Remote Scripts"
                manual = (
                    f"Automatic install failed:\n{msg}\n\n"
                    f"Manual install:\n"
                    f"1. Open your Remote Scripts folder:\n"
                    f"   {manual_path}\n"
                    f"   (create it if it doesn't exist)\n"
                    f"2. Create a folder named: {self.remote_script_name}\n"
                    f"3. Copy RemoteScript/__init__.py into that folder\n\n"
                    f"Then restart Ableton."
                )
                messagebox.showerror("Install failed — manual steps below", manual)

            self._refresh_gating()

        ttk.Button(frame, text="Install / Update", command=do_install).pack(anchor="w", pady=(6, 0))

        hint = "You cannot proceed until installation succeeds."
        ttk.Label(frame, text=hint, style="WizardSub.TLabel", foreground="#cccccc").pack(anchor="w", pady=(10, 0))

    def _step_api_keys(self) -> None:
        frame = ttk.Frame(self.body, style="Wizard.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="API Keys (secure storage)", style="WizardSub.TLabel", font=("Segoe UI", 13, "bold"), foreground="white").pack(anchor="w", pady=(6, 10))

        text = (
            "Keys are stored encrypted on this machine.\n"
            "You can leave them empty if you plan to use a local provider in a future update."
        )
        ttk.Label(frame, text=text, style="WizardSub.TLabel", justify="left").pack(anchor="w", pady=(0, 12))

        if not self.api_key_manager:
            ttk.Label(
                frame,
                text="Secure key storage is not available (missing dependency: cryptography).",
                style="WizardSub.TLabel",
                foreground="#ff6b35",
            ).pack(anchor="w")
            return

        form = ttk.Frame(frame, style="Wizard.TFrame")
        form.pack(fill=tk.X, pady=(0, 10))

        providers = ["GROQ", "CLAUDE"]
        self._key_entries: Dict[str, tk.Entry] = {}

        for i, p in enumerate(providers):
            row = ttk.Frame(form, style="Wizard.TFrame")
            row.pack(fill=tk.X, pady=6)
            ttk.Label(row, text=f"{p}:", style="WizardSub.TLabel", width=12).pack(side=tk.LEFT)
            e = tk.Entry(row, show="•", width=44, bg="#1e1e1e", fg="white", insertbackground="white")
            e.pack(side=tk.LEFT, fill=tk.X, expand=True)
            e.insert(0, self.api_keys.get(p, ""))
            self._key_entries[p] = e

            count_var = tk.StringVar(value=f"{len(self.api_keys.get(p, ''))} chars")
            count_lbl = ttk.Label(row, textvariable=count_var, style="WizardSub.TLabel",
                                  foreground="#666666", width=9)
            count_lbl.pack(side=tk.LEFT, padx=(6, 0))

            def _make_tracer(cv: tk.StringVar, entry: tk.Entry):
                def _trace(*_):
                    n = len(entry.get())
                    cv.set(f"{n} chars" if n == 0 else f"✓ {n} chars")
                return _trace

            e.bind("<KeyRelease>", _make_tracer(count_var, e))
            e.bind("<<Paste>>", lambda ev, cv=count_var, en=e: en.after(10, lambda: cv.set(f"✓ {len(en.get())} chars")))

        def save_keys() -> None:
            self._persist_api_keys_from_entries(show_success=True)

        ttk.Button(frame, text="Save keys", command=save_keys).pack(anchor="w")

    def _step_finish(self) -> None:
        frame = ttk.Frame(self.body, style="Wizard.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Finish", style="WizardSub.TLabel", font=("Segoe UI", 13, "bold"), foreground="white").pack(anchor="w", pady=(6, 10))

        summary = (
            f"Remote Scripts folder:\n  {self.remote_scripts_dir}\n\n"
            f"Control Surface name:\n  {self.remote_script_name}\n\n"
            "Next steps inside Ableton:\n"
            f"  Preferences → Link/Tempo/MIDI → Control Surface: {self.remote_script_name}\n"
            "  Input/Output: None\n"
            "  Restart Ableton\n"
        )
        ttk.Label(frame, text=summary, style="WizardSub.TLabel", justify="left").pack(anchor="w", pady=(0, 12))

        ttk.Label(
            frame,
            text="Click Finish to complete setup and start the app.",
            style="WizardSub.TLabel",
            foreground="#00d4ff",
        ).pack(anchor="w")

    # ---------- Finish / Close ----------
    def _finish(self) -> None:
        if not self.install_success:
            messagebox.showerror("Setup incomplete", "Remote Script is not installed yet.")
            return
        try:
            mark_setup_complete()
        except Exception as e:
            messagebox.showerror("Error", f"Could not write setup marker:\n{e}")
            return
        self._allow_close = True
        self.destroy()

    def _on_close_blocked(self) -> None:
        # Mandatory wizard: user cannot close without completing.
        messagebox.showwarning(
            "Setup required",
            "You must complete the first launch setup wizard before using the app.",
        )


def run_first_launch_wizard(project_root: Optional[Path] = None) -> bool:
    """
    Returns True when setup is completed.
    """
    pr = project_root or PROJECT_ROOT
    app = FirstLaunchWizard(project_root=pr)
    app.mainloop()
    return is_setup_complete()


if __name__ == "__main__":
    ok = run_first_launch_wizard(PROJECT_ROOT)
    raise SystemExit(0 if ok else 1)

