PROFESOR ABELTON — Quick Start (macOS)
Version: 2.0.1

REQUIREMENTS:
- Ableton Live 11 or 12  (Live 10 is NOT supported)
- macOS 12 or later (Apple Silicon M-series / Intel)
- Internet connection for AI (Groq / Claude API keys)


1) How to run
-------------
1. Extract the ZIP.
2. Move ProfesorAbelton.app to your Applications folder (or run directly).
3. If macOS blocks the app (Gatekeeper warning):
   - Right-click ProfesorAbelton.app → Open → Open
   - You only need to do this once.
4. Complete the First Launch Wizard (opens automatically on first run).

2) Ableton setup (Control Surface)
-----------------------------------
So that Ableton detects the control script:
1. Launch ProfesorAbelton.app (the First Launch Wizard will install the script).
2. Restart Ableton Live.
3. In Ableton Preferences → Link/Tempo/MIDI:
   - Control Surface: ProfesorAbelton
   - Input/Output: None

Manual install (if wizard fails):
- Copy the RemoteScript/ folder from inside the app bundle to:
  ~/Music/Ableton/User Library/Remote Scripts/ProfesorAbelton/
- Restart Ableton.

3) API Keys
-----------
In the GUI: Settings (⚙️) → API Keys
- Supported providers: GROQ + CLAUDE (MCP tools)

4) License
----------
Enter your Gumroad license key in ⚙️ Settings after first launch.
The app will not process AI requests without a valid license.

5) Troubleshooting
------------------
- "ProfesorAbelton not in Control Surfaces" → restart Ableton after wizard completes.
- App blocked by macOS → right-click → Open (see step 3 above).
- "License not valid" → check your Gumroad key and internet connection.

License: see LICENSE.txt
