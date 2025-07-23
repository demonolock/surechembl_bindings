## Module for comparison with BindingDB

For full BindingDB data (250 Mb), download from:
https://drive.google.com/drive/folders/1Z529rdYFcV66CNhXkupaYCGGok_3MKRr

### Overview
The bindingdb module is designed to prepare and enrich chemical and biological data for comparison with the BindingDB database. It processes molecular and protein information, standardizes representations, and generates output files that can be directly compared to BindingDB's reference data. The module also provides scripts for updating, validating, and analyzing the processed data.


## Directory Structure and File Descriptions
- `BindingDB_singlechain_short.csv` - A smaller, sample version of the BindingDB dataset for quick testing and development.
- `check_bdb_upd.py` - Script for evaluating and validating test data against the BindingDB dataset. Includes molecule standardization and filtering by molecular representation (SMILES or InChI Key).

Folder `enrich_data/`

- `add_inchi_key_and_sequence.py` - Enriches normalized data with InChI Keys (using PubChem and SureChEMBL APIs) and protein sequences (using UniProt). Uses caching to avoid redundant API calls.
- `json_to_bindingdb.py` - Converts enriched JSON data into a CSV format compatible with BindingDB, mapping binding metrics (Ki, IC50, Kd, EC50) to the appropriate columns.

Folder `enrich_data/input/`
- `analyze_final.ipynb` - Jupyter notebook for analyzing and filtering the input data, e.g., checking for missing values or strange units.

Folder `enrich_data/output/`
- `bindb.csv` - The main output CSV file, formatted for comparison with BindingDB. Contains enriched and standardized data.
- `inchi_key_cache.db` - Cache file for InChI Key lookups to speed up repeated runs. We need it because websites are unstable.
- `sequence_cache.db` Cache file for protein sequence lookups.
- `compare_with_bindb.ipynb` - Jupyter notebook for comparing the generated output with BindingDB data.
