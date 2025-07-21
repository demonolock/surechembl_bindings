import json
import os
from llm_patent_agents.patent_processor import process_patent_text
from filter.src.patent_parser import fetch_patent_description
import time
from filter.src.get_patents import get_patents_ids


def main():
    patent_numbers = get_patents_ids('filter/src/out/patent_ids_filtered_1.txt')
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_output")

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