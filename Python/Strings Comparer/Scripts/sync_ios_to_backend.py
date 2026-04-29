import json
import os
import re
import requests

def parse_localizable_strings(file_path):
    mapping = {}
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return mapping
    
    # Matches "key" = "value";
    pattern = re.compile(r'"([^"]+)"\s*=\s*"(.*?)"\s*;', re.DOTALL)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        matches = pattern.findall(content)
        for key, value in matches:
            mapping[key] = value
            
    return mapping

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.dirname(script_dir)
    
    result_dir = os.path.join(base_path, 'Results')
    source_dir = os.path.join(base_path, 'SourceFiles')

    # Input app type
    print("\nSelect App Type (default is customer):")
    print("1. customer")
    print("2. driver")
    print("3. merchant")
    print("4. picker")
    choice = input("Enter number or name [customer]: ").strip().lower()
    
    app_map = {"1": "customer", "2": "driver", "3": "merchant", "4": "picker"}
    app_type = app_map.get(choice, choice if choice else "customer")

    # String Type Mapping
    type_map = {
        "customer": 2,
        "driver": 3,
        "merchant": 8
    }
    
    comparison_file = os.path.join(result_dir, f'app_backend_{app_type}_comparison.json')
    strings_file = os.path.join(source_dir, f'{app_type}/Localizable.strings')
    
    if not os.path.exists(comparison_file):
        print(f"Error: {comparison_file} not found. Run comparison script first.")
        return

    print("Loading comparison data...")
    with open(comparison_file, 'r') as f:
        comp_data = json.load(f)
    
    ios_missing_keys = comp_data.get('in_apps_not_in_backend', {}).get('ios', [])
    print(f"Found {len(ios_missing_keys)} keys in iOS missing from backend.")

    print("Parsing Localizable.strings for values...")
    local_mapping = parse_localizable_strings(strings_file)
    
    # Build batch data
    batch_data = {}
    for key in ios_missing_keys:
        if key in local_mapping:
            batch_data[key] = {"en": local_mapping[key]}
    
    if not batch_data:
        print("No values found for missing keys. Check Localizable.strings.")
        return

    print(f"Preparing to sync {len(batch_data)} keys to backend...")

    # url = 'https://api.hyze.ai/api/language/strings'
    url = 'https://demoapi.starlor.ai/api/language/strings'

    # token = 'U2FsdGVkX19uma2lKrLyZoG67pxbaxCKQa5nvp1MeodAf2Q8p/iD2sirZGwWSs3mFWTgthIpFN5KLap0ghX3uB6KyIbcdupaluAgldc/aCtAa7UhKpFgtczFIurMgdiCTV4M5zZDBh8VHjp32d+ti25sb0hNB45M8MAHeDFcpUGmomD1DbN6pT7R0i2/tdbb+qZzzjAxX7akP09H5tfgYZXn2YldSqlCVOemBpznkChVHt4SlboAS3pRlMy62bbS4WI204fj14UXaPqZreMuKQ9QPdCEcsLR/hK/XhjVfy3By6eCOMj6zpRRgYOjOyW4dvPD7d/InPYTlgmmmI2INIrCiC7K6T6ZkFGVIcMdcAG+Mg5WLMw00KyOkB31XljROq5LA/JSEozvvUMDdkELIaksj/jZyz3/QwS0cxz9l+BkW3Ju35575Bp7og+7Wxqd'
    token = 'U2FsdGVkX19KbrKC3PENVXgbf4wBx7ur3KLumeztsW+MDxR90rtbkFqTJ5HKo3Fq3xLC2n6TnZa10hmd/siiTH6sJklVt7y0jw1L5s2DBHItA1J3Vu1fY8S9eGQHb41IDQR7xLD7hTi8PQEQ0ajEtZf4AX4TeUV0jNvjXFhN6LCp5n+RkT01C/vS2iJUtmIFuZ6Io5ALbfRp0V/6J/efUfr1++zIishRzu1CVbJpVBvG3NcmLPH6PCY4Dr+PPcgz/W/WX+qtISYs4KSkS2UfoZZZqJ4jong1x0QvTY/FkpgWAfCFVpJRZGiiu00gkGhuYTbiER5r5X4IXBfOPu+/9ynNVOSlP0t2Co0tLAkvtoF2cYV9CJM5MutaPHSX59LVhn1n8tvZMESQDO4hf2hqI0JAv75XeMeeBxc/dApzNbEHtZNkAp+brKOPYBkPa6qi'
    
    headers = {
        'authorization': f'Bearer {token}',
        'content-type': 'application/json'
    }
    
    payload = {
        "stringType": type_map[app_type],
        "data": batch_data
    }

    try:
        # Sending in one big batch as requested/implied
        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Successfully synced strings to backend!")
            print(f"Response: {response.json()}")
        else:
            print(f"Failed to sync. Status: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    main()
