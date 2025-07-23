import csv
import json
import re

final_json = "output/final_inchi_seq.json"
bindb_csv = "output/bindb.csv"

# csv format
# "Ligand SMILES", "Ligand InChI Key", "Sequence",
# "Ki (nM)", "IC50 (nM)", "Kd (nM)", "EC50 (nM)"

# json format
# {
#     "molecule_name": "T0070907",
#     "protein_target_name": "PP ARa",
#     "protein_uniprot_id": null,
#     "protein_seq_id": null,
#     "binding_metric": "Ki",
#     "value": "0.85",
#     "unit": "mM",
#     "patent_number": "WO-2008024749-A2",
#     "Ligand InChI Key": "FRPJSHKMZHWJBE-UHFFFAOYSA-N",
#     "Sequence": ""
# }

csv_header = [
    "Ligand SMILES",
    "Ligand InChI Key",
    "Sequence",
    "Ki (nM)",
    "IC50 (nM)",
    "Kd (nM)",
    "EC50 (nM)",
    "unit",
]

with open(final_json, "r", encoding="utf-8") as f:
    data = json.load(f)


def value_to_float(value_str):
    """Convert value with scientific notation/formulas to float if possible."""
    value_str = (
        value_str.replace(",", "").replace("×", "e").replace("x", "e").replace(" ", "")
    )
    # Accept numbers like 1.0e-9 or 1.0^−9
    match = re.search(r"([0-9.]+)(?:e|\^)?([-\d]+)?", value_str)
    if match:
        base = float(match.group(1))
        exp = int(match.group(2)) if match.group(2) else 0
        return base * (10 ** exp)
    return None


def parse_range(value):
    """If value is a range or 'X to Y', return the second value (Y) as string."""
    match = re.search(
        r"(?:(?:about|from)?\s*([\d\.\-]+)[^a-zA-Z\d]+)?(?:to|−|-|–|~|—|and)\s*([\d\.\-]+)",
        value,
    )
    if match:
        return match.group(2)
    return value


def parse_plus_minus(val):
    """For '4.7±0.6', '4.7+/−0.6' etc. return sum as string."""
    pm_match = re.match(r"([<>]?\s*\d+\.?\d*)\s*(?:\+/?−|±)\s*(\d+\.?\d*)", val)
    if pm_match:
        left = float(pm_match.group(1).replace("<", "").replace(">", ""))
        right = float(pm_match.group(2))
        return str(round(left + right, 3))
    return val


def convert_to_nM(value, unit):
    """Convert value to nM, if possible. Returns string with possible sign."""
    try:
        if isinstance(value, str):
            value = value.strip()
            # Handle < and > signs
            sign = ""
            if value.startswith("<") or value.startswith(">"):
                sign = value[0]
                value = value[1:].strip()
            # Handle ranges
            value = parse_range(value)
            # Handle plus-minus
            value = parse_plus_minus(value)
            # Handle scientific notation
            num = value_to_float(value)
        else:
            sign = ""
            num = float(value)
        unit = unit.lower().replace("μ", "u").replace("µ", "u").replace(" ", "")
        if num is None:
            return None
        if unit == "nm":
            return f"{sign}{num:.5g}"
        if unit == "um":
            return f"{sign}{num * 1e3:.5g}"
        if unit == "mm":
            return f"{sign}{num * 1e6:.5g}"
        if unit == "m":
            return f"{sign}{num * 1e9:.5g}"
        if unit == "pm":
            return f"{sign}{num * 1e-3:.5g}"
        if unit == "fm":
            return f"{sign}{num * 1e-6:.5g}"
        # If nanogram/mL or other units, cannot convert without more info
        return None
    except Exception as e:
        return None


with open(bindb_csv, "w", encoding="utf-8", newline="") as w_file:
    writer = csv.DictWriter(w_file, fieldnames=csv_header)
    writer.writeheader()

    for row in data:
        if (
            row.get("Ligand InChI Key")
            and row.get("Sequence")
            and row.get("binding_metric")
            and row.get("value")
            and row.get("unit")
        ):
            metric = row["binding_metric"].lower().strip()
            if metric not in ["ic50", "ec50", "kd", "ki"]:
                print(f"skip {metric}")
                continue

            out_row = {
                "Ligand SMILES": row.get("Ligand SMILES", ""),
                "Ligand InChI Key": row.get("Ligand InChI Key", ""),
                "Sequence": row.get("Sequence", ""),
                "Ki (nM)": "",
                "IC50 (nM)": "",
                "Kd (nM)": "",
                "EC50 (nM)": "",
                "unit": "nM",  # Always set to nM after conversion
            }

            converted_value = convert_to_nM(row.get("value", ""), row.get("unit", ""))
            if converted_value is None:
                continue
            if metric == "ic50":
                out_row["IC50 (nM)"] = converted_value
            elif metric == "ec50":
                out_row["EC50 (nM)"] = converted_value
            elif metric == "kd":
                out_row["Kd (nM)"] = converted_value
            elif metric == "ki":
                out_row["Ki (nM)"] = converted_value

            # Set unit as nM after conversion
            out_row["unit"] = "nM"

            writer.writerow(out_row)
