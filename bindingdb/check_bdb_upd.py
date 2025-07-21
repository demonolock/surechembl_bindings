import os

import pandas as pd
import numpy as np
import argparse
from rdkit import Chem
from tqdm import tqdm
from rdkit.Chem import rdchem
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.rdchem import BondType as BT
from typing import Optional

def standardize(smiles):
    # follows the steps in
    # https://github.com/greglandrum/RSC_OpenScience_Standardization_202104/blob/main/MolStandardize%20pieces.ipynb
    # as described **excellently** (by Greg) in
    # https://www.youtube.com/watch?v=eWTApNX8dJQ
    try:
        mol = Chem.MolFromSmiles(smiles)
    except TypeError:
        print(f"Failed for {smiles}, {type(smiles)}")
        mol = None
    if mol is None:
        return None
    # removeHs, disconnect metal atoms, normalize the molecule, reionize the molecule
    clean_mol = rdMolStandardize.Cleanup(mol)

    # if many fragments, get the "parent" (the actual mol we are interested in)
    parent_clean_mol = rdMolStandardize.FragmentParent(clean_mol)

    # try to neutralize molecule
    uncharger = rdMolStandardize.Uncharger()  # annoying, but necessary as no convenience method exists
    uncharged_parent_clean_mol = uncharger.uncharge(parent_clean_mol)

    # note that no attempt is made at reionization at this step
    # nor at ionization at some pH (rdkit has no pKa caculator)
    # the main aim to to represent all molecules from different sources
    # in a (single) standard way, for use in ML, catalogue, etc.

    try:
        te = rdMolStandardize.TautomerEnumerator()  # idem
        taut_uncharged_parent_clean_mol = te.Canonicalize(uncharged_parent_clean_mol)
    except RuntimeError:
        taut_uncharged_parent_clean_mol = None

    return taut_uncharged_parent_clean_mol

def standardize_and_validate_smiles(smiles: str) -> Optional[str]:
    ATOM_LIST = list(range(1, 119))
    CHIRALITY_LIST = [
        Chem.rdchem.ChiralType.CHI_UNSPECIFIED,
        Chem.rdchem.ChiralType.CHI_TETRAHEDRAL_CW,
        Chem.rdchem.ChiralType.CHI_TETRAHEDRAL_CCW,
        Chem.rdchem.ChiralType.CHI_OTHER
    ]
    ATOM_DEGREE = [0, 1, 2, 3, 4, 5, 6]
    BOND_LIST = [BT.SINGLE, BT.DOUBLE, BT.TRIPLE, BT.AROMATIC]
    BONDDIR_LIST = [
        Chem.rdchem.BondDir.NONE,
        Chem.rdchem.BondDir.ENDUPRIGHT,
        Chem.rdchem.BondDir.ENDDOWNRIGHT
    ]
    try:
        mol = standardize(smiles)
        if mol is None:
            return None
        standardized_smiles = Chem.MolToSmiles(mol)
        mol = Chem.MolFromSmiles(standardized_smiles)
        if mol is None:
            # sometimes rdkit cannot parse its own output
            return None
        # now check that iMolCLR would understand the molecule
        mol = Chem.AddHs(mol)
        for atom in mol.GetAtoms():
            ATOM_LIST.index(atom.GetAtomicNum())
            CHIRALITY_LIST.index(atom.GetChiralTag())
            ATOM_DEGREE.index(atom.GetDegree())
        for bond in mol.GetBonds():
            BOND_LIST.index(bond.GetBondType()),
            BONDDIR_LIST.index(bond.GetBondDir())
        return standardized_smiles
    except ValueError:
        return None

if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    our_output = os.path.join(dir_path, "enrich_data", "output", "bindb.csv")

    parser = argparse.ArgumentParser(description='Evaluate test data against BindingDB dataset.')
    parser.add_argument('--test_csv', default=our_output, help='Path to test CSV file')
    parser.add_argument('--mol_representation_filter', default='InChI_key', choices=['smiles', 'InChI_key'],
                        help='Which molecular representation to use for identifying unique ligand-target pairs (default: smiles)')
    args = parser.parse_args()

    df = pd.read_csv(
        'BindingDB_singlechain.csv', sep=',',
        usecols=[
            "Ligand SMILES", "Ligand InChI", "Ligand InChI Key",
            "Target Name", "Sequence",
            "Ki (nM)", "IC50 (nM)", "Kd (nM)", "EC50 (nM)", "Curation/DataSource"
        ], dtype=str
    )

    test = pd.read_csv(
        args.test_csv,
        usecols=[
            "Ligand SMILES", "Ligand InChI Key", "Sequence",
            "Ki (nM)", "IC50 (nM)", "Kd (nM)", "EC50 (nM)"
        ], dtype=str
    )

    if args.mol_representation_filter == 'smiles':
        print("Using standardized SMILES for molecule-target comparison...")
        test["Ligand SMILES"] = test["Ligand SMILES"].apply(standardize_and_validate_smiles)
        cols = ['Ligand SMILES', 'Sequence']
    else:
        print("Using InChI Key for molecule-target comparison...")
        cols = ['Ligand InChI Key', 'Sequence']

    existing_pairs = set(map(tuple, df[cols].dropna().values))
    new_mask = ~test[cols].agg(tuple, axis=1).isin(existing_pairs)
    new_pairs_count = new_mask.sum()

    print(f"Number of novel ligand-target pairs: {new_pairs_count}")

    aff_cols = ["Ki (nM)", "IC50 (nM)", "Kd (nM)", "EC50 (nM)"]
    merged = test[cols + aff_cols].merge(
        df[cols + aff_cols], on=cols, how="inner",
        suffixes=("_patents", "_bdb")
    )

    for c in aff_cols:
        merged[f"{c}_patents"] = pd.to_numeric(merged[f"{c}_patents"].astype(str).str.strip(' <>~'), errors='coerce')
        merged[f"{c}_bdb"] = pd.to_numeric(merged[f"{c}_bdb"].astype(str).str.strip(' <>~'), errors='coerce')

    corr_values = []
    corr = {}
    for c in aff_cols:
        a = merged[f"{c}_patents"]
        b = merged[f"{c}_bdb"]
        mask = a.notna() & b.notna()
        n = mask.sum()
        if n > 1:
            r = a[mask].corr(b[mask], method="pearson")
            corr[c] = r
            corr_values.append(r)
        else:
            corr[c] = np.nan

    print("\nCorrelation values:")
    for k, v in corr.items():
        if np.isnan(v):
            print(f"{k:8s}: insufficient data")
        else:
            print(f"{k:8s}: {v:.3f}")

    valid_corr = [v for v in corr_values if not np.isnan(v)]
    average_corr = np.mean(valid_corr) if valid_corr else 0.0

    print(f"\nAverage correlation (valid metrics only): {average_corr:.3f}")


