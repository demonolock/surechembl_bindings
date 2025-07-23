import duckdb

file = "pharma_patents_cut.parquet"

chunk_size = 2
offset = 0

while True:
    query = f"""
        SELECT patent_number, smiles, inchi_key
        FROM '{file}' AS pp
        order by patent_number, smiles
        limit {chunk_size} OFFSET {offset};
        """
    offset += chunk_size
    rows = duckdb.query(query).fetchall()
    if not rows:
        break
    for row in rows:
        print(f"patent_number: {row[0]}, smile: {row[1]}, inchi_key: {row[2]}")