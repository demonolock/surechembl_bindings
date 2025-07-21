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

# patent_numbers = ['EP-2566876-A1']
for patent_number in patent_numbers:
    try:
        print(patent_number)
        patent_data = fetch_patent(patent_number)
        filtered_measures = [measure for measure in measures if measure['patent_number'] == patent_number]
        # filtered_measures = [{'molecule_name': 'sildenafil', 'protein_target_name': None, 'protein_uniprot_id': None, 'protein_seq_id': None, 'binding_metric': 'IC50', 'value': None, 'unit': None, 'patent_number': 'WO-2006023603-A2'}, {'molecule_name': 'sildenafil', 'protein_target_name': None, 'protein_uniprot_id': None, 'protein_seq_id': None, 'binding_metric': None, 'value': '10.4 ± 5.7', 'unit': 'nM', 'patent_number': 'WO-2006023603-A2'}, {'molecule_name': 'sildenafil', 'protein_target_name': 'PDE5 A', 'protein_uniprot_id': None, 'protein_seq_id': None, 'binding_metric': None, 'value': '-10', 'unit': 'nM', 'patent_number': 'WO-2006023603-A2'}, {'molecule_name': 'sildenafil', 'protein_target_name': None, 'protein_uniprot_id': None, 'protein_seq_id': None, 'binding_metric': None, 'value': '10', 'unit': 'nM', 'patent_number': 'WO-2006023603-A2'}, {'molecule_name': 'sildenafil', 'protein_target_name': None, 'protein_uniprot_id': None, 'protein_seq_id': None, 'binding_metric': 'IC50', 'value': '5-10', 'unit': 'nM', 'patent_number': 'WO-2006023603-A2'}, {'molecule_name': 'EMD 360527', 'protein_target_name': None, 'protein_uniprot_id': None, 'protein_seq_id': None, 'binding_metric': 'IC50', 'value': '1', 'unit': 'μM', 'patent_number': 'WO-2006023603-A2'}, {'molecule_name': 'compounds', 'protein_target_name': 'PDE5A', 'protein_uniprot_id': None, 'protein_seq_id': None, 'binding_metric': 'IC50', 'value': '-10', 'unit': 'nM', 'patent_number': 'WO-2006023603-A2'}, {'molecule_name': 'sildenafil', 'protein_target_name': 'PDE5A', 'protein_uniprot_id': None, 'protein_seq_id': None, 'binding_metric': None, 'value': '37±5.2', 'unit': 'nM', 'patent_number': 'WO-2006023603-A2'}, {'molecule_name': 'EMD-360527/5', 'protein_target_name': 'PDE5A', 'protein_uniprot_id': None, 'protein_seq_id': None, 'binding_metric': None, 'value': None, 'unit': None, 'patent_number': 'WO-2006023603-A2'}, {'molecule_name': 'compounds', 'protein_target_name': 'PDEl', 'protein_uniprot_id': None, 'protein_seq_id': None, 'binding_metric': 'IC50', 'value': '1-20', 'unit': 'μM', 'patent_number': 'WO-2006023603-A2'}, {'molecule_name': 'compounds', 'protein_target_name': 'PDE3', 'protein_uniprot_id': None, 'protein_seq_id': None, 'binding_metric': 'IC50', 'value': '1-20', 'unit': 'μM', 'patent_number': 'WO-2006023603-A2'}]
        content, aliases = get_alias_list(patent_data, filtered_measures)

        print("aliases")
        print(aliases)
        result, alias_value_ans = process_patent(SYSTEM_PROMPT, USER_PROMPT, content, aliases)
        if result and len(result) > 0:
            print(result)
            print(alias_value_ans)
    except Exception as err:
        print(f"skip {patent_number}")
        print(err)

print()