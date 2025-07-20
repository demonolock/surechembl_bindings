from patent_filter import patent_filter

from patent_parser import fetch_patent_description
from get_patents import get_patents_ids


def main():
    all_patent_numbers = get_patents_ids('data/patent_ids_dummy.txt')
    unfiltered_patents = get_patents_ids('out/patent_ids_unfiltered.txt')

    curr_patents_numbers = all_patent_numbers - unfiltered_patents

    for patent_number in curr_patents_numbers:
        print(f'Start {patent_number}')
        descr = fetch_patent_description(patent_number)
        if not descr:
            print(f'Not get {patent_number}')
            with open('out/patent_ids_error.txt', 'a') as f:
                f.write(patent_number + '\n')
        elif patent_filter(descr):
            print(f'Write {patent_number}')
            with open('out/patent_ids_filtered.txt', 'a') as f:
                f.write(patent_number + '\n')
            with open(f'/home/chebykin/patents/{patent_number}', 'w') as f:
                f.write(descr)
        else:
            print(f'Unfilter {patent_number}')
            with open('out/patent_ids_unfiltered.txt', 'a') as f:
                f.write(patent_number + '\n')

main()