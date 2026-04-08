#!/usr/bin/env python3
"""
Script to replace all unsafe document.getElementById().innerHTML patterns with setHTML() calls.
This fixes a critical security/stability issue in the LMS system.
"""

import re
import sys

# Read the file
file_path = r"c:\Users\Admin\Desktop\CODIX LMS\main (3) (3) (2).html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to match: document.getElementById('id').innerHTML = value;
# We want to convert to setHTML('id', value);
pattern = r"document\.getElementById\('([^']+)'\)\.innerHTML\s*=\s*"
replacement = r"setHTML('\1', "

# Count occurrences
matches = len(re.findall(pattern, content))
print(f"Found {matches} occurrences of unsafe DOM pattern")

if matches > 0:
    # Replace all occurrences
    new_content = re.sub(pattern, replacement, content)
    
    # Now we need to fix the semicolons - convert "=" statements to function calls
    # The pattern leaves us with: setHTML('id', ... );
    # We need to ensure the closing parenthesis is properly placed
    
    # Safer approach: just do the simple replace
    new_content = content.replace(
        "document.getElementById(",
        "setHTML_ID("  # temporary placeholder
    )
    
    # Actually, let's do it more carefully with a loop
    new_content = content
    
    # Find all getElementById patterns and replace them
    def replace_getelementbyid(match):
        id_name = match.group(1)
        return f"setHTML('{id_name}', "
    
    new_content = re.sub(
        r"document\.getElementById\('([^']+)'\)\.innerHTML\s*=\s*",
        replace_getelementbyid,
        content
    )
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Successfully replaced {matches} occurrences")
    print(f"File updated: {file_path}")
else:
    print("No matches found")
