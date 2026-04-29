# ==========================================
# SETTINGS - UPDATE THESE PATHS IF NEEDED
# ==========================================
PROJECT_ROOT = "/Users/elluminati/Documents/Product/Hyze 2/merchant"
# ==========================================

import os
import re
import json

def extract_keys_from_strings_file(file_path):
    keys_data = [] # List of (key, line)
    if not os.path.exists(file_path): return keys_data
    pattern = re.compile(r'"([^"]+)"\s*=\s*".*?"\s*;')
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                keys_data.append((match.group(1), line))
    return keys_data

def extract_vars_from_swift_file(file_path):
    vars_data = [] # List of (variable_name, key_value, full_line)
    if not os.path.exists(file_path): return vars_data
    # Updated pattern to handle 'let' or 'var'
    pattern = re.compile(r'(?:let|var)\s+(\w+)\s*=\s*"([^"]+)"')
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                vars_data.append((match.group(1), match.group(2), line))
    return vars_data

def find_file_in_project(root_path, filenames):
    print(f"Searching for {filenames} in {root_path}...")
    for root, dirs, files in os.walk(root_path):
        for filename in filenames:
            if filename in files: return os.path.join(root, filename)
    return None

def move_lines_to_bottom(file_path, lines_to_move, label):
    if not lines_to_move: return
    kept_lines = []
    found_lines_to_move = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line in lines_to_move:
                found_lines_to_move.append(line)
            else:
                kept_lines.append(line)
                
    while kept_lines and kept_lines[-1].strip() == "":
        kept_lines.pop()
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(kept_lines)
        f.write(f"\n\n// MARK: - {label} (Moved by script)\n")
        f.writelines(found_lines_to_move)
    print(f"Moved {len(found_lines_to_move)} lines to bottom of {os.path.basename(file_path)}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "project_config.json")
    
    # Load config
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try: config = json.load(f)
            except: pass
            
    # Resolve paths
    strings_key = PROJECT_ROOT + "_strings"
    vars_key = PROJECT_ROOT + "_vars"
    
    strings_file = config.get(strings_key)
    if not strings_file or not os.path.exists(strings_file):
        strings_file = find_file_in_project(PROJECT_ROOT, ["Localizable.strings"])
        if strings_file: config[strings_key] = strings_file
        
    vars_file = config.get(vars_key)
    if not vars_file or not os.path.exists(vars_file):
        # Look for either name
        vars_file = find_file_in_project(PROJECT_ROOT, ["LocalizeKey.swift", "iOSFile", "iOSFile.swift"])
        if vars_file: config[vars_key] = vars_file
        
    # Save config if updated
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

    if not strings_file or not vars_file:
        print(f"Error: Could not find required files in {PROJECT_ROOT}.")
        print(f"Strings: {strings_file}")
        print(f"Vars: {vars_file}")
        return

    # Extensions
    exts = {".swift", ".m", ".h", ".storyboard", ".xib"}
    
    print("Indexing project code...")
    all_code = ""
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if any(skip in root for skip in ["Pods", ".git", ".xcodeproj", ".xcassets"]): continue
        for file in files:
            if os.path.splitext(file)[1].lower() in exts:
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        all_code += f.read() + "\n"
                except: pass

    # 1. Analyze Swift Variables
    vars_data = extract_vars_from_swift_file(vars_file)
    unused_vars_lines = []
    used_keys_via_vars = set() # Keys whose variables are USED
    
    print(f"Analyzing {len(vars_data)} Swift variables...")
    for name, key, line in vars_data:
        # Check variable usage
        var_count = len(re.findall(r'\b' + re.escape(name) + r'\b', all_code))
        if var_count > 1:
            # Variable is used! Key is used!
            used_keys_via_vars.add(key)
        else:
            # Variable dead. Now check if Key is used as a string literal elsewhere
            if all_code.count(f'"{key}"') <= 1:
                unused_vars_lines.append(line)

    # 2. Analyze String Keys
    keys_data = extract_keys_from_strings_file(strings_file)
    unused_strings_lines = []
    print(f"Analyzing {len(keys_data)} String keys...")
    for key, line in keys_data:
        # A key is USED if:
        # a) Its variable is used (in used_keys_via_vars)
        # b) It appears as a string literal elsewhere (count > 1 in all_code because 1 is in LocalizeKey)
        if key in used_keys_via_vars:
            continue
            
        if all_code.count(f'"{key}"') <= 1:
            unused_strings_lines.append(line)

    print("\n" + "="*30)
    print(f"TRULY UNUSED SWIFT VARS: {len(unused_vars_lines)}")
    print(f"TRULY UNUSED STRING KEYS: {len(unused_strings_lines)}")
    print("="*30 + "\n")

    if unused_vars_lines or unused_strings_lines:
        confirm = input("Move all truly unused items to bottom of their files? (y/n): ").strip().lower()
        if confirm == 'y':
            move_lines_to_bottom(vars_file, unused_vars_lines, "UNUSED VARIABLES")
            move_lines_to_bottom(strings_file, unused_strings_lines, "UNUSED STRINGS")
        else:
            print("Action cancelled.")
    else:
        print("Everything is used! Good job.")

if __name__ == "__main__":
    main()
