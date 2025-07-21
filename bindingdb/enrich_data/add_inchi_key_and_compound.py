import json

import requests

def name_to_inchi_key(name):
    # Get CID (Compound ID) from the name
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/cids/JSON"
    resp = requests.get(url)
    if not resp.ok:
        return None
    cids = resp.json().get('IdentifierList', {}).get('CID', [])
    if not cids:
        return None

    # Get InChIKey for the first CID
    cid = cids[0]
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/InChIKey/JSON"
    resp = requests.get(url)
    if not resp.ok:
        return None
    props = resp.json()['PropertyTable']['Properties'][0]
    return props.get('InChIKey')

# Example usage:
# print(name_to_inchi_key("aspirin"))  # Should print InChIKey for aspirin
# BSYNRYMUTXBXSQ-UHFFFAOYSA-N

def get_sequence_uniprot(protein_name):
    # Search UniProt for the protein name and get the best match
    url = f"https://rest.uniprot.org/uniprotkb/search?query={protein_name}&format=json&fields=accession"
    resp = requests.get(url)
    if not resp.ok or not resp.json().get("results"):
        return None
    accession = resp.json()["results"][0]["primaryAccession"]

    # Get the sequence for this accession
    seq_url = f"https://rest.uniprot.org/uniprotkb/{accession}.fasta"
    seq_resp = requests.get(seq_url)
    if not seq_resp.ok:
        return None

    # Parse FASTA to get the sequence string
    fasta = seq_resp.text
    lines = fasta.splitlines()
    sequence = "".join(line.strip() for line in lines if not line.startswith(">"))
    return sequence


# Example usage:
# print(get_sequence_uniprot("Insulin"))
# MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAEDLQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN

input = "input/final_json.json"
output = "output/final_inchi_seq.json"

with open(input, 'r', encoding='utf-8') as f:
    results = json.load(f)
    for result in results:
        inchi_key = None
        sequence = None
        molecule_name = result['molecule_name']
        if molecule_name:
            inchi_key = name_to_inchi_key(molecule_name)
        target_name = result['protein_target_name']
        if target_name:
            sequence = get_sequence_uniprot(target_name)
        result['Ligand InChI Key'] = inchi_key
        result['Sequence'] = sequence

with open(output, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)