import duckdb
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
from concurrent.futures import ProcessPoolExecutor, as_completed

file = "pharma_patents_cut.parquet"
output_csv = "patents_with_ic50_ki_ec50.csv"

# 1. Get all unique patent numbers (already deduplicated)
query = f"SELECT DISTINCT patent_number FROM '{file}'"
rows = duckdb.query(query).fetchall()
patent_numbers = [row[0] for row in rows]

def process_patent(patent_number):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    url = f"https://www.surechembl.org/patent/{patent_number}"
    found = False
    try:
        driver.get(url)
        time.sleep(6)  # Long enough for full page JS render (tune as needed)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Extract description
        description_section = None
        for el in soup.find_all(class_=lambda c: c and 'description' in c):
            sec = el.find(class_='section')
            if sec:
                description_section = sec.get_text(separator=" ", strip=True)
                break

        # Check for bioactivity keywords: ('Ki (nM)', 'IC50 (nM)', 'Kd (nM)', 'EC50 (nM)')
        if description_section and re.search(r'\b(IC50|Ki|EC50|Kd)\b', description_section, re.IGNORECASE):
            found = True
    except Exception as e:
        print(f"Error with patent {patent_number}: {e}")
    finally:
        driver.quit()
    if found:
        print(f"Found: {patent_number}")
        return patent_number
    else:
        return None

# 2. Multiprocessing (e.g., 4 workers -- adjust to your CPU/VM capability)
max_workers = 10  # Or more/less as you see fit

results = []
with ProcessPoolExecutor(max_workers=max_workers) as executor:
    future_to_patent = {executor.submit(process_patent, pn): pn for pn in patent_numbers}
    for future in as_completed(future_to_patent):
        pn = future_to_patent[future]
        try:
            result = future.result()
            if result is not None:
                results.append(result)
        except Exception as e:
            print(f"Error in future for {pn}: {e}")

# 3. Write results to CSV
with open(output_csv, mode="w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["patent_number"])
    for patent_number in results:
        writer.writerow([patent_number])

print(f"Done! Found {len(results)} hits. Results in {output_csv}")
