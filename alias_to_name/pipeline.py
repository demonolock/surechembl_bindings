"""
1. Получаем из json patent_number и список имен молекул.
2. Составляем список алиасов. Это то что есть в molecula_name, но нет в annotation.
3. Ищем алиасы по тексту патента. Просим LLM понять что это значит.
"""
import argparse
import json
import logging

from alias_to_name.config import ConfigAliasLLM
from alias_to_name.utils import filter_and_convert_molecula_alias_to_name
from common_utils.patent_parser import fetch_patent_description

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    parser = argparse.ArgumentParser(
        description="Пайплайн для извлечения данных из патентов."
    )
    parser.add_argument(
        "input_file",
        type=str,
        default="",  # Не нужно если есть from_cache
        help="Путь к текстовому файлу со списком ID патентов.",
    )
    parser.add_argument(
        "output_file",
        type=str,
        default="",  # Не нужно если есть from_cache
        help="Путь к текстовому файлу со списком ID патентов.",
    )
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf‑8") as f:
        measures = json.load(f)

    patent_numbers = set(
        [measure["patent_number"] for measure in measures if "patent_number" in measure]
    )
    for patent_number in patent_numbers:
        try:
            logging.info(f"{patent_number} begin")
            patent = fetch_patent_description(patent_number)
            config = ConfigAliasLLM()
            measured = filter_and_convert_molecula_alias_to_name(
                patent, measures, config, logging
            )
            with open(args.output_file + "/" + patent_number, "w") as f:
                json.dump(measured, f)
        except Exception as err:
            logging.info(f"skip {patent_number}")
            logging.error(err)


if __name__ == "__main__":
    main()
