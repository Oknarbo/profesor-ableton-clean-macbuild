# Profesor Abelton GUI
# Text and Voice Interface for Ableton Live
# Version: 2.0.0

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import socket
import json
import threading
import time
import os
import sys
import platform
import secrets

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from Utils.api_key_manager import APIKeyManager
except Exception:
    APIKeyManager = None

try:
    from Utils.license_manager import (
        verify_license, is_dev_mode,
        make_activation_token, verify_activation_token,
    )
    LICENSE_MANAGER_AVAILABLE = True
except Exception:
    LICENSE_MANAGER_AVAILABLE = False
    def verify_license(key): return {"valid": False, "message": "License manager not available."}
    def is_dev_mode(): return False
    def make_activation_token(key): return ""
    def verify_activation_token(key, token): return False

try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw, ImageTk
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("⚠️ System tray not available. Install: pip install pystray pillow")


class ProfesorAbeltonGUI:
    """Main GUI application for Profesor Abelton"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Profesor Abelton")
        self.root.geometry("420x900")
        self.root.minsize(350, 600)
        self._set_window_icon()
        
        # Configuration
        self.config = self.load_config()
        self.server_host = self.config.get("server", {}).get("host", "127.0.0.1")
        self.server_port = self.config.get("server", {}).get("port", 8766)
        self.auth_token = str(self.config.get("security", {}).get("auth_token", "") or "")
        
        # API Keys (encrypted on disk, per-machine)
        self.api_key_manager = APIKeyManager() if APIKeyManager else None
        self.api_keys = self.api_key_manager.load_keys() if self.api_key_manager else {}

        # One-time migration: move any plaintext keys from config into encrypted storage, then sanitize config.
        plaintext_keys = self.config.get("api_keys", {})
        if self.api_key_manager and isinstance(plaintext_keys, dict) and plaintext_keys:
            merged = dict(plaintext_keys)
            merged.update(self.api_keys)  # encrypted storage wins if both exist
            self.api_keys = merged
            try:
                self.api_key_manager.save_keys(self.api_keys)
            except Exception:
                self.api_keys = self.api_key_manager.load_keys()
            self.config.pop("api_keys", None)
            self.save_config()
        else:
            self.config.pop("api_keys", None)

        # Provider selection
        self.provider_var = tk.StringVar(value=self.config.get("ai_providers", {}).get("default", "GROQ"))
        self.gumroad_license_key = str(self.config.get("gumroad_license_key", "") or "")
        # Verify machine-bound token — prevents sharing config files to bypass license
        _stored_token = str(self.config.get("license_token", "") or "")
        self.license_activated = (
            bool(self.config.get("license_activated", False))
            and verify_activation_token(self.gumroad_license_key, _stored_token)
        )
        self.show_api_debug = bool(self.config.get("ui", {}).get("show_api_debug", False))

        # Voice control is intentionally disabled in this build.
        self.current_language = "en"  # 'en' or 'hr'
        
        # Current state
        self.ableton_state = {}
        self.chat_history = []
        
        # System tray
        self.tray_icon = None
        self.is_hidden = False
        self._cap_logo_image = None
        self._window_icon_image = None
        self._is_shutting_down = False

        # Status monitor smoothing: avoid false red state on short ping glitches.
        self._last_server_ok_ts = 0.0
        self._last_server_contact_ts = 0.0
        self._server_status_grace_seconds = 120.0
        self._server_ever_connected = False
        
        # Setup UI
        self.setup_ui()

        # License check on startup (delayed so UI is fully loaded first)
        self.root.after(2000, self._startup_license_check)

        # Ensure the window shows in the Windows taskbar (not only Alt+Tab).
        self._ensure_taskbar_icon()

        # Window close should fully exit so Windows releases the EXE/folder.
        self.root.protocol('WM_DELETE_WINDOW', self.shutdown_application)
        
        # Start state monitor
        self.monitor_thread = threading.Thread(target=self.monitor_connection, daemon=True)
        self.monitor_thread.start()

    def _resolve_asset_path(self, relative_path):
        """Resolve asset path for source mode and PyInstaller mode."""
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return os.path.join(getattr(sys, "_MEIPASS"), relative_path)
        return os.path.join(os.path.dirname(__file__), "..", relative_path)

    def _set_window_icon(self):
        """Set the feather branding for the window/taskbar icon."""
        try:
            png_path = self._resolve_asset_path(os.path.join("Assets", "profesor_abelton_feather.png"))
            if os.path.exists(png_path):
                with Image.open(png_path) as source_image:
                    img = source_image.convert("RGBA")
                self._window_icon_image = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, self._window_icon_image)

            icon_path = self._resolve_asset_path(os.path.join("Assets", "profesor_abelton_feather.ico"))
            if not os.path.exists(icon_path):
                icon_path = self._resolve_asset_path(os.path.join("Assets", "original_clean_app_icon.ico"))
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

    def _load_app_icon_image(self):
        """Load the branded feather icon, falling back only if needed."""
        candidates = [
            os.path.join("Assets", "profesor_abelton_feather.png"),
            os.path.join("Assets", "profesor_abelton_feather.ico"),
            os.path.join("Assets", "original_clean_app_icon.png"),
            os.path.join("Assets", "original_clean_app_icon.ico"),
        ]
        for rel_path in candidates:
            asset_path = self._resolve_asset_path(rel_path)
            if os.path.exists(asset_path):
                with Image.open(asset_path) as source_image:
                    return source_image.convert("RGBA")
        return None

    def _create_fallback_tray_image(self):
        """Draw a clearer old-style bird feather for the system tray."""
        width = 64
        height = 64
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)

        # Dark quill shaft
        dc.line([(16, 54), (45, 10)], fill=(12, 12, 12, 255), width=5)

        # Main vane silhouette
        vane = [
            (14, 54), (18, 49), (22, 44), (26, 38), (30, 32), (34, 26),
            (38, 20), (43, 13), (49, 10), (54, 12), (51, 19), (47, 27),
            (42, 35), (36, 43), (30, 49), (23, 54),
        ]
        dc.polygon(vane, fill=(18, 18, 18, 255))

        # Feather barbs
        barb_lines = [
            ((22, 47), (39, 41)),
            ((25, 42), (42, 35)),
            ((28, 37), (45, 29)),
            ((31, 32), (47, 24)),
            ((34, 27), (49, 19)),
        ]
        for start, end in barb_lines:
            dc.line([start, end], fill=(255, 255, 255, 110), width=1)

        return image

    def _load_tray_image(self):
        """Return the same icon used for the app/taskbar whenever possible."""
        image = self._load_app_icon_image()
        if image is not None:
            return image
        return self._create_fallback_tray_image()

    def _stop_tray_icon(self):
        """Stop and release the system tray icon if it exists."""
        if not self.tray_icon:
            return
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.tray_icon = None

    def _mark_server_connected(self):
        self.server_status_icon.config(text="[OK]", fg="#00ff88")
        self.server_status_label.config(text="Connected")

    def _mark_server_disconnected(self, label):
        if self._server_ever_connected:
            self._mark_server_connected()
        else:
            self.server_status_icon.config(text="[X]", fg="#ff6b35")
            self.server_status_label.config(text=label)

    def _mark_ableton_connected(self):
        self.ableton_status_icon.config(text="[OK]", fg="#00ff88")
        self.ableton_status_label.config(text="Connected")

    def _mark_ableton_waiting(self, label="Waiting..."):
        self.ableton_status_icon.config(text="[?]", fg="#888888")
        self.ableton_status_label.config(text=label)

    def _load_cap_logo_image(self, size=(34, 34)):
        """Load black graduation-cap logo for header branding."""
        try:
            candidates = [
                os.path.join("Assets", "profesor_abelton_cap_black.png"),
                os.path.join("Assets", "profesor_abelton_cap_black.ico"),
                os.path.join("Assets", "profesor_abelton_cap_blue.png"),
                os.path.join("Assets", "profesor_abelton_cap_blue.ico"),
            ]
            cap_path = None
            for rel in candidates:
                abs_path = self._resolve_asset_path(rel)
                if os.path.exists(abs_path):
                    cap_path = abs_path
                    break
            if not cap_path:
                return None
            img = Image.open(cap_path).convert("RGBA").resize(size, Image.LANCZOS)
            self._cap_logo_image = ImageTk.PhotoImage(img)
            return self._cap_logo_image
        except Exception:
            return None

    def _recv_json_line(self, sock, timeout=5.0):
        """Receive one newline-delimited JSON message."""
        sock.settimeout(timeout)
        buffer = ""
        while True:
            chunk = sock.recv(4096).decode("utf-8", errors="replace")
            if not chunk:
                break
            buffer += chunk
            if "\n" in buffer:
                line, _rest = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                return json.loads(line)
        raise Exception("No JSON line received from server")
    
    def _ensure_taskbar_icon(self):
        """
        Windows-only: force app window style so the GUI is visible in the taskbar.
        This fixes the common issue: window is reachable via Alt+Tab but has no taskbar button.
        """
        if platform.system() != "Windows":
            return

        try:
            import ctypes  # Windows only
            try:
                # Helps Windows group the taskbar button under our app, not under the parent console host.
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ProfesorAbelton")  # type: ignore[attr-defined]
            except Exception:
                pass

            GWL_EXSTYLE = -20
            GWLP_HWNDPARENT = -8
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOZORDER = 0x0004
            SWP_FRAMECHANGED = 0x0020
            GA_ROOT = 2
            SW_RESTORE = 9

            def _apply():
                try:
                    # Apply only once per process to avoid Tk/Win32 weirdness (ghost/duplicate windows).
                    if getattr(self, "_taskbar_fix_applied", False):
                        return

                    self.root.update_idletasks()
                    hwnd_child = self.root.winfo_id()
                    if not hwnd_child:
                        return

                    user32 = ctypes.windll.user32

                    # On Windows, Tk uses a wrapper HWND (top-level) plus an inner child HWND.
                    # Tkinter's winfo_id() frequently returns the *child* window handle.
                    # Taskbar/owner/exstyle must be applied to the *wrapper* HWND, otherwise you can
                    # end up with a second white window and/or missing caption buttons.
                    hwnd = user32.GetAncestor(hwnd_child, GA_ROOT) or hwnd_child

                    # Owned windows don't appear in the taskbar. Ensure no owner/parent is set.
                    try:
                        set_long_ptr = getattr(user32, "SetWindowLongPtrW", None)
                        if set_long_ptr is None:
                            set_long_ptr = user32.SetWindowLongW  # type: ignore[attr-defined]
                        set_long_ptr(hwnd, GWLP_HWNDPARENT, 0)
                    except Exception:
                        pass

                    # Use Get/SetWindowLongPtr when available (64-bit safe).
                    get_long_ptr = getattr(user32, "GetWindowLongPtrW", None)
                    if get_long_ptr is None:
                        get_long_ptr = user32.GetWindowLongW  # type: ignore[attr-defined]

                    set_long_ptr_ex = getattr(user32, "SetWindowLongPtrW", None)
                    if set_long_ptr_ex is None:
                        set_long_ptr_ex = user32.SetWindowLongW  # type: ignore[attr-defined]

                    style = get_long_ptr(hwnd, GWL_EXSTYLE)
                    style = style & ~WS_EX_TOOLWINDOW
                    style = style | WS_EX_APPWINDOW
                    set_long_ptr_ex(hwnd, GWL_EXSTYLE, style)

                    # Refresh window frame
                    try:
                        user32.SetWindowPos(
                            hwnd,
                            0,
                            0,
                            0,
                            0,
                            0,
                            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
                        )
                    except Exception:
                        pass

                    # Nudge Windows shell to re-evaluate taskbar visibility for this window.
                    # Without this, style changes sometimes only affect Alt+Tab but not the taskbar button.
                    try:
                        user32.ShowWindow(hwnd, SW_RESTORE)
                    except Exception:
                        pass

                    try:
                        if getattr(self, "_taskbar_shell_kick_done", False) is False:
                            self._taskbar_shell_kick_done = True
                            # Do NOT change "minimize to tray" behavior: this only runs once at startup.
                            self.root.after(
                                10,
                                lambda: (
                                    self.root.withdraw(),
                                    self.root.after(30, self.root.deiconify),
                                ),
                            )
                    except Exception:
                        pass

                    self._taskbar_fix_applied = True
                except Exception:
                    pass

            try:
                self.root.bind("<Map>", lambda _e: _apply())
            except Exception:
                pass
            self.root.after(250, _apply)
        except Exception:
            return

    def _get_config_path(self) -> str:
        """
        Return a writable config path.
        - Frozen app: ~/.profesor_abelton/copilot_config.json  (always writable)
        - Dev/source: ../Config/copilot_config.json  (relative to GUI folder)
        """
        if getattr(sys, "frozen", False):
            cfg_dir = os.path.join(os.path.expanduser("~"), ".profesor_abelton")
            os.makedirs(cfg_dir, exist_ok=True)
            return os.path.join(cfg_dir, "copilot_config.json")
        return os.path.join(os.path.dirname(__file__), "..", "Config", "copilot_config.json")

    def load_config(self):
        """Load configuration"""
        config_path = self._get_config_path()
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            # Frozen: try to seed from the bundled default config
            if getattr(sys, "frozen", False):
                try:
                    import sys as _sys
                    bundled = os.path.join(getattr(_sys, "_MEIPASS", ""), "Config", "copilot_config.json")
                    with open(bundled, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except Exception:
                    config = {}
            else:
                config = {}
        except Exception:
            config = {}

        config.setdefault("server", {"host": "127.0.0.1", "port": 8766})
        config.setdefault("security", {"auth_token": ""})
        config.setdefault("ui", {"show_api_debug": False})
        config.setdefault("gumroad_license_key", "")
        return self._normalize_config(config)

    def _normalize_config(self, config):
        changed = False

        server_cfg = config.setdefault("server", {})
        host = str(server_cfg.get("host", "127.0.0.1") or "127.0.0.1").strip().lower()
        if host not in {"localhost", "127.0.0.1", "::1"}:
            server_cfg["host"] = "127.0.0.1"
            changed = True
        elif host != "127.0.0.1":
            server_cfg["host"] = "127.0.0.1"
            changed = True

        security_cfg = config.setdefault("security", {})
        auth_token = str(security_cfg.get("auth_token", "") or "").strip()
        if not auth_token:
            security_cfg["auth_token"] = secrets.token_hex(32)
            changed = True

        ui_cfg = config.setdefault("ui", {})
        if "show_api_debug" not in ui_cfg:
            ui_cfg["show_api_debug"] = False
            changed = True

        if changed:
            self.config = config
            self.save_config()
        return config
    
    def update_mcp_status(self):
        """Update MCP status indicator (always ON now)"""
        # MCP is now always enabled
        self.mcp_status_label.config(text="[MCP: ON]", fg='#00ff88')

    def save_config(self):
        """Save configuration"""
        config_path = self._get_config_path()
        try:
            # Never store API keys in plaintext config.
            self.config.pop("api_keys", None)
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")
    
    def setup_ui(self):
        """Setup modern Gumroad-friendly interface"""
        # Modern Gumroad-ready color scheme
        BG_DARK = '#0a0a0a'        # Deep black background
        BG_HEADER = '#1a1a1a'      # Dark header
        BG_PANEL = '#2a2a2a'       # Panel background
        BG_ACCENT = '#3a3a3a'      # Accent panels
        FG_TEXT = '#e0e0e0'        # Light text
        FG_DIM = '#888888'         # Dimmed text
        ACCENT_BLUE = '#00d4ff'    # Bright cyan accent
        ACCENT_GREEN = '#00ff88'   # Bright green for success
        ACCENT_ORANGE = '#ff6b35'  # Warm orange for warnings
        BORDER_COLOR = '#404040'   # Subtle borders

        # Configure root background and styling
        self.root.configure(bg=BG_DARK)
        self.style = {'bg': BG_DARK, 'fg': FG_TEXT, 'font': ('Segoe UI', 10)}

        # ============= MODERN HEADER SECTION =============
        # Avoid fixed-height headers: they can clip text on Windows DPI scaling (125%/150%).
        header_frame = tk.Frame(self.root, bg=BG_HEADER)
        header_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)

        # Main branding section
        branding_frame = tk.Frame(header_frame, bg=BG_HEADER)
        branding_frame.pack(fill=tk.X, padx=20, pady=(15, 10))

        # Logo and title
        logo_frame = tk.Frame(branding_frame, bg=BG_HEADER)
        logo_frame.pack(side=tk.LEFT)

        # Graduation-cap branding (larger black icon)
        cap_logo = self._load_cap_logo_image((34, 34))
        if cap_logo:
            logo_label = tk.Label(
                logo_frame,
                image=cap_logo,
                bg="#f4f4f4",
                relief=tk.RAISED,
                bd=1,
                padx=5,
                pady=5
            )
        else:
            logo_label = tk.Label(
                logo_frame,
                text="\U0001F393",
                font=('Segoe UI', 18, 'bold'),
                bg='#f2f2f2',
                fg='#111111',
                padx=8,
                pady=4,
                relief=tk.RAISED,
                bd=1
            )
        logo_label.pack(side=tk.LEFT, padx=(0, 8))

        title_frame = tk.Frame(logo_frame, bg=BG_HEADER)
        title_frame.pack(side=tk.LEFT)

        title_main = tk.Label(
            title_frame,
            text="PROFESOR",
            font=('Segoe UI', 16, 'bold'),
            bg=BG_HEADER,
            fg='white'
        )
        title_main.pack(anchor=tk.W)

        title_sub = tk.Label(
            title_frame,
            text="ABELTON",
            font=('Segoe UI', 12, 'bold'),
            bg=BG_HEADER,
            fg=ACCENT_BLUE
        )
        title_sub.pack(anchor=tk.W)

        # Version badge
        version_label = tk.Label(
            branding_frame,
            text="v2.0.0",
            font=('Segoe UI', 8),
            bg=BG_ACCENT,
            fg=FG_TEXT,
            padx=8,
            pady=2,
            relief=tk.FLAT
        )
        version_label.pack(side=tk.RIGHT, padx=(10, 0))

        # Status indicators panel
        status_panel = tk.Frame(header_frame, bg=BG_PANEL, relief=tk.RIDGE, bd=1)
        status_panel.pack(fill=tk.X, padx=20, pady=(0, 15))

        # Status grid
        status_title = tk.Label(
            status_panel,
            text="SYSTEM STATUS",
            font=('Segoe UI', 9, 'bold'),
            bg=BG_PANEL,
            fg=FG_DIM
        )
        status_title.pack(pady=(8, 5))

        status_grid = tk.Frame(status_panel, bg=BG_PANEL)
        status_grid.pack(pady=(0, 8))

        # Server status
        server_frame = tk.Frame(status_grid, bg=BG_PANEL)
        server_frame.pack(side=tk.LEFT, padx=15)

        self.server_status_icon = tk.Label(
            server_frame,
            text="[X]",
            font=('Segoe UI', 10, 'bold'),
            bg=BG_PANEL,
            fg=ACCENT_ORANGE
        )
        self.server_status_icon.pack(side=tk.LEFT, padx=(0, 5))

        self.server_status_label = tk.Label(
            server_frame,
            text="Server",
            font=('Segoe UI', 9),
            bg=BG_PANEL,
            fg=FG_TEXT
        )
        self.server_status_label.pack(side=tk.LEFT)

        # Ableton status
        ableton_frame = tk.Frame(status_grid, bg=BG_PANEL)
        ableton_frame.pack(side=tk.LEFT, padx=15)

        self.ableton_status_icon = tk.Label(
            ableton_frame,
            text="[X]",
            font=('Segoe UI', 10, 'bold'),
            bg=BG_PANEL,
            fg=ACCENT_ORANGE
        )
        self.ableton_status_icon.pack(side=tk.LEFT, padx=(0, 5))

        self.ableton_status_label = tk.Label(
            ableton_frame,
            text="Ableton",
            font=('Segoe UI', 9),
            bg=BG_PANEL,
            fg=FG_TEXT
        )
        self.ableton_status_label.pack(side=tk.LEFT)

        # MCP status moved to status bar
        
        # ============= MODERN CHAT SECTION =============
        chat_panel = tk.Frame(self.root, bg=BG_ACCENT, relief=tk.RIDGE, bd=1)
        chat_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=15, pady=(5, 10))

        # Chat header
        # Avoid fixed-height headers: they can clip text on Windows DPI scaling (125%/150%).
        chat_header = tk.Frame(chat_panel, bg=BG_ACCENT)
        chat_header.pack(fill=tk.X, padx=15, pady=(10, 5))

        chat_title = tk.Label(
            chat_header,
            text="🤖 AI CONVERSATION",
            font=('Segoe UI', 10, 'bold'),
            bg=BG_ACCENT,
            fg=ACCENT_BLUE
        )
        chat_title.pack(side=tk.LEFT)

        # Clear chat button
        clear_btn = tk.Button(
            chat_header,
            text="🗑️",
            font=('Segoe UI', 9),
            bg=BG_ACCENT,
            fg=FG_TEXT,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.clear_chat,
            padx=8,
            pady=2
        )
        clear_btn.pack(side=tk.RIGHT)

        # Chat display area
        chat_container = tk.Frame(chat_panel, bg=BG_DARK, relief=tk.SUNKEN, bd=1)
        chat_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.chat_display = scrolledtext.ScrolledText(
            chat_container,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            bg=BG_DARK,
            fg=FG_TEXT,
            insertbackground=ACCENT_BLUE,
            relief=tk.FLAT,
            padx=12,
            pady=12,
            selectbackground=BG_ACCENT,
            selectforeground='white'
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Configure modern tags for colored messages
        self.chat_display.tag_config('user', foreground=ACCENT_GREEN, font=('Segoe UI', 10, 'bold'))
        self.chat_display.tag_config('ai', foreground=FG_TEXT, font=('Segoe UI', 10))
        self.chat_display.tag_config('system', foreground=ACCENT_BLUE, font=('Segoe UI', 9, 'italic'))
        self.chat_display.tag_config('error', foreground=ACCENT_ORANGE, font=('Segoe UI', 10, 'bold'))
        self.chat_display.tag_config('timestamp', foreground=FG_DIM, font=('Segoe UI', 8))
        
        # Controls are now integrated in the modern input panel below
        
        # ============= MODERN INPUT SECTION =============
        # Avoid fixed-height input panel: allow it to size to its contents.
        input_panel = tk.Frame(self.root, bg=BG_ACCENT, relief=tk.RIDGE, bd=1)
        input_panel.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(0, 15))

        # Input header
        # Avoid fixed-height header row: buttons/text can get clipped on DPI scaling.
        input_header = tk.Frame(input_panel, bg=BG_ACCENT)
        input_header.pack(fill=tk.X, padx=15, pady=(8, 5))

        # Compact provider selector
        provider_combo = ttk.Combobox(
            input_header,
            textvariable=self.provider_var,
            values=["GROQ", "CLAUDE"],
            width=7,
            state='readonly',
            font=('Segoe UI', 7)
        )
        provider_combo.pack(side=tk.LEFT, padx=(0, 10))

        input_title = tk.Label(
            input_header,
            text="💬 YOUR MESSAGE",
            font=('Segoe UI', 9, 'bold'),
            bg=BG_ACCENT,
            fg=ACCENT_BLUE
        )
        input_title.pack(side=tk.LEFT)

        # Control buttons
        controls_frame = tk.Frame(input_header, bg=BG_ACCENT)
        controls_frame.pack(side=tk.RIGHT)

        # Send button (primary action)
        self.send_button = tk.Button(
            controls_frame,
            text="SEND",
            font=('Segoe UI', 8, 'bold'),
            bg=ACCENT_GREEN,
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self.send_message,
            padx=12,
            pady=4,
            borderwidth=0
        )
        self.send_button.pack(side=tk.LEFT, padx=(0, 5))

        # Settings button
        settings_btn = tk.Button(
            controls_frame,
            text="SETTINGS",
            font=('Segoe UI', 7, 'bold'),
            bg=BG_ACCENT,
            fg=FG_TEXT,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.show_settings,
            padx=8,
            pady=4
        )
        settings_btn.pack(side=tk.LEFT, padx=(0, 5))

        # System tray button
        if TRAY_AVAILABLE:
            tray_btn = tk.Button(
                controls_frame,
                text="HIDE",
                font=('Segoe UI', 7, 'bold'),
                bg=BG_ACCENT,
                fg=FG_TEXT,
                relief=tk.FLAT,
                cursor='hand2',
                command=self.hide_to_tray,
                padx=8,
                pady=4
            )
            tray_btn.pack(side=tk.LEFT)
        
        # Modern text input area
        input_area = tk.Frame(input_panel, bg=BG_DARK, relief=tk.SUNKEN, bd=1)
        input_area.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.input_field = tk.Text(
            input_area,
            height=3,
            font=('Segoe UI', 10),
            bg=BG_DARK,
            fg=FG_TEXT,
            insertbackground=ACCENT_BLUE,
            relief=tk.FLAT,
            padx=12,
            pady=12,
            wrap=tk.WORD,
            selectbackground=BG_ACCENT,
            selectforeground='white'
        )
        self.input_field.pack(fill=tk.BOTH, expand=True)
        self.input_field.bind('<Return>', self.on_enter_key)
        self.input_field.bind('<Shift-Return>', lambda e: None)  # Allow Shift+Enter for newline

        # Placeholder text
        self.input_field.insert('1.0', 'Type your message to Profesor Ableton...')
        self.input_field.config(fg=FG_DIM)

        def on_focus_in(event):
            if self.input_field.get('1.0', 'end-1c') == 'Type your message to Profesor Ableton...':
                self.input_field.delete('1.0', tk.END)
                self.input_field.config(fg=FG_TEXT)

        def on_focus_out(event):
            if not self.input_field.get('1.0', 'end-1c').strip():
                self.input_field.insert('1.0', 'Type your message to Profesor Ableton...')
                self.input_field.config(fg=FG_DIM)

        self.input_field.bind('<FocusIn>', on_focus_in)
        self.input_field.bind('<FocusOut>', on_focus_out)

        # Status bar at bottom
        # Avoid fixed-height status bar: can clip descenders on some fonts/scales.
        status_bar = tk.Frame(self.root, bg=BG_HEADER, relief=tk.RIDGE, bd=1)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)

        # Status info (no emoji)
        status_info = tk.Label(
            status_bar,
            text="Ready to produce music with AI assistance",
            font=('Segoe UI', 8),
            bg=BG_HEADER,
            fg=FG_DIM
        )
        status_info.pack(side=tk.LEFT, padx=15)

        # MCP status in status bar
        self.mcp_status_label = tk.Label(
            status_bar,
            text="🔧 MCP: OFF",
            font=('Segoe UI', 8),
            bg=BG_HEADER,
            fg=FG_DIM
        )
        self.mcp_status_label.pack(side=tk.LEFT, padx=(10, 0))

        # Update MCP status (force ON since we hardcoded it)
        self.update_mcp_status()

        # Version info
        version_info = tk.Label(
            status_bar,
            text="Profesor Ableton v2.0.0",
            font=('Segoe UI', 8),
            bg=BG_HEADER,
            fg=FG_DIM
        )
        version_info.pack(side=tk.RIGHT, padx=15)
        
        # Welcome message (no emoji)
        self.add_system_message("Profesor Abelton ready!")
        self.add_system_message("Connect to server and Ableton to start...")
    
    def on_enter_key(self, event):
        """Handle Enter key - send message, Shift+Enter for newline"""
        if event.state & 0x1:  # Shift is pressed
            return  # Allow newline
        else:
            self.send_message()
            return 'break'  # Prevent newline
    
    def add_message(self, text, tag='system'):
        """Add message to chat display"""
        self.chat_display.insert(tk.END, text + '\n\n', tag)
        self.chat_display.see(tk.END)
    
    def add_user_message(self, text):
        """Add user message"""
        self.add_message(f"👤 You: {text}", 'user')
    
    def add_ai_message(self, text, provider='AI'):
        """Add AI message"""
        self.add_message(f"🎓 Profesor ({provider}): {text}", 'ai')
    
    def add_system_message(self, text):
        """Add system message"""
        self.add_message(f"💡 {text}", 'system')

    def _format_request_debug(self, debug_info):
        if not isinstance(debug_info, dict):
            return None

        mode = debug_info.get("mode")
        context_level = debug_info.get("context_level")
        model = debug_info.get("model")
        track_count = debug_info.get("track_count")

        parts = []
        if model:
            parts.append(f"model={model}")
        if mode:
            parts.append(f"mode={mode}")
        if context_level:
            parts.append(f"context={context_level}")
        if track_count is not None:
            parts.append(f"tracks={track_count}")

        if not parts:
            return None
        return "Debug: " + " | ".join(parts)
    
    def add_error_message(self, text):
        """Add error message"""
        self.add_message(f"❌ Error: {text}", 'error')
    
    def send_message(self):
        """Send text message to AI"""
        message = self.input_field.get("1.0", tk.END).strip()

        if not message:
            return

        if not is_dev_mode() and not self.license_activated:
            self.add_system_message(
                "⚠️ License not activated — enter your Gumroad license key in ⚙️ Settings."
            )
            return

        self.input_field.delete("1.0", tk.END)
        self.add_user_message(message)
        
        # Send to server in background
        threading.Thread(
            target=self.send_to_server,
            args=('command', message),
            daemon=True
        ).start()
    
    def send_to_server(self, msg_type, content):
        """Send message to server"""
        sock = None
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            
            print(f"🔌 Connecting to {self.server_host}:{self.server_port}...")
            sock.connect((self.server_host, self.server_port))
            print(f"✅ Connected")

            # IMPORTANT: First, register as GUI client
            connect_msg = {
                "type": "connect",
                "client": "gui",
                "auth_token": self.auth_token,
            }
            print(f"📤 Sending connect message...")
            sock.sendall(json.dumps(connect_msg).encode('utf-8') + b'\n')
            
            # Wait for connect response
            print(f"📥 Waiting for connect response...")
            connect_response = sock.recv(8192).decode('utf-8')
            print(f"📨 Received: {connect_response[:100]}")
            
            if '\n' in connect_response:
                connect_response = connect_response.split('\n')[0]
            
            if connect_response.strip():
                connect_result = json.loads(connect_response.strip())
                
                if connect_result.get("status") != "ok":
                    raise Exception(f"Server rejected connection: {connect_result}")
                print(f"✅ Connection accepted")
                self._last_server_contact_ts = time.time()
                self._server_ever_connected = True
                self.root.after(0, self._mark_server_connected)
            
            # Get API key for provider
            provider = self.provider_var.get()
            api_key = self.api_keys.get(provider, "")

            # Update environment variable for Claude MCP
            if provider == "CLAUDE":
                os.environ["CLAUDE_MCP_ENABLED"] = "true"
                os.environ["CLAUDE_API_KEY"] = api_key if api_key else ""

            # Prepare command message
            message = {
                "type": msg_type,
                "prompt": content,
                "language": self.current_language,
                "provider": provider,
                "api_key": api_key if api_key else None,
                "gumroad_license_key": self.gumroad_license_key or None,
                "auth_token": self.auth_token,
            }

            # Send command with newline delimiter
            print(f"📤 Sending command...")
            sock.settimeout(60.0)  # Longer timeout for AI response
            sock.sendall(json.dumps(message).encode('utf-8') + b'\n')

            # Receive response
            print(f"📥 Waiting for AI response...")
            response_data = sock.recv(16384).decode('utf-8')
            print(f"📨 Received response: {len(response_data)} bytes")
            
            if '\n' in response_data:
                response_data = response_data.split('\n')[0]
            
            if not response_data.strip():
                raise Exception("Empty response from server")
                
            response = json.loads(response_data.strip())

            # Handle response
            if 'error' in response:
                if response.get('license_error'):
                    self.add_system_message(
                        "⚠️ " + response['error'] + " — enter a valid key in ⚙️ Settings."
                    )
                    self.license_activated = False
                else:
                    self.add_error_message(response['error'])
            elif 'response' in response:
                provider_name = response.get('provider', 'AI')
                self.add_ai_message(response['response'], provider_name)

                debug_text = self._format_request_debug(response.get("request_debug"))
                if debug_text and self.show_api_debug:
                    self.add_system_message(debug_text)

                # Show tool calls if MCP was used
                if 'tool_calls' in response and response['tool_calls']:
                    self.add_system_message(f"MCP Tools used: {len(response['tool_calls'])}")

                # Execute commands if any
                if 'commands' in response and response['commands']:
                    self.add_system_message(f"Executing {len(response['commands'])} command(s)...")
            else:
                self.add_system_message("Response received")

        except socket.timeout:
            self.add_error_message("Server timeout. Make sure server is running!")
        except ConnectionRefusedError:
            self.add_error_message("Cannot connect to server. Make sure it's running!")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            self.add_error_message(f"Communication error: {e}")
        finally:
            if sock:
                try:
                    sock.close()
                    print(f"🔌 Socket closed")
                except:
                    pass
    
    def toggle_voice(self):
        """Voice control is disabled in this release."""
        messagebox.showinfo(
            "Voice control",
            "Voice control je privremeno uklonjen i bit ce operativan u sljedecoj verziji.",
        )
    
    def listen_voice(self):
        """Voice control is disabled in this release."""
        self.add_system_message("Voice control je privremeno uklonjen u ovoj verziji.")
    
    def change_language(self, event):
        """Change voice language"""
        lang = self.language_var.get()
        self.current_language = "en" if lang == "English" else "hr"
        self.add_system_message(f"Language changed to: {lang}")
    
    def clear_chat(self):
        """Clear chat display"""
        self.chat_display.delete(1.0, tk.END)
        self.add_system_message("Chat cleared")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
🎓 Profesor Abelton - Help

TEXT COMMANDS:
• Type any question or instruction
• Examples:
  - "Create a new MIDI track"
  - "Set tempo to 128 BPM"
  - "Explain what a compressor does"
  - "Add reverb to track 1"

VOICE COMMANDS:
• Voice control je uklonjen u ovoj verziji
• Koristi tekstualne komande u chat polju

LANGUAGE:
• English: General commands and production
• Croatian: Full Croatian language support

AI PROVIDERS:
• GROQ: Groq Cloud (requires API key)
• CLAUDE: Anthropic Claude (requires API key)

SETTINGS:
• Click ⚙️ to enter API keys
• Set API keys for Groq and Claude

MINIMIZE:
• Click ⬇️ to minimize to system tray
• Right-click icon for menu

For more info, see README.md
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Help")
        help_window.geometry("500x600")
        help_window.configure(bg='#1e1e1e')
        
        help_text_widget = scrolledtext.ScrolledText(
            help_window,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            bg='#1e1e1e',
            fg='#cccccc',
            padx=15,
            pady=15
        )
        help_text_widget.pack(fill=tk.BOTH, expand=True)
        help_text_widget.insert(1.0, help_text)
        help_text_widget.config(state=tk.DISABLED)
    
    def _startup_license_check(self):
        """One-time license check on startup. Activates and stores result locally."""
        if is_dev_mode():
            self.add_system_message("🔧 Developer mode — license check skipped.")
            return

        if self.license_activated:
            return

        if not self.gumroad_license_key:
            self.add_system_message(
                "⚠️ No license key found. Enter your Gumroad license key in ⚙️ Settings."
            )
            return

        self.add_system_message("🔑 Verifying license key...")

        def _check():
            result = verify_license(self.gumroad_license_key)
            def _update():
                if result["valid"]:
                    self.license_activated = True
                    self.config["license_activated"] = True
                    self.config["license_token"] = make_activation_token(self.gumroad_license_key)
                    self.save_config()
                    self.add_system_message("✅ License activated! Profesor Abelton is ready.")
                else:
                    self.add_system_message(
                        f"⚠️ License not verified: {result['message']} "
                        "— Enter a valid key in ⚙️ Settings."
                    )
            self.root.after(0, _update)

        threading.Thread(target=_check, daemon=True).start()

    def show_settings(self):
        """Show settings dialog for API keys"""
        # Prevent multiple settings windows
        if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()  # Bring to front
            return

        settings_window = tk.Toplevel(self.root)
        self.settings_window = settings_window  # Store reference
        settings_window.title("⚙️ Settings - API Keys")
        settings_window.geometry("500x680")
        settings_window.configure(bg='#2d2d30')
        settings_window.resizable(False, True)
        
        # Title
        title_label = tk.Label(
            settings_window,
            text="🔑 API Keys",
            font=('Segoe UI', 14, 'bold'),
            bg='#2d2d30',
            fg='white'
        )
        title_label.pack(pady=15)
        
        # Info
        info_label = tk.Label(
            settings_window,
            text="Enter API keys for AI providers.",
            font=('Segoe UI', 9),
            bg='#2d2d30',
            fg='#cccccc',
            justify=tk.LEFT
        )
        info_label.pack(pady=(0, 15))
        
        # Frame for inputs
        inputs_frame = tk.Frame(settings_window, bg='#2d2d30')
        inputs_frame.pack(padx=30, pady=10, fill=tk.X, expand=False)
        
        # API key entries
        providers = ["GROQ", "CLAUDE"]
        entries = {}
        
        for i, provider in enumerate(providers):
            # Label
            label = tk.Label(
                inputs_frame,
                text=f"{provider}:",
                font=('Segoe UI', 10, 'bold'),
                bg='#2d2d30',
                fg='white',
                width=10,
                anchor='w'
            )
            label.grid(row=i, column=0, sticky=tk.W, pady=8)
            
            # Entry
            entry = tk.Entry(
                inputs_frame,
                font=('Segoe UI', 9),
                bg='#3c3c3c',
                fg='white',
                insertbackground='white',
                show='•',
                width=40
            )
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=8, padx=10)
            entry.insert(0, self.api_keys.get(provider, ""))
            entries[provider] = entry
        
        inputs_frame.columnconfigure(1, weight=1)

        # Gumroad license key
        gumroad_label = tk.Label(
            inputs_frame,
            text="GUMROAD:",
            font=('Segoe UI', 10, 'bold'),
            bg='#2d2d30',
            fg='white',
            width=10,
            anchor='w'
        )
        gumroad_label.grid(row=len(providers), column=0, sticky=tk.W, pady=(14, 8))

        gumroad_entry = tk.Entry(
            inputs_frame,
            font=('Segoe UI', 9),
            bg='#3c3c3c',
            fg='white',
            insertbackground='white',
            width=40
        )
        gumroad_entry.grid(row=len(providers), column=1, sticky=(tk.W, tk.E), pady=(14, 8), padx=10)
        gumroad_entry.insert(0, self.gumroad_license_key)

        # Verify button next to the entry
        verify_status_var = tk.StringVar(value="✅ Activated" if self.license_activated else "")

        def do_verify():
            key = gumroad_entry.get().strip()
            if not key:
                verify_status_var.set("⚠️ Enter a key first")
                return
            verify_status_var.set("⏳ Checking...")
            settings_window.update_idletasks()
            result = verify_license(key)
            if result["valid"]:
                verify_status_var.set("✅ Valid!")
            else:
                verify_status_var.set(f"❌ {result['message']}")

        verify_btn = tk.Button(
            inputs_frame,
            text="Verify",
            font=('Segoe UI', 9),
            bg='#007acc',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=do_verify,
            padx=8,
            pady=2
        )
        verify_btn.grid(row=len(providers), column=2, pady=(14, 8), padx=(0, 10))

        verify_status_label = tk.Label(
            inputs_frame,
            textvariable=verify_status_var,
            font=('Segoe UI', 8),
            bg='#2d2d30',
            fg='#aaaaaa',
            anchor='w'
        )
        verify_status_label.grid(row=len(providers) + 1, column=1, sticky=tk.W, padx=10, pady=(0, 4))

        gumroad_hint = tk.Label(
            inputs_frame,
            text="Enter the Gumroad license key provided after purchase.",
            font=('Segoe UI', 8),
            bg='#2d2d30',
            fg='#555555',
            justify=tk.LEFT,
            anchor='w',
            wraplength=280
        )
        gumroad_hint.grid(row=len(providers) + 2, column=1, sticky=tk.W, padx=10, pady=(0, 6))

        debug_var = tk.BooleanVar(value=self.show_api_debug)
        debug_checkbox = tk.Checkbutton(
            inputs_frame,
            text="Show API debug info in chat",
            variable=debug_var,
            font=('Segoe UI', 9),
            bg='#2d2d30',
            fg='white',
            selectcolor='#3c3c3c',
            activebackground='#2d2d30',
            activeforeground='white',
            anchor='w'
        )
        debug_checkbox.grid(row=len(providers) + 3, column=1, sticky=tk.W, padx=10, pady=(4, 10))

        # MCP Status (Always Enabled)
        mcp_frame = tk.Frame(settings_window, bg='#2d2d30', relief=tk.RIDGE, bd=2)
        mcp_frame.pack(padx=30, pady=(6, 10), fill=tk.X)

        mcp_title = tk.Label(
            mcp_frame,
            text="🤖 MCP Status: ALWAYS ENABLED",
            font=('Segoe UI', 12, 'bold'),
            bg='#2d2d30',
            fg='#00ff88'
        )
        mcp_title.pack(pady=(10, 5))

        mcp_info = tk.Label(
            mcp_frame,
            text="MCP (Model Context Protocol) is always enabled.\nClaude can directly control Ableton functions!",
            font=('Segoe UI', 9),
            bg='#2d2d30',
            fg='#cccccc',
            justify=tk.LEFT
        )
        mcp_info.pack(pady=(0, 10))

        # Force MCP ON
        os.environ["CLAUDE_MCP_ENABLED"] = "true"
        self.config["mcp_enabled"] = True

        # Buttons
        button_frame = tk.Frame(settings_window, bg='#2d2d30')
        button_frame.pack(pady=12)
        
        def save_keys():
            if not self.api_key_manager:
                messagebox.showerror(
                    "Missing Dependency",
                    "Secure API key storage is not available.\n\nInstall with:\n  pip install cryptography"
                )
                return

            # Save API keys
            for provider, entry in entries.items():
                key = entry.get().strip()
                if key:
                    self.api_keys[provider] = key
                elif provider in self.api_keys:
                    del self.api_keys[provider]

            # Persist encrypted keys
            try:
                self.api_key_manager.save_keys(self.api_keys)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to securely save API keys: {e}")
                return

            # Save MCP setting
            os.environ["CLAUDE_MCP_ENABLED"] = "true"  # Always ON
            self.config["mcp_enabled"] = True  # Save to config
            new_license_key = gumroad_entry.get().strip()
            if new_license_key != self.gumroad_license_key:
                # Key changed — reset activation so it gets re-verified at next startup
                self.license_activated = False
                self.config["license_activated"] = False
                self.config["license_token"] = ""
            self.gumroad_license_key = new_license_key
            self.config["gumroad_license_key"] = self.gumroad_license_key
            self.show_api_debug = bool(debug_var.get())
            self.config.setdefault("ui", {})["show_api_debug"] = self.show_api_debug
            self.save_config()

            # If verified in dialog, activate immediately and store machine-bound token
            if verify_status_var.get().startswith("✅"):
                self.license_activated = True
                self.config["license_activated"] = True
                self.config["license_token"] = make_activation_token(self.gumroad_license_key)
                self.save_config()
                self.add_system_message("✅ Settings saved! License activated.")
            else:
                self.add_system_message("✅ Settings saved! MCP: ON, Gumroad key updated.")
            self.update_mcp_status()
            settings_window.destroy()
            self.settings_window = None  # Clear reference
        
        def cancel():
            settings_window.destroy()
        
        save_btn = tk.Button(
            button_frame,
            text="💾 Save",
            font=('Segoe UI', 10, 'bold'),
            bg='#007acc',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=save_keys,
            padx=20,
            pady=10
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="✖️ Cancel",
            font=('Segoe UI', 10),
            bg='#555',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=cancel,
            padx=20,
            pady=10
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def hide_to_tray(self):
        """Hide window to system tray"""
        if not TRAY_AVAILABLE:
            self.root.iconify()  # Fallback to minimize
            return
        
        self.root.withdraw()
        self.is_hidden = True
        
        if not self.tray_icon:
            def on_clicked(icon, item):
                self.root.after(0, self.show_from_tray)
            
            def on_quit(icon, item):
                self.root.after(0, self.shutdown_application)
            
            menu = Menu(
                MenuItem('Open', on_clicked, default=True),
                MenuItem('Exit', on_quit)
            )
            
            self.tray_icon = Icon("Profesor Abelton", self._load_tray_image(), "Profesor Abelton", menu)
            
            # Run tray icon in background
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def show_from_tray(self):
        """Show window from system tray"""
        self._stop_tray_icon()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_hidden = False

    def shutdown_application(self):
        """Fully close the GUI and release the bundled EXE."""
        if self._is_shutting_down:
            return
        self._is_shutting_down = True
        self.is_hidden = False
        self._stop_tray_icon()

        try:
            self.root.quit()
        except Exception:
            pass

        try:
            self.root.destroy()
        except Exception:
            pass
    
    def monitor_connection(self):
        """Monitor server and Ableton connection"""
        retry_count = 0
        max_retries_before_pause = 3
        
        while True:
            sock = None
            try:
                # Try to connect
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3.0)
                sock.connect((self.server_host, self.server_port))

                self._last_server_contact_ts = time.time()
                self._server_ever_connected = True
                self.root.after(0, self._mark_server_connected)

                # Register monitor client and ping, but keep server green
                # even if ping parsing fails intermittently.
                response = None
                try:
                    connect_msg = {"type": "connect", "client": "gui"}
                    connect_msg["auth_token"] = self.auth_token
                    sock.sendall(json.dumps(connect_msg).encode("utf-8") + b"\n")
                    _connect_response = self._recv_json_line(sock, timeout=3.0)

                    ping_msg = {"type": "ping"}
                    ping_msg["auth_token"] = self.auth_token
                    sock.sendall(json.dumps(ping_msg).encode("utf-8") + b"\n")
                    response = self._recv_json_line(sock, timeout=3.0)
                except Exception as ping_err:
                    print(f"⚠️ Monitor ping degraded: {ping_err}")

                self._last_server_ok_ts = time.time()

                # Update GUI from main thread
                def update_gui():
                    self._mark_server_connected()

                    if response and bool(response.get("ableton_connected", False)):
                        self._mark_ableton_connected()
                    elif response is None:
                        # Keep previous Ableton state if ping response was unavailable.
                        pass
                    else:
                        self._mark_ableton_waiting("Waiting...")

                self.root.after(0, update_gui)
                retry_count = 0  # Reset retry count on success

            except socket.timeout:
                retry_count += 1
                print(f"⚠️ Monitor timeout (attempt {retry_count})")
                def update_error():
                    self._mark_server_disconnected("Timeout")
                    self._mark_ableton_waiting("Waiting...")
                self.root.after(0, update_error)
                
            except ConnectionRefusedError:
                retry_count += 1
                print(f"⚠️ Server not running (attempt {retry_count})")
                def update_error():
                    self._mark_server_disconnected("Not Running")
                    self._mark_ableton_waiting("N/A")
                self.root.after(0, update_error)
                
            except Exception as e:
                retry_count += 1
                print(f"⚠️ Monitor error: {e} (attempt {retry_count})")
                def update_error():
                    self._mark_server_disconnected("Error")
                    self._mark_ableton_waiting("N/A")
                self.root.after(0, update_error)
            finally:
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass

            # Adaptive sleep - sleep longer if multiple failures
            if retry_count >= max_retries_before_pause:
                time.sleep(10)  # Longer pause after multiple failures
                retry_count = 0  # Reset after pause
            else:
                time.sleep(5)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ProfesorAbeltonGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

