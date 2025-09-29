#!/usr/bin/env python3
"""
Re-enable Ollama for local AI
Updates .env to include Ollama back in providers
"""

import os
from pathlib import Path

def update_env_file():
    env_path = Path(".env")
    
    if not env_path.exists():
        print("ERROR: .env file not found!")
        return
    
    # Read current content
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Update AI providers to include ollama
    updated_content = content.replace(
        'AI_PROVIDERS=grok',
        'AI_PROVIDERS=grok,ollama'
    ).replace(
        'MEMORY_SAVE_MODE=true',
        'MEMORY_SAVE_MODE=false'
    )
    
    # Write back
    with open(env_path, 'w') as f:
        f.write(updated_content)
    
    print("OK Ollama re-enabled in .env file")
    print(">> Make sure you have enough RAM for Ollama")
    print(">> Restart the server: python copilot_server.py")
    print(">> Start Ollama: ollama serve")

if __name__ == "__main__":
    update_env_file()
