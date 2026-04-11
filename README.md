# Profesor Abelton

**Version:** 2.0.1  
**AI providers:** Groq (llama-3.3-70b-versatile) + Claude (claude-haiku, MCP tools)  
**Ableton Control Surface name:** `ProfesorAbelton`

Profesor Abelton is an AI assistant for Ableton Live. Control your session using plain English — create tracks, set tempo, add devices, manage clips, and more. Claude runs in **MCP tool mode** (35 tools) for structured, reliable Ableton actions. Groq is available as a fast alternative.

> Not affiliated with Ableton AG. "Profesor Abelton" is a wordplay brand name.

---

## Requirements

| | |
|---|---|
| **OS** | Windows 10/11 · macOS 12+ (Apple Silicon & Intel) |
| **Ableton Live** | **11 or 12 only** — Live 10 is not supported |
| **Internet** | Required for Groq / Claude API calls |
| **API keys** | Groq and/or Anthropic (Claude) |

---

## Quick Start — Windows

1. Extract the ZIP, open the `ProfesorAbelton\` folder.
2. Launch **`ProfesorAbelton.exe`**.
3. Complete the **First Launch Wizard**:
   - Installs the Remote Script into Ableton automatically
   - Enter your Groq / Claude API keys
   - Enter your Gumroad license key
4. In Ableton: **Preferences → Link/Tempo/MIDI → Control Surface: `ProfesorAbelton`** → Input/Output: None
5. Restart Ableton.
6. Try: *"create a new midi track"*, *"set tempo to 128"*, *"add reverb to track 1"*

**Note:** Do not move or delete the `_internal\` folder. The `.exe` must stay in the same folder as the rest of the bundle.

---

## Quick Start — macOS

1. Extract the ZIP, drag **`ProfesorAbelton.app`** to your Applications folder (or run directly).
2. If macOS blocks the app: right-click → **Open** → Open.
3. Complete the **First Launch Wizard** (installs Remote Script, saves API keys).
4. In Ableton: **Preferences → Link/Tempo/MIDI → Control Surface: `ProfesorAbelton`** → Input/Output: None
5. Restart Ableton.

---

## License Activation

After first launch, enter your **Gumroad license key** in **⚙️ Settings → API Keys**.  
The app will verify the key once online and cache the result for 24 hours.  
Without a valid license, AI requests are blocked.

---

## Features

- **Direct Ableton control** — tracks, clips, tempo, devices, transport, mixer
- **Claude MCP (35 tools)** — structured tool calling for predictable actions
- **Groq** — fast natural language fallback
- **First Launch Wizard** — one-click Remote Script install + key setup
- **Encrypted API key storage** — keys stored per-machine, not in plain text
- **License protection** — machine-bound activation, server-side verification

---

## Troubleshooting

### `ProfesorAbelton` not visible in Ableton Control Surfaces
- Run the wizard again (launch the app, it will offer to reinstall).
- Verify the script exists:
  - **Windows:** `%APPDATA%\Ableton\Live XX\Preferences\User Remote Scripts\ProfesorAbelton\__init__.py`
  - **macOS:** `~/Music/Ableton/User Library/Remote Scripts/ProfesorAbelton/__init__.py`
- Restart Ableton completely.
- **Live 10 is not supported** — upgrade to Live 11 or 12.

### GUI shows "Disconnected"
- Make sure the app (server) is running.
- Check that port **8766** is not blocked by a firewall.

### GUI shows "Ableton: Waiting…"
- Set Control Surface to `ProfesorAbelton` in Ableton Preferences.
- Restart Ableton after changing the Control Surface.

### "License not valid" error
- Check that you entered the correct Gumroad key in ⚙️ Settings.
- Make sure you have an internet connection (required for first-time verification).

---

## Support

- Discord: *(add link)*
- Email: *(add support email)*
