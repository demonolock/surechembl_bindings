import duckdb

file = "/home/vshepard/hackaton_life/pharma_patents_cut.parquet"

# 1. Get all unique patent numbers (already deduplicated)
query = f"SELECT DISTINCT patent_number FROM '{file}'"
rows = duckdb.query(query).fetchall()
patent_numbers = [row[0] for row in rows]

with open("/home/vshepard/hackaton_life/test.txt", 'w', encoding='utf-8') as file:
    for word in patent_numbers:
        file.write(word + '\n')