import requests

inchikey = "YXFVVABEGXRONW-UHFFFAOYSA-N"
url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/{inchikey}/property/IUPACName,Title,CanonicalSMILES/JSON"

resp = requests.get(url)
if resp.ok:
    props = resp.json()["PropertyTable"]["Properties"][0]
    name = props.get("Title") or props.get("IUPACName")
    print("Name:", name)
else:
    print("Not found in PubChem")
