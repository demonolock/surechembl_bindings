import argparse

from common_utils.get_patents import get_patents_ids
from downloader.src.__main__ import download


def main():
    parser = argparse.ArgumentParser(description="Пайплайн для скачивания патентов.")
    parser.add_argument(
        "--input_file", type=str, help="Путь к текстовому файлу со списком ID патентов."
    )
    parser.add_argument(
        "--input_dir", type=str, help="Путь к файлам patent_ids_{type}.txt от предыдущего запуска.",
        default=""
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Путь к директории, куда будут скачиваться патентамы.",
    )
    args = parser.parse_args()

    patent_numbers = get_patents_ids(args.input_file)
    download(patent_numbers, args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()