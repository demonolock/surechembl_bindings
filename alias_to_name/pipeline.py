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
output_file = os.path.join(dir_path, "output/output_replaced")

print(measures_file)
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
Alias list end

Text:
{patent_text}

Return only in format "alias;; molecula_name" and nothing more
"""

# patent_numbers = ['EP-2566876-A1']
for patent_number in patent_numbers:
    try:
        print(patent_number)
        patent_data = fetch_patent(patent_number)
        filtered_measures = [measure for measure in measures if isinstance(measure, dict) \
                             and measure['patent_number'] == patent_number \
                             and isinstance(measure['molecule_name'], str) \
                             and isinstance(measure['protein_target_name'], str)
                             and isinstance(measure['binding_metric'], str)]
        if not filtered_measures:
            continue
        content, aliases = get_alias_list(patent_data, filtered_measures)

        print("aliases")
        print(aliases)
        alias_value_ans = {}
        if aliases:
            result, alias_value_ans = process_patent(SYSTEM_PROMPT, USER_PROMPT, content, aliases)
            if result and len(result) > 0:
                print(result)
                print(alias_value_ans)
        replaced_measured = []
        for measure in filtered_measures:
            if alias_value_ans.get(measure['molecule_name'], None) is not None:
                measure['molecule_name'] = alias_value_ans.get(measure['molecule_name'])
                replaced_measured.append(measure)
            with open(output_file + '/' + patent_number, 'w') as f:
                json.dump(measure, f)
    except Exception as err:
        print(f"skip {patent_number}")
        print(err)

print()