PROFESOR ABELTON — Quick Start
Version: 2.0.1

REQUIREMENTS:
- Ableton Live 11 or 12  (Live 10 is NOT supported)
- Windows 10/11 or macOS (Apple Silicon / Intel)
- Internet connection for AI (Groq / Claude API keys)


This is a PORTABLE application — no traditional installation required.

1) How to run
-------------
1. Extract the full ZIP (do not run directly from inside the ZIP).
2. Open the folder: ProfesorAbelton\
3. Launch: ProfesorAbelton.exe

IMPORTANT:
- Do not delete or move the "_internal" folder or any other files next to the .exe.
- The .exe must remain in the same folder as the rest of the bundle.

2) Ableton setup (Control Surface)
-----------------------------------
So that Ableton detects the control script:
1. Launch ProfesorAbelton.exe (the First Launch Wizard will guide you).
2. Restart Ableton Live.
3. In Ableton Preferences → Link/Tempo/MIDI:
   - Control Surface: ProfesorAbelton
   - Input/Output: None

Manual install (if wizard fails):
- The script is located in this package under: RemoteScript\
- Destination (Windows, typical):
  %APPDATA%\Ableton\Live XX\Preferences\User Remote Scripts\ProfesorAbelton\

3) API Keys
-----------
In the GUI: Settings (⚙️) → API Keys
- Supported providers: GROQ + CLAUDE (MCP tools)

4) License
----------
Enter your Gumroad license key in ⚙️ Settings after first launch.
The app will not process AI requests without a valid license.

5) Window / tray behaviour
--------------------------
- The window appears in the taskbar like a normal application.
- System tray is used only when you click HIDE or close the window (X),
  if tray support is available on your system.

License: see LICENSE.txt
