#!/usr/bin/env python3
"""
Fix emoji characters in Python files for Windows terminal compatibility
"""

import re
from pathlib import Path

def fix_emojis_in_file(file_path):
    """Replace emoji characters with ASCII equivalents."""
    
    # Emoji replacements
    replacements = {
        '🤖': '>>',
        '🧠': '>>',
        '🚀': '>>',
        '🔮': '>>',
        '🧮': '>>',
        '✅': 'OK',
        '❌': 'ERROR',
        '⏰': 'TIMEOUT',
        '🔌': '>>',
        '📥': '>>',
        '📤': '>>',
        '🤔': '>>',
        '📡': '>>',
        '💾': '>>',
        '🎵': '',
        '🔧': '>>',
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace emojis
        for emoji, replacement in replacements.items():
            content = content.replace(emoji, replacement)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed emojis in: {file_path}")
            return True
        else:
            print(f"No emojis found in: {file_path}")
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix emojis in all Python files."""
    python_files = [
        "copilot_server.py",
        "gui_copilot.py", 
        "launch_copilot.py"
    ]
    
    fixed_count = 0
    for file_name in python_files:
        file_path = Path(file_name)
        if file_path.exists():
            if fix_emojis_in_file(file_path):
                fixed_count += 1
        else:
            print(f"File not found: {file_name}")
    
    print(f"\\nFixed {fixed_count} files")
    print("You can now run: python copilot_server.py")

if __name__ == "__main__":
    main()
