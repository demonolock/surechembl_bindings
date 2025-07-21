import duckdb

file = "/home/chebykin/hackaton/pharma_patents_cut.parquet"

# 1. Get all unique patent numbers (already deduplicated)
query = f"SELECT DISTINCT patent_number FROM '{file}' limit 100000"
rows = duckdb.query(query).fetchall()
patent_numbers = [row[0] for row in rows]

with open("/home/chebykin/hackaton/test.txt", 'w', encoding='utf-8') as file:
    for word in patent_numbers:
        file.write(word + '\n')