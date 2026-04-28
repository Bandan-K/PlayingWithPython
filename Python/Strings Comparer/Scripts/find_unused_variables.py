import os
import re
import json
import json

def extract_vars_from_swift_file(file_path):
    vars_list = [] # List of (variable_name, full_line)
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return vars_list
    
    # Match var variableName = "key"
    pattern = re.compile(r'var\s+(\w+)\s*=\s*".*?"')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                vars_list.append((match.group(1), line))
    return vars_list

def find_file_in_project(root_path, filename):
    print(f"Searching for {filename} in {root_path}...")
    for root, dirs, files in os.walk(root_path):
        if filename in files:
            return os.path.join(root, filename)
    return None

def move_unused_lines_to_bottom(file_path, unused_var_data):
    # unused_var_data is list of (name, line)
    if not unused_var_data:
        return
        
    
    kept_lines = []
    actual_unused_found = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            is_unused = False
            for name, full_line in unused_var_data:
                # Precise match for the definition line
                if full_line == line:
                    is_unused = True
                    actual_unused_found.append(line)
                    break
            if not is_unused:
                kept_lines.append(line)
                
    # Clean up empty lines at the end
    while kept_lines and kept_lines[-1].strip() == "":
        kept_lines.pop()
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(kept_lines)
        f.write("\n\n// MARK: - UNUSED VARIABLES (Moved by script)\n")
        f.writelines(actual_unused_found)
    
    print(f"Successfully moved {len(actual_unused_found)} unused variables to the bottom of {file_path}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.dirname(script_dir)
    config_path = os.path.join(script_dir, "project_config.json")
    
    project_path = "/Users/elluminati/Documents/Product/Hyze 2/driver"
    
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try:
                config = json.load(f)
            except:
                config = {}
    
    # Cache key for variables file
    cache_key = project_path + "_vars"
    vars_file = config.get(cache_key)
    
    if not vars_file or not os.path.exists(vars_file):
        vars_file = find_file_in_project(project_path, "LocalizeKey.swift")
        if vars_file:
            config[cache_key] = vars_file
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"Saved path for this project: {vars_file}")
        else:
            print(f"Error: Could not find LocalizeKey.swift in {project_path}")
            return

    print(f"Checking variables from: {vars_file}")
    vars_data = extract_vars_from_swift_file(vars_file)
    if not vars_data:
        print("No variables found in file.")
        return

    print(f"Found {len(vars_data)} variables. Indexing project code...")
    
    # Index all .swift files
    all_code_content = ""
    file_count = 0
    for root, dirs, files in os.walk(project_path):
        if any(skip in root for skip in ["Pods", ".git", ".xcodeproj", ".xcassets"]):
            continue
            
        for file in files:
            if file.endswith(".swift"):
                file_path = os.path.join(root, file)
                # Still include LocalizeKey.swift to count the definition
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        all_code_content += f.read() + "\n"
                    file_count += 1
                except:
                    pass

    print(f"Indexed {file_count} files. Searching for unused variables and direct key usage...")
    
    unused_vars = []
    direct_key_usage = [] # Keys used directly instead of via variable
    
    # Pre-parse strings file path to skip it during key search
    config_path = os.path.join(script_dir, "project_config.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    strings_file = config.get(project_path)

    for name, line in vars_data:
        # 1. Check if VARIABLE NAME is used
        var_matches = re.findall(r'\b' + re.escape(name) + r'\b', all_code_content)
        
        if len(var_matches) > 1:
            # Variable is used (more than 1 match means it's used outside its definition)
            continue
            
        # 2. If variable is unused, check if STRING KEY is used directly
        # Extract the key from the line: var name = "key"
        key_match = re.search(r'=\s*"([^"]+)"', line)
        if key_match:
            key_value = key_match.group(1)
            # Search for "key_value" (with quotes) to be sure
            # We must ignore the occurrences in Localizable.strings and LocalizeKey.swift
            # So we check if it's found in the "all_code_content" (which already excluded Localizable.strings)
            # But all_code_content DOES include LocalizeKey.swift. 
            # So if count > 1, it's used elsewhere.
            
            key_search_pattern = f'"{key_value}"'
            key_matches = all_code_content.count(key_search_pattern)
            
            if key_matches > 1:
                # Key is used directly in code!
                direct_key_usage.append((name, key_value))
                print(f"[DIRECT KEY USE] Variable '{name}' unused, but key '{key_value}' used directly.")
            else:
                # Both unused
                unused_vars.append((name, line))
                print(f"[UNUSED] {name}")
        else:
            # Fallback if regex fails
            unused_vars.append((name, line))

    print("\n" + "="*30)
    print(f"SEARCH COMPLETE")
    print(f"Total variables checked: {len(vars_data)}")
    print(f"Unused variables: {len(unused_vars)}")
    print(f"Direct key usages: {len(direct_key_usage)}")
    print("="*30 + "\n")

    if unused_vars:
        confirm = input(f"\nDo you want to move these {len(unused_vars)} variables to the end of LocalizeKey.swift? (y/n): ").strip().lower()
        if confirm == 'y':
            move_unused_lines_to_bottom(vars_file, unused_vars)
        else:
            print("Move cancelled.")
    else:
        print("All variables are being used!")

if __name__ == "__main__":
    main()
