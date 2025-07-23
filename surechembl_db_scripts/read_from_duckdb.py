import duckdb

db_path = '/home/vshepard/hackaton_life/surecheml_db.duckdb'

con = duckdb.connect(database=db_path, read_only=True)

query = """
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
          p.patent_number
      FROM pharma_ids pid
      JOIN patents p ON p.id = pid.id and p.publication_date < '2023-01-01' and p.publication_date >= '2022-01-01'
      JOIN patent_compound_map pcm ON pcm.patent_id = p.id
      JOIN compounds c ON c.id = pcm.compound_id AND c.smiles != 'N'
      JOIN fields f ON f.id = pcm.field_id and f.fieldname = 'desc'
  )
  TO '/home/vshepard/hackaton_life/pharma_patents_numbers_2022.csv'
  WITH (
    FORMAT      CSV,        -- change from PARQUET → CSV
    HEADER      TRUE,       -- include column names in the first row
    DELIMITER   ',');
  """
result = con.execute(query).fetchdf()