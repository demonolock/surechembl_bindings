import csv
import json

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
    "unit"
]

with open(final_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

with open(bindb_csv, 'w', encoding='utf-8', newline='') as w_file:
    writer = csv.DictWriter(w_file, fieldnames=csv_header)
    writer.writeheader()

    for row in data:
        # Ensure required keys are present
        if (
            row["Ligand InChI Key" ] and
            row["Sequence"] and
            row["binding_metric"] and
            row["value"] and
            row["unit"]
        ):
            out_row = {
                "Ligand SMILES": row.get("Ligand SMILES", ""),
                "Ligand InChI Key": row.get("Ligand InChI Key", ""),
                "Sequence": row.get("Sequence", ""),
                "Ki (nM)": "",
                "IC50 (nM)": "",
                "Kd (nM)": "",
                "EC50 (nM)": "",
                "unit": row.get( "unit", "")
            }
            metric = row["binding_metric"]
            if metric not in ['IC50', 'EC50', 'Kd', 'Ki']:
                print(f"skip {metric}")
                continue
            out_row[f"{metric} (nM)"] = row.get("value", "")
            writer.writerow(out_row)

    
    