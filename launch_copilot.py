#!/usr/bin/env python3
"""
Launcher for Ableton AI Copilot
Starts both server and GUI in separate processes
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def main():
    print(" Ableton AI Copilot Launcher")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("copilot_server.py").exists():
        print("ERROR Error: Run this from the ableton-copilot directory")
        input("Press Enter to exit...")
        return
    
    # Check if .env exists
    if not Path(".env").exists():
        print("⚠️  Warning: .env file not found")
        print("📝 Creating basic .env file...")
        with open(".env", "w") as f:
            f.write("# Add your API keys here\n")
            f.write("AI_PROVIDERS=ollama\n")
            f.write("OLLAMA_TIMEOUT=10\n")
    
    print(">> Starting AI Copilot Server...")
    
    # Start server in background
    try:
        server_process = subprocess.Popen(
            [sys.executable, "copilot_server.py"],
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        print(f"OK Server started (PID: {server_process.pid})")
        
        # Wait a moment for server to initialize
        print("⏳ Waiting for server to initialize...")
        time.sleep(2)
        
        print("🎨 Starting GUI...")
        
        # Start GUI in new process/console
        gui_process = subprocess.Popen(
            [sys.executable, "gui_copilot.py"],
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        print(f"OK GUI started (PID: {gui_process.pid})")
        
        print("\\n🎉 Ableton AI Copilot is running!")
        print("📋 Summary:")
        print(f"   - Server PID: {server_process.pid}")
        print(f"   - GUI PID: {gui_process.pid}")
        print("\\n📌 Instructions:")
        print("   - GUI window should appear shortly")
        print("   - Close GUI window to stop the application")
        print("   - Server will continue running in background")
        print("\\nERROR To stop everything:")
        print("   - Close the GUI window")
        print("   - Or press Ctrl+C in this launcher")
        
        # Wait for processes
        try:
            gui_process.wait()
            print("\\n🛑 GUI closed")
        except KeyboardInterrupt:
            print("\\n🛑 Launcher interrupted")
        
        # Cleanup
        if server_process.poll() is None:
            print("🧹 Stopping server...")
            server_process.terminate()
            server_process.wait()
        
        print("OK All processes stopped")
        
    except Exception as e:
        print(f"ERROR Error starting processes: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
