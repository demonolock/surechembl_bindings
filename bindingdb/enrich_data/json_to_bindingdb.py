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
    "patent_number",
    "molecule_name",
    "protein_target_name",
]


def json_to_bindingdb(data: list[dict], bindb_csv_path: str) -> None:
    with open(bindb_csv_path, "w", encoding="utf-8", newline="") as w_file:
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
                    "unit": row.get("unit", ""),
                    "patent_number": row.get("patent_number", ""),
                    "molecule_name": row.get("molecule_name", ""),
                    "protein_target_name": row.get("protein_target_name", ""),
                }

                value = row.get("value", "")
                if value is None:
                    continue
                if metric == "ic50":
                    out_row["IC50 (nM)"] = value
                elif metric == "ec50":
                    out_row["EC50 (nM)"] = value
                elif metric == "kd":
                    out_row["Kd (nM)"] = value
                elif metric == "ki":
                    out_row["Ki (nM)"] = value

                writer.writerow(out_row)


if __name__ == "__main__":
    with open(final_json, "r", encoding="utf-8") as f:
        final_json = json.load(f)
    json_to_bindingdb(final_json, bindb_csv)
