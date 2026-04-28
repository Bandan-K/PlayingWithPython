import os
import re
import json
import shutil

def extract_keys_from_strings_file(file_path):
    keys = []
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return keys
    
    # Match "key" = "value";
    pattern = re.compile(r'"([^"]+)"\s*=\s*".*?"\s*;')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                keys.append(match.group(1))
    return keys

def find_file_in_project(root_path, filename):
    print(f"Searching for {filename} in {root_path}...")
    for root, dirs, files in os.walk(root_path):
        if filename in files:
            return os.path.join(root, filename)
    return None

def move_unused_keys_to_bottom(file_path, keys_to_remove):
    if not keys_to_remove:
        return
        
    print(f"Creating backup: {file_path}.bak")
    shutil.copy2(file_path, file_path + ".bak")
    
    kept_lines = []
    unused_lines = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            is_unused = False
            # Check if line contains any of the unused keys
            for key in keys_to_remove:
                if f'"{key}"' in line and '=' in line:
                    is_unused = True
                    unused_lines.append(line)
                    break
            if not is_unused:
                kept_lines.append(line)
                
    # Clean up empty lines at the end of kept_lines if any
    while kept_lines and kept_lines[-1].strip() == "":
        kept_lines.pop()
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(kept_lines)
        f.write("\n\n// MARK: - UNUSED STRINGS (Moved by script)\n")
        f.writelines(unused_lines)
    
    print(f"Successfully moved {len(unused_lines)} unused strings to the bottom of {file_path}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.dirname(script_dir)
    config_path = os.path.join(script_dir, "project_config.json")
    
    # Default project path provided by user
    project_path = "/Users/elluminati/Documents/Product/Hyze 2/driver"
    
    # Load or Find strings file path
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try:
                config = json.load(f)
            except:
                config = {}
    
    # Use project_path as key to support multiple projects
    strings_file = config.get(project_path)
    
    if not strings_file or not os.path.exists(strings_file):
        strings_file = find_file_in_project(project_path, "Localizable.strings")
        if strings_file:
            config[project_path] = strings_file
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"Saved path for this project: {strings_file}")
        else:
            print(f"Error: Could not find Localizable.strings in {project_path}")
            return

    # Extensions to check
    extensions = {".swift", ".m", ".h", ".storyboard", ".xib"}
    
    print(f"Using strings from: {strings_file}")
    keys = extract_keys_from_strings_file(strings_file)
    if not keys:
        print("No keys found.")
        return

    print(f"Found {len(keys)} keys. Indexing project code...")
    
    # Speed Optimization: Read all code into memory once
    all_code_content = ""
    file_count = 0
    for root, dirs, files in os.walk(project_path):
        if any(skip in root for skip in ["Pods", ".git", ".xcodeproj", ".xcassets"]):
            continue
            
        for file in files:
            if os.path.splitext(file)[1].lower() in extensions:
                file_path = os.path.join(root, file)
                if file_path == strings_file:
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        all_code_content += f.read() + "\n"
                    file_count += 1
                except:
                    pass

    print(f"Indexed {file_count} files. Searching for unused keys...")
    
    unused_keys = []
    for key in keys:
        if key not in all_code_content:
            unused_keys.append(key)

    print("\n" + "="*30)
    print(f"SEARCH COMPLETE")
    print(f"Total keys checked: {len(keys)}")
    print(f"Unused keys found: {len(unused_keys)}")
    print("="*30 + "\n")

    if unused_keys:
        output_file = os.path.join(base_path, "Results", "unused_keys.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            for key in unused_keys:
                f.write(f"{key}\n")
                print(f"[UNUSED] {key}")
        print(f"\nFull list saved to: {output_file}")
        
        # Interactive move
        confirm = input(f"\nDo you want to move these {len(unused_keys)} keys to the end of Localizable.strings? (y/n): ").strip().lower()
        if confirm == 'y':
            move_unused_keys_to_bottom(strings_file, unused_keys)
        else:
            print("Move cancelled.")
    else:
        print("All keys are being used! Good job.")

if __name__ == "__main__":
    main()
