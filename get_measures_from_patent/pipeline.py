import json
import os
from llm_patent_agents.patent_processor import process_patent_text
from filter.src.patent_parser import fetch_patent_description
import time
from filter.src.get_patents import get_patents_ids

from_cache = True
# Тут результат выгрузки filter/__main__.py
patent_dir = "/home/vshepard/hackaton_life/patents"

dir_path = os.path.dirname(os.path.abspath(__file__))
processed_patents_file = os.path.join(dir_path, 'output', 'processed_patents.json')
# Get processed patent_number list
if os.path.exists(processed_patents_file):
    with open(processed_patents_file, "r", encoding="utf-8") as f:
        try:
            processed_patents = set(json.load(f))
        except Exception:
            processed_patents = set()
else:
    processed_patents = set()

def save_processed_patents():
    with open(processed_patents_file, "w", encoding="utf-8") as f:
        json.dump(list(processed_patents), f, indent=2, ensure_ascii=False)

def process_description(patent_text, patent_number, output_dir):
    if patent_number in processed_patents:
        print(f"{patent_number} already processed, skipping.")
        return

    print(f'End download {patent_number}')
    extracted_data = process_patent_text(
        patent_text=patent_text,
        associated_molecules=[],
        patent_id=patent_number,
        debug=True,
        debug_output_dir=output_dir
    )

    # Save the final JSON output
    if extracted_data:
        debug_dir = os.path.join(output_dir, patent_number)
        os.makedirs(debug_dir, exist_ok=True)
        final_output_path = os.path.join(debug_dir, "03_final_output.json")
        with open(final_output_path, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, indent=4, ensure_ascii=False)
        print(f"- Saved final output to: {final_output_path}")

    # Print the final result
    res = json.dumps(extracted_data, indent=4)
    print("\n--- Final Extracted Data ---")
    print(res)
    print(f"\nTotal data points extracted: {len(extracted_data)}")

    # Mark this patent as processed, save immediately, and print confirmation
    processed_patents.add(patent_number)
    save_processed_patents()
    print(f"Patent {patent_number} added to {processed_patents_file} and saved.")

def main():
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_output")
    if from_cache:
        for filename in os.listdir(patent_dir):
            file_path = os.path.join(patent_dir, filename)
            if os.path.isfile(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    patent_text = f.read()
                patent_number = os.path.splitext(filename)[0]  # remove if there any file extension
                if not patent_text:
                    print(f'No data in {file_path}')
                    continue
                process_description(patent_text, patent_number, output_dir)
    else:
        patent_numbers = get_patents_ids('filter/src/out/patent_ids_filtered_1.txt')

        for patent_number in patent_numbers:
            print(f'Start {patent_number}')
            patent_text = None

            start_time = time.time()
            print(f'Start download {patent_number}')
            while not patent_text and time.time() - start_time < 40:
                patent_text = fetch_patent_description(patent_number)
                time.sleep(4)
            if patent_text:
                process_description(patent_text, patent_number, output_dir)
            else:
                print(f'FAILED download {patent_number} after 40 sec')
                with open('patent_ids_error.txt', 'a') as f:
                    f.write(patent_number + '\n')

main()