Скачать файлы surechembl
wget -r -np -nH -e robots=off --cut-dirs=1 -P ./surechembl_data https://ftp.ebi.ac.uk/pub/databases/chembl/SureChEMBL/bulk_data/

https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_35/schema_documentation.html
/home/vshepard/pbckp/cfs_estimate_v3/bin/pg_restore --no-owner -p 47091 -U vshepard -d chembl_35 /home/vshepard/hackaton_life/surechembl_db/chembl_35_postgresql/chembl_35/chembl_35_postgresql/chembl_35_postgresql.dmp



1. Скачать базу Surechembl
https://chembl.blogspot.com/2025/05/download-surechembl-data-major-update.html
wget -r -np -nH -e robots=off --cut-dirs=1 -P ./surechembl_data https://ftp.ebi.ac.uk/pub/databases/chembl/SureChEMBL/bulk_data/

2. Установить duckdb
curl https://install.duckdb.org | sh

3. Создать базу
duckdb surecheml_db.duckdb

4. Загрузить данные
Внутри окна открывшегося предыдущей командой вводить

create table compounds as select * from "/home/vshepard/hackaton_life/data/databases/patents/databases/chembl/SureChEMBL/bulk_data/2025-07-15/compounds.parquet";
create table fields as select * from "/home/vshepard/hackaton_life/data/databases/patents/databases/chembl/SureChEMBL/bulk_data/2025-07-15/fields.parquet";
create table patents as select * from "/home/vshepard/hackaton_life/surechembl_data/databases/chembl/SureChEMBL/bulk_data/2025-07-15/patents.parquet";
create table patent_compound_map as select * from "/home/vshepard/hackaton_life/surechembl_data/databases/chembl/SureChEMBL/bulk_data/2025-07-15/patent_compound_map.parquet";


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
  TO '/home/vshepard/hackaton_life/pharma_patents_cut.parquet'
  WITH (FORMAT PARQUET, CODEC 'ZSTD');



Порядок запуска:

1. Поиск подходящих patent_number
filter/src/__main__.py
2. Извлекаем метрики из description патентов
get_measures_from_patent/pipeline.py
3. Заменяем алиасы на имена молекул
alias_to_name/pipeline.py
4. Добавляем в данные inchi_key и sequence по именам молекулы и таргета
bindingdb/enrich_data/add_inchi_key_and_compound.py
5. Форматируем в вид пригодный для скрипта расчета корреляции
bindingdb/enrich_data/json_to_bindingdb.py



