import argparse
import concurrent
import logging
import os

from common_utils.get_patents import get_patents_ids
from get_measures_from_patent.pipeline import process_single_patent


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