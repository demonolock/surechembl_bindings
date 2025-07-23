import argparse
import json
import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

from common_utils.get_patents import get_patents_ids
from common_utils.patent_parser import fetch_patent_description
from patent_filter import patent_filter

IDS_UNFILTERED_FILE = "patent_ids_unfiltered.txt"
IDS_FILTERED_FILE = "patent_ids_unfiltered.txt"
IDS_ERROR_DOWNLOAD_FILE = "patent_ids_error.txt"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def download(patent_numbers: set[str], output_dir: str) -> None:
    unfiltered_patents_file = os.path.join(output_dir, IDS_UNFILTERED_FILE)
    filtered_patents_file = os.path.join(output_dir, IDS_FILTERED_FILE)
    error_patents_file = os.path.join(output_dir, IDS_ERROR_DOWNLOAD_FILE)

    unfiltered_patents = get_patents_ids(unfiltered_patents_file)
    filtered_patents = get_patents_ids(filtered_patents_file)

    curr_patents_numbers = patent_numbers - unfiltered_patents - filtered_patents

    max_workers = 16  # Максимум CPU - то что вы используете (браузер, IDE). Я взяла половину от своих 16 CPU

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_patent = {
            executor.submit(fetch_patent_description, pn): pn
            for pn in curr_patents_numbers
        }
        for future in as_completed(future_to_patent):
            patent_number = future_to_patent[future]
            try:
                descr = future.result()
                if not descr:
                    logging.info(f"Not get {patent_number}")
                    with open(error_patents_file, "a") as f:
                        f.write(patent_number + "\n")
                elif patent_filter(descr):
                    logging.info(f"Filtered {patent_number}")
                    with open(filtered_patents_file, "a") as f:
                        f.write(patent_number + "\n")
                    with open(
                        os.path.join(output_dir, f"{patent_number}.json"), "w"
                    ) as f:
                        f.write(json.dumps(descr, ensure_ascii=False, indent=2))
                else:
                    logging.info(f"Unfiltered {patent_number}")
                    with open(unfiltered_patents_file, "a") as f:
                        f.write(patent_number + "\n")
            except Exception as e:
                logging.error(f"Error in future for {patent_number}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Пайплайн для скачивания патентов.")
    parser.add_argument(
        "--input_file", type=str, help="Путь к текстовому файлу со списком ID патентов."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Путь к директории, куда будут скачиваться патентамы.",
    )
    args = parser.parse_args()

    patent_numbers = get_patents_ids(args.input_file)
    download(patent_numbers, args.output_dir)


if __name__ == "__main__":
    main()
