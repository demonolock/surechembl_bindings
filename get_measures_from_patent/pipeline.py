import argparse
import concurrent.futures
import json
import logging
import os
import time

from alias_to_name.config import ConfigAliasLLM
from alias_to_name.pipeline import filter_and_convert_molecula_alias_to_name
from common_utils.get_patents import get_patents_ids
from common_utils.patent_parser import fetch_patent_description
from get_measures_from_patent.config import ConfigMeasuresLLM
from llm_patent_agents.patent_processor import process_patent_text

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def process_single_patent(
    patent_number: str, output_dir: str, timeout: int = 40, cache_dir: str | None = None
) -> None:
    """Обрабатывает один патент: либо скачивает, либо берет из кэша, извлекает данные."""
    try:
        logging.info(f"Начинаю обработку патента: {patent_number}")
        patent_text = None

        if cache_dir:
            file_path = os.path.join(cache_dir, f"{patent_number}.json")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    patent_text = json.load(f)
            else:
                logging.warning(f"Файл кэша {file_path} не найден.")
        else:
            start_time = time.time()

            # Попытка скачать текст патента
            while not patent_text and time.time() - start_time < timeout:
                patent_text = fetch_patent_description(patent_number)
                if not patent_text:
                    time.sleep(4)

        if not patent_text:
            logging.warning(
                f"Не удалось скачать патент {patent_number} за {timeout} секунд."
            )
            with open("patent_ids_download_error.txt", "a") as f:
                f.write(patent_number + "\n")
            return

        logging.info(f"Патент {patent_number} успешно скачан.")

        # Обработка текста и извлечение данных
        extracted_data = process_patent_text(
            patent_text=patent_text["content"],
            associated_molecules=[],
            patent_id=patent_number,
            debug=True,
            debug_output_dir=output_dir,
            config=ConfigMeasuresLLM(),
        )

        # Сохранение результата
        if extracted_data:
            debug_dir = os.path.join(output_dir, patent_number)
            os.makedirs(debug_dir, exist_ok=True)
            final_output_path = os.path.join(debug_dir, "03_final_output.json")
            replaced_extracted_data = filter_and_convert_molecula_alias_to_name(
                patent_text, extracted_data, ConfigAliasLLM(), logging
            )
            with open(final_output_path, "w", encoding="utf-8") as f:
                json.dump(replaced_extracted_data, f, indent=4, ensure_ascii=False)
            logging.info(
                f"Сохранен результат для {patent_number}: {len(replaced_extracted_data )} записей."
            )
        else:
            logging.info(f"Для патента {patent_number} не найдено данных.")

    except Exception as e:
        logging.error(
            f"Произошла ошибка при обработке патента {patent_number}: {e}",
            exc_info=True,
        )
        with open("patent_ids_processing_error.txt", "a") as f:
            f.write(patent_number + "\n")


def main():
    """Основная функция для запуска пайплайна обработки патентов."""
    parser = argparse.ArgumentParser(
        description="Пайплайн для извлечения данных из патентов."
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default="",  # Не нужно если есть patent_dirs. Будут браться уже скаченные данные.
        help="Путь к текстовому файлу со списком ID патентов.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=16,
        help="Количество параллельных потоков для обработки патентов.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=40,
        help="Таймаут в секундах для скачивания одного патента.",
    )
    parser.add_argument(
        "--patent_dirs",
        type=str,
        help="Директория со скаченными патентами с помощью модуля downloader.",
    )
    parser.add_argument(
        "--output_dir", type=str, help="Директория для вывода результата."
    )
    args = parser.parse_args()

    if args.patent_dirs:
        logging.info(f"Обработка патентов из кэша в {args.patent_dirs}")
        files = [
            f
            for f in os.listdir(args.patent_dirs)
            if os.path.isfile(os.path.join(args.patent_dirs, f))
        ]
        logging.info(f"Найдено {len(files)} файлов для обработки.")

        # Extract patent numbers from file names (without extension)
        patent_numbers = [os.path.splitext(f)[0] for f in files]

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.workers
        ) as executor:
            future_to_patent = {
                executor.submit(
                    process_single_patent,
                    pn,
                    args.output_dir,
                    cache_dir=args.patent_dirs,
                ): pn
                for pn in patent_numbers
            }
            for future in concurrent.futures.as_completed(future_to_patent):
                patent_number = future_to_patent[future]
                try:
                    future.result()
                except Exception as exc:
                    logging.error(f"{patent_number} сгенерировал исключение: {exc}")
    else:
        patent_numbers = get_patents_ids(args.input_file)
        logging.info(
            f"Начинаю обработку {len(patent_numbers)} патентов с {args.workers} воркерами."
        )

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.workers
        ) as executor:
            # Передаем каждому воркеру функцию и ее аргументы
            future_to_patent = {
                executor.submit(
                    process_single_patent, pn, args.output_dir, timeout=args.timeout
                ): pn
                for pn in patent_numbers
            }

            # Обрабатываем результаты по мере их завершения
            for future in concurrent.futures.as_completed(future_to_patent):
                patent_number = future_to_patent[future]
                try:
                    future.result()  # Проверяем на наличие исключений во время выполнения
                except Exception as exc:
                    logging.error(f"{patent_number} сгенерировал исключение: {exc}")

        logging.info("Обработка всех патентов завершена.")


if __name__ == "__main__":
    main()
