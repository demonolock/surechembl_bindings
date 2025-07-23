import duckdb

db_path = '/home/vshepard/hackaton_life/surecheml_db.duckdb'

con = duckdb.connect(database=db_path, read_only=True)

query = "SELECT inchi_key FROM compounds;"
result = con.execute(query).fetchdf()

