import json
import os
import re
import math

def normalize_value(value_str):
    if not isinstance(value_str, str):
        return None

    s = value_str.lower()
    s = s.replace(' ', '').replace('x', '*').replace('×', '*').replace('≦', '<=').replace('~', '')
    
    # Handle ranges by taking the upper value
    if '-' in s and 'e-' not in s: # avoid scientific notation
        parts = s.split('-')
        if len(parts) == 2:
            try:
                return float(parts[1])
            except (ValueError, IndexError):
                pass # Fallback to other parsers
    if 'to' in s:
        parts = s.split('to')
        if len(parts) == 2:
            try:
                return float(parts[1])
            except (ValueError, IndexError):
                pass

    # Remove operators and uncertainty
    s = re.sub(r'[<>=±]', '', s)

    # Handle scientific notation like 10^{-9} or 1*10^-8
    match = re.search(r'(\d*\.?\d*)\*?10\^\{?(-?\d+)\}?', s)
    if match:
        base = float(match.group(1)) if match.group(1) else 1.0
        exponent = int(match.group(2))
        return base * (10 ** exponent)

    # Handle E notation
    if 'e' in s:
        try:
            return float(s)
        except ValueError:
            pass

    try:
        return float(s)
    except ValueError:
        return None

def normalize_units(unit_str):
    if not isinstance(unit_str, str):
        return None
    
    unit_str = unit_str.lower().replace(' ', '').replace('μ', 'u').replace('µ', 'u')
    
    supported_units = {
        'nm': 1,
        'um': 1000,
        'mm': 1000000,
        'pm': 0.001
    }
    
    return supported_units.get(unit_str)

def normalize_metric_name(metric_str):
    if not isinstance(metric_str, str):
        return None
        
    metric_str = metric_str.lower().replace(' ', '').replace('-', '').replace('₅₀', '50')
    
    if 'ic50' in metric_str or 'pic50' in metric_str:
        return 'IC50'
    if 'ki' in metric_str or 'pki' in metric_str:
        return 'Ki'
    if 'kd' in metric_str or 'pkd' in metric_str:
        return 'Kd'
    if 'ec50' in metric_str or 'pec50' in metric_str:
        return 'EC50'
        
    return None

def process_row(row):
    if not isinstance(row, dict):
        return None

    # 1. Normalize and filter by metric name
    metric = normalize_metric_name(row.get('binding_metric'))
    if not metric:
        return None
    
    # 2. Normalize and filter by unit
    unit_multiplier = normalize_units(row.get('unit'))
    if unit_multiplier is None and not row.get('is_logarithmic'):
        return None

    # 3. Normalize value
    value = normalize_value(row.get('value'))
    if value is None:
        return None

    # 4. Handle logarithmic values
    if row.get('is_logarithmic'):
        # p-value to molar (10^-p_value), then to nanomolar (* 10^9)
        value = (10 ** -value) * 1e9
        unit = 'nM'
    else:
        value = value * unit_multiplier
        unit = 'nM'

    # Create new cleaned row
    new_row = {
        "molecule_name": row.get("molecule_name"),
        "protein_target_name": row.get("protein_target_name"),
        "patent_number": row.get("patent_number"),
        "binding_metric": metric,
        "value": value,
        "unit": unit,
    }
    
    # Filter out rows with any null values in essential fields
    if any(v is None for v in new_row.values()):
        return None
        
    return new_row

def main():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(dir_path, "input/final_json_1.json")
    output_file = os.path.join(dir_path, "output/normalized_data.json")

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading input file: {e}")
        return

    normalized_data = []
    for row in data:
        processed = process_row(row)
        if processed:
            normalized_data.append(processed)
            
    print(f"Total rows processed: {len(data)}")
    print(f"Total rows after normalization and filtering: {len(normalized_data)}")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(normalized_data, f, indent=2, ensure_ascii=False)
        
    print(f"Normalized data saved to {output_file}")

if __name__ == "__main__":
    main()
