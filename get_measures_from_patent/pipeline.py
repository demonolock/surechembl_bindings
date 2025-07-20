import json
import time
from filter.src.get_patents import get_patents_ids
from llm_patent_agents.patent_processor import process_patent_text
from filter.src.patent_parser import fetch_patent_description


def main():
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
            print(f'End download {patent_number}')
            extracted_data = process_patent_text(
                patent_text=patent_text,
                associated_molecules=[],
                patent_id=patent_number,
                debug=True
            )

            # 3. Print the final result
            res = json.dumps(extracted_data, indent=4)
            print("\n--- Final Extracted Data ---")
            print(res)
            print(f"\nTotal data points extracted: {len(extracted_data)}")

        else:
            print(f'FAILED download {patent_number} after 40 sec')
            with open('patent_ids_error.txt', 'a') as f:
                f.write(patent_number + '\n')

main()