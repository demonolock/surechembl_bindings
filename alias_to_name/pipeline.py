"""
1. Получаем из json patent_number и список имен молекул.
2. Составляем список алиасов. Это то что есть в molecula_name, но нет в annotation.
3. Ищем алиасы по тексту патента. Просим LLM понять что это значит.
"""
import json
import os

from alias_to_name.web_utils import fetch_patent, split_text_with_overlap

from alias_to_name.utils import ask_llm

dir_path = os.path.dirname(os.path.abspath(__file__))
patent_number = "EP-3068388-A2"
measures_file = os.path.join(dir_path, "data/json/03_final_output.json")
patent_file = os.path.join(dir_path, "data/json/patent_EP-3068388-A2.json")

with open(measures_file, "r", encoding="utf‑8") as f:
    measures = json.load(f)

# Сайт не грузит, пока читаю с файла
# patent_data = fetch_patent(patent_number)
with open(patent_file, "r", encoding="utf‑8") as f:
    patent_data = json.load(f)

description = patent_data['data']['contents']['patentDocument']['descriptions'][0]['section']
content = description['content']
annotations = description['annotations']
chemicals = []
for a in annotations:
    if a['category'] == 'chemical' or a['category'] == 'target':
        chemicals.append(a['name'].lower().strip())

for measure in measures:
    aliases = []
    molecule_name = measure['molecule_name'].lower().strip()
    if molecule_name not in chemicals:
        aliases.append(measure['molecule_name'])




SYSTEM_PROMPT = """
You are a chemistry nomenclature expert.
Task: For each alias below, return the most common name of the molecule it refers to.
If an alias is unknown or maps to multiple molecules, output “Not found”.
Order matters – keep the answers in the same order as the aliases appear.
Output only the names (one per line, no bullets, no extra text).
"""
USER_PROMPT = """
Alias list start:
{alias_list}

Text:
{patent_text}
"""

for chunck_text in split_text_with_overlap(content):
    aliases_in_chunk = []
    message = [{"role": "system", "content": SYSTEM_PROMPT},
               {"role": "user",   "content": USER_PROMPT.format(alias_list=[])}]
    ask_llm(message=message)

print()