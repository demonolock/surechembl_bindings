import duckdb

file = "pharma_patents_numbers_2022.csv"

# 1. Get all unique patent numbers (already deduplicated)
query = f"SELECT DISTINCT patent_number FROM '{file}'"
rows = duckdb.query(query).fetchall()
patent_numbers = [row[0] for row in rows]

with open("ids.txt", "w", encoding="utf-8") as file:
    for word in patent_numbers:
        file.write(word + "\n")
