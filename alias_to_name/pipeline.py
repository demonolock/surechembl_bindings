"""
1. Получаем из json patent_number и список имен молекул.
2. Составляем список алиасов. Это то что есть в molecula_name, но нет в annotation.
3. Ищем алиасы по тексту патента. Просим LLM понять что это значит.
"""
import json
import os

from alias_to_name.utils import fetch_patent, split_text_with_overlap, ask_llm, get_alias_list, process_patent

dir_path = os.path.dirname(os.path.abspath(__file__))
measures_file = os.path.join(dir_path, "output/final_json.json")
patent_file = os.path.join(dir_path, "data/json/patent_EP-3068388-A2.json")

with open(measures_file, "r", encoding="utf‑8") as f:
    measures = json.load(f)

patent_numbers = set([measure['patent_number'] for measure in measures if 'patent_number' in measure])
# Если сайт не грузит, читаю с файла
# with open(patent_file, "r", encoding="utf‑8") as f:
#     patent_data = json.load(f)

SYSTEM_PROMPT = """
You are a chemistry nomenclature expert.
Task: For each alias below, return the most common name of the molecule it refers to.
If an alias is unknown or maps to multiple molecules, output “Not found”.
"""
USER_PROMPT = """
Alias list start:
{alias_list}

Text:
{patent_text}

Return only in format "alias, molecula_name" and nothing more
"""

for patent_number in patent_numbers:
    try:
        patent_data = fetch_patent(patent_number)
        filtered_measures = [measure for measure in measures if measure['patent_number'] == patent_number]
        content, aliases = get_alias_list(patent_data, filtered_measures)

        result = process_patent(SYSTEM_PROMPT, USER_PROMPT, patent_number, measures)
        if result and len(result) > 0:
            print(result)
    except Exception as err:
        print(f"skip {patent_number}")

print()