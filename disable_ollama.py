#!/usr/bin/env python3
"""
Disable Ollama to save memory
Updates .env to use only cloud APIs
"""

import os
from pathlib import Path

def update_env_file():
    env_path = Path(".env")
    
    if not env_path.exists():
        print("ERROR: .env file not found!")
        print("TIP: Create .env file first with your API keys")
        return
    
    # Read current content
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Update AI providers to exclude ollama
    updated_content = content.replace(
        'AI_PROVIDERS=grok,ollama',
        'AI_PROVIDERS=grok'
    ).replace(
        'AI_PROVIDERS=ollama,grok',
        'AI_PROVIDERS=grok'
    ).replace(
        'AI_PROVIDERS=ollama',
        'AI_PROVIDERS=grok'
    )
    
    # Add comment about memory saving
    if 'MEMORY_SAVE_MODE' not in updated_content:
        updated_content += "\n# Memory save mode - Ollama disabled\nMEMORY_SAVE_MODE=true\n"
    
    # Write back
    with open(env_path, 'w') as f:
        f.write(updated_content)
    
    print("OK Ollama disabled in .env file")
    print(">> Memory usage should be much lower now")
    print(">> Restart the server: python copilot_server.py")

if __name__ == "__main__":
    update_env_file()
