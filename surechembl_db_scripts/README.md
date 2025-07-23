# SureChEMBL Data Download and Processing Guide

This guide will help you download SureChEMBL bulk patent data, set up a local DuckDB database, and extract pharmaceutical patents for downstream analysis. All steps are written for Linux, but can be adapted for other platforms.

---

## 1. Download SureChEMBL Bulk Data

SureChEMBL provides a large collection of patent-compound data. Download the latest bulk data using:

```bash
wget -r -np -nH -e robots=off --cut-dirs=1 -P ./surechembl_data \
  https://ftp.ebi.ac.uk/pub/databases/chembl/SureChEMBL/bulk_data/
```

* All files will be saved under `./surechembl_data`.
* Official SureChEMBL update info: [SureChEMBL download instructions](https://chembl.blogspot.com/2025/05/download-surechembl-data-major-update.html)

---

## 2. Install DuckDB

DuckDB is a fast, easy-to-use analytical database for working with large datasets.

Install DuckDB via:

```bash
curl https://install.duckdb.org | sh
```

---

## 3. Create a DuckDB Database

Start DuckDB in your working directory:

```bash
duckdb surechembl_db.duckdb
```

This will open the DuckDB SQL prompt.

---

## 4. Load SureChEMBL Data Into DuckDB

Run the following SQL commands inside the DuckDB prompt, adjusting paths as needed:

```sql
create table compounds as select * from '/path/to/surechembl_data/compounds.parquet';
create table fields as select * from '/path/to/surechembl_data/fields.parquet';
create table patents as select * from '/path/to/surechembl_data/patents.parquet';
create table patent_compound_map as select * from '/path/to/surechembl_data/patent_compound_map.parquet';
```

* Replace `/path/to/surechembl_data/` with your actual local path (e.g., `/home/user/surechembl_data/databases/chembl/SureChEMBL/bulk_data/2025-07-15/`)

---

## 5. Extract Pharmaceutical Patents

To extract patents with pharmaceutical relevance (CPC/IPC classes A61K or A61P), run the following SQL query in DuckDB:

```sql
COPY (
  WITH pharma_cpc AS (
      SELECT DISTINCT id
      FROM patents, UNNEST(cpc) AS t(code)
      WHERE TRIM(code) LIKE 'A61K%' OR TRIM(code) LIKE 'A61P%'
  ),
  pharma_ipc AS (
      SELECT DISTINCT id
      FROM patents, UNNEST(ipc) AS t(code)
      WHERE TRIM(code) LIKE 'A61K%' OR TRIM(code) LIKE 'A61P%'
  ),
  pharma_ids AS (
      SELECT id FROM pharma_cpc
      UNION
      SELECT id FROM pharma_ipc
  )
  SELECT distinct
      p.patent_number,
      c.smiles,
      c.inchi_key
  FROM pharma_ids pid
  JOIN patents p ON p.id = pid.id
  JOIN patent_compound_map pcm ON pcm.patent_id = p.id
  JOIN compounds c ON c.id = pcm.compound_id AND c.smiles != 'N'
  JOIN fields f ON f.id = pcm.field_id and f.fieldname = 'desc'
)
TO '/path/to/output/pharma_patents_cut.parquet'
WITH (FORMAT PARQUET, CODEC 'ZSTD');
```

* Change `/path/to/output/pharma_patents_cut.parquet` to your desired output location.

---

## 6. (Optional) Restore ChEMBL PostgreSQL Database

ChEMBL also provides a PostgreSQL dump for relational querying. Example restore command:

```bash
{POSTGRES_BIN}/pg_restore  --no-owner -p port -U user -d chembl_35 chembl_35_postgresql.dmp
```

See [ChEMBL schema documentation](https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_35/schema_documentation.html) for database details.

---

## Notes

* Bulk SureChEMBL files can be large—ensure you have sufficient disk space.
* All SQL assumes you are running inside the DuckDB SQL prompt.
* You may need to adjust file paths to match your environment.
* Check the [SureChEMBL blog](https://chembl.blogspot.com/) for latest update info.
