from concurrent.futures import ProcessPoolExecutor, as_completed

from patent_filter import patent_filter

from patent_parser import fetch_patent_description
from get_patents import get_patents_ids

patent_dirs = '/home/vshepard/hackaton_life/patents'
def main():
    all_patent_numbers = get_patents_ids('data/patent_ids_dummy.txt')
    unfiltered_patents = get_patents_ids('out/patent_ids_unfiltered.txt')
    filtered_patents = get_patents_ids('out/patent_ids_filtered.txt')

    curr_patents_numbers = all_patent_numbers - unfiltered_patents - filtered_patents

    max_workers = 16  # Максимум CPU - то что вы используете (браузер, IDE). Я взяла половину от своих 16 CPU

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_patent = {executor.submit(fetch_patent_description, pn): pn for pn in curr_patents_numbers}
        for future in as_completed(future_to_patent):
            patent_number = future_to_patent[future]
            try:
                descr = future.result()
                if not descr:
                    print(f'Not get {patent_number}')
                    with open('out/patent_ids_error.txt', 'a') as f:
                        f.write(patent_number + '\n')
                elif patent_filter(descr):
                    print(f'Write {patent_number}')
                    with open('out/patent_ids_filtered.txt', 'a') as f:
                        f.write(patent_number + '\n')
                    with open(f'{patent_dirs}/{patent_number}', 'w') as f:
                        f.write(descr)
                else:
                    print(f'Unfilter {patent_number}')
                    with open('out/patent_ids_unfiltered.txt', 'a') as f:
                        f.write(patent_number + '\n')
            except Exception as e:
                print(f"Error in future for {patent_number}: {e}")

main()