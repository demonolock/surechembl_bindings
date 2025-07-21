import json
import os

dir_path = os.path.dirname(os.path.abspath(__file__))
subpath = "../get_measures_from_patent/debug_output"
output_path = os.path.join(dir_path, "output", "final_json.json")
final = []
# All files recursively
for root, dirs, files in os.walk(os.path.join(dir_path, subpath)):
    for file in files:
        if file.endswith("outputs.jsonl"):
            # Add here reading of the file
            file_path = os.path.join(root, file)
            with open(file_path, 'r') as f:
                for line in f:
                    data = json.loads(line)
                    patent_number = root.split("/")[-1]
                    if 'final_json' in data:
                        for i, item in enumerate(data['final_json']):
                            item['patent_number'] = patent_number
                        final += data['final_json']

with open(output_path, 'w') as outfile:
    json.dump(final, outfile, indent=4, ensure_ascii=False)
