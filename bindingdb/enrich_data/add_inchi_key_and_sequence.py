import json
import os
import random
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import shelve

input_file = "input/normalized_data.json"
output_file = "output/final_inchi_seq.json"

# File paths for caches
dir = os.path.dirname(os.path.abspath(__file__))
inchi_key_cache_file = os.path.join(dir, "output/inchi_key_cache.db")
sequence_cache_file = os.path.join(dir, "output/sequence_cache.db")


def skip_nulls(row):
    return not (
        row.get("molecule_name")
        and row.get("protein_target_name")
        and row.get("binding_metric")
        and row.get("value")
        and row.get("unit")
        and row.get("patent_number")
    )


def wrong_metric(row):
    metric = row.get("binding_metric", "").replace(" ", "").lower().strip()
    return metric not in ["kd", "ki", "ic50", "ec50"]


def get_inchi_key_pubchem(name):
    try:
        url = (
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/cids/JSON"
        )
        resp = requests.get(url, timeout=10)
        if not resp.ok:
            return None
        cids = resp.json().get("IdentifierList", {}).get("CID", [])
        if not cids:
            return None
        cid = cids[0]
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/InChIKey/JSON"
        resp = requests.get(url, timeout=10)
        if not resp.ok:
            return None
        props = resp.json().get("PropertyTable", {}).get("Properties", [{}])[0]
        return props.get("InChIKey")
    except Exception:
        return None


def get_inchi_key_surechembl(name):
    try:
        url = f"https://www.surechembl.org/api/chemical/name/{name}"
        resp = requests.get(url, timeout=10)
        if not resp.ok:
            return None
        data = resp.json()
        # SureChEMBL API returns a list of results; InChIKey may be under various keys
        if isinstance(data, list) and data:
            result = data[0]
            return result.get("standardInchiKey") or result.get("inchiKey")
        elif isinstance(data, dict):
            return data.get("standardInchiKey") or data.get("inchiKey")
        return None
    except Exception:
        return None


# You can add more fallback services as needed, e.g., ChemSpider, OPSIN, etc.


def name_to_inchi_key(name, inchi_key_cache):
    if name in inchi_key_cache:
        return inchi_key_cache[name]

    inchi_key = get_inchi_key_pubchem(name)
    if inchi_key:
        inchi_key_cache[name] = inchi_key
        return inchi_key

    # If not found, try SureChEMBL
    inchi_key = get_inchi_key_surechembl(name)
    if inchi_key:
        inchi_key_cache[name] = inchi_key
        return inchi_key
    # Do NOT cache None if all fail
    return None


def random_email(domain="gmail.com"):
    username = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{domain}"


def get_sequence_uniprot(protein_name, sequence_cache):
    if protein_name in sequence_cache:
        return sequence_cache[protein_name]
    url = f"https://rest.uniprot.org/uniprotkb/search?query={protein_name}&format=json&fields=accession"
    try:
        resp = requests.get(url, timeout=15)
        if resp.ok and resp.json().get("results"):
            accession = resp.json()["results"][0]["primaryAccession"]
            seq_url = f"https://rest.uniprot.org/uniprotkb/{accession}.fasta"
            seq_resp = requests.get(seq_url, timeout=15)
            if seq_resp.ok:
                fasta = seq_resp.text
                lines = fasta.splitlines()
                sequence = "".join(
                    line.strip() for line in lines if not line.startswith(">")
                )
                if sequence:
                    sequence_cache[protein_name] = sequence
                    return sequence
    except Exception as e:
        pass  # Try next source

    # 2. Try GenBank/RefSeq via NCBI Entrez (requires Biopython)
    # Тут может быть  HTTP Error 429: Too Many Requests
    # Но я расчитываю что редко сюда будем попадать с реальным сиквенсом. Потом можно улучшить и обернуть в rate limit.
    try:
        from Bio import Entrez, SeqIO

        Entrez.email = random_email()
        # Search for the protein by name in protein db (includes GenBank, RefSeq)
        handle = Entrez.esearch(db="protein", term=protein_name, retmax=1)
        record = Entrez.read(handle)
        if record["IdList"]:
            protein_id = record["IdList"][0]
            fetch_handle = Entrez.efetch(
                db="protein", id=protein_id, rettype="fasta", retmode="text"
            )
            seq_record = SeqIO.read(fetch_handle, "fasta")
            sequence = str(seq_record.seq)
            if sequence:
                time.sleep(1)  # rate limit
                print("Found sequence:", sequence)
                sequence_cache[protein_name] = sequence
                return sequence
    except Exception as e:
        pass

    return None


def process_one(result, inchi_key_cache, sequence_cache):
    inchi_key = None
    sequence = None
    molecule_name = result.get("molecule_name")
    if molecule_name:
        inchi_key = name_to_inchi_key(molecule_name, inchi_key_cache)
    if inchi_key:
        result["Ligand InChI Key"] = inchi_key
        target_name = result.get("protein_target_name")
        if target_name:
            sequence = get_sequence_uniprot(target_name, sequence_cache)
        result["Sequence"] = sequence
    return result


def add_inchi_key_and_sequence(binding: dict, max_workers: int = 1) -> list[dict]:
    updated_bindings = []

    # Open shelve persistent caches
    with shelve.open(
        inchi_key_cache_file, writeback=True
    ) as inchi_key_cache, shelve.open(
        sequence_cache_file, writeback=True
    ) as sequence_cache:

        def process_wrapper(result):
            return process_one(result, inchi_key_cache, sequence_cache)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for result in binding:
                if (
                    not isinstance(result, dict)
                    or skip_nulls(result)
                    or wrong_metric(result)
                ):
                    print(f"Skip the row: {result}")
                    continue
                futures.append(executor.submit(process_wrapper, result))
            for future in as_completed(futures):
                try:
                    updated_binding = future.result()
                    updated_bindings.append(updated_binding)
                    print(f"Add the row: {updated_binding}")
                except Exception as e:
                    print(f"Error processing result: {e}")

        # Explicitly sync caches to disk
        inchi_key_cache.sync()
        sequence_cache.sync()

    return updated_bindings


if __name__ == "__main__":
    with open(input_file, "r", encoding="utf-8") as f:
        bindings = json.load(f)
    updated_bindings = add_inchi_key_and_sequence(bindings)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(updated_bindings, f, ensure_ascii=False, indent=2)