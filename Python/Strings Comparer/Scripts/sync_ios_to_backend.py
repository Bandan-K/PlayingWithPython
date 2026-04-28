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
    
    comparison_file = os.path.join(result_dir, 'app_backend_customer_comparison.json')
    strings_file = os.path.join(source_dir, 'Localizable.strings')
    
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

    # token = 'U2FsdGVkX18qTCcnDuXb5FGrFfroz7ZUtt9F1Utq9kdj9bHgPUIy6I/QGUqrjLJq55b1Buaprje47rM+N+wD+TM6EfQhzlNqKSx9K6wei5YRl1zEGqR1AwyLykVyFb8j1FErkloztRKNkhJXART/b0GRazlUT/YtMEM7NLSNnrS+fgkq2+Th8JIsYvmTor+FHftQqbscqWc3kCcEXVpQHinTJW7+nEGAIuUsPGTlqjum/Vs4yY3G9MZPdMFiE1kQ18GYTjhuiu1EAuvtC4TQNdXHLoyzi7k0pZ3DOdj/ozRFYyXZ/YF4g2fNNy1xzBYnhyYvOp/iZnYl6AP/vHyHwKXlTtOb9RLwqwwCEVMs1PJ4MRZDzxEnqR2tCWt4e41j17bXOj7OHOneIHgIvYX20jB8+KtqXYcfLYV/qZ+sEkMQ+lap9PV/Ewt0mgDSBLJg'
    token = 'U2FsdGVkX19KbrKC3PENVXgbf4wBx7ur3KLumeztsW+MDxR90rtbkFqTJ5HKo3Fq3xLC2n6TnZa10hmd/siiTH6sJklVt7y0jw1L5s2DBHItA1J3Vu1fY8S9eGQHb41IDQR7xLD7hTi8PQEQ0ajEtZf4AX4TeUV0jNvjXFhN6LCp5n+RkT01C/vS2iJUtmIFuZ6Io5ALbfRp0V/6J/efUfr1++zIishRzu1CVbJpVBvG3NcmLPH6PCY4Dr+PPcgz/W/WX+qtISYs4KSkS2UfoZZZqJ4jong1x0QvTY/FkpgWAfCFVpJRZGiiu00gkGhuYTbiER5r5X4IXBfOPu+/9ynNVOSlP0t2Co0tLAkvtoF2cYV9CJM5MutaPHSX59LVhn1n8tvZMESQDO4hf2hqI0JAv75XeMeeBxc/dApzNbEHtZNkAp+brKOPYBkPa6qi'
    
    headers = {
        'authorization': f'Bearer {token}',
        'content-type': 'application/json'
    }
    
    payload = {
        "stringType": 2,
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
