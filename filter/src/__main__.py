from patent_filter import patent_filter

from patent_parser import fetch_patent_description
from get_patents import get_patents_ids


def main():
    patent_numbers = get_patents_ids('data/patent_ids_dummy.txt')

    for patent_number in patent_numbers:
        descr = fetch_patent_description(patent_number)
        if patent_filter(descr):
            with open('out/patent_ids_filtered.txt', 'w') as f:
                f.write(patent_number)

main()