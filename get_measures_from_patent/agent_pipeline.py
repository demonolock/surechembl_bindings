import json
import os
import time
import argparse
import logging
import concurrent.futures

from alias_to_name.pipeline import filter_and_convert_molecula_alias_to_name
from .llm_patent_agents.patent_processor import process_patent_text
from filter.src.patent_parser import fetch_patent_description
from filter.src.get_patents import get_patents_ids

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_single_patent(patent_number, output_dir, timeout=40):
    """Обрабатывает один патент: скачивает и извлекает данные."""
    try:
        logging.info(f'Начинаю обработку патента: {patent_number}')
        patent_text = None
        start_time = time.time()

        # Попытка скачать текст патента
        while not patent_text and time.time() - start_time < timeout:
            patent_text = fetch_patent_description(patent_number)
            if not patent_text:
                time.sleep(4)

        if not patent_text:
            logging.warning(f'Не удалось скачать патент {patent_number} за {timeout} секунд.')
            with open('patent_ids_download_error.txt', 'a') as f:
                f.write(patent_number + '\n')
            return

        logging.info(f'Патент {patent_number} успешно скачан.')
        # Обработка текста и извлечение данных
        extracted_data = process_patent_text(
            patent_text=patent_text['content'],
            associated_molecules=[],
            patent_id=patent_number,
            debug=True,
            debug_output_dir=output_dir
        )

        # Сохранение результата
        if extracted_data:
            debug_dir = os.path.join(output_dir, patent_number)
            os.makedirs(debug_dir, exist_ok=True)
            replaced_extracted_data = filter_and_convert_molecula_alias_to_name(patent_text, patent_number, extracted_data)
            final_output_path = os.path.join(debug_dir, "03_final_output.json")
            with open(final_output_path, "w", encoding="utf-8") as f:
                json.dump(replaced_extracted_data, f, indent=4, ensure_ascii=False)
            logging.info(f"Сохранен результат для {patent_number}: {len(replaced_extracted_data)} записей.")
        else:
            logging.info(f"Для патента {patent_number} не найдено данных.")

    except Exception as e:
        logging.error(f'Произошла ошибка при обработке патента {patent_number}: {e}', exc_info=True)
        with open('patent_ids_processing_error.txt', 'a') as f:
            f.write(patent_number + '\n')

def main():
    """Основная функция для запуска пайплайна обработки патентов."""
    parser = argparse.ArgumentParser(description="Пайплайн для извлечения данных из патентов.")
    parser.add_argument(
        "input_file",
        type=str,
        help="Путь к текстовому файлу со списком ID патентов."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Количество параллельных потоков для обработки патентов."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=40,
        help="Таймаут в секундах для скачивания одного патента."
    )
    args = parser.parse_args()

    patent_numbers = get_patents_ids(args.input_file)
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_output_1")

    logging.info(f"Начинаю обработку {len(patent_numbers)} патентов с {args.workers} воркерами.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Передаем каждому воркеру функцию и ее аргументы
        future_to_patent = {executor.submit(process_single_patent, pn, output_dir, args.timeout): pn for pn in patent_numbers}

        # Обрабатываем результаты по мере их завершения
        for future in concurrent.futures.as_completed(future_to_patent):
            patent_number = future_to_patent[future]
            try:
                future.result()  # Проверяем на наличие исключений во время выполнения
            except Exception as exc:
                logging.error(f'{patent_number} сгенерировал исключение: {exc}')

    logging.info("Обработка всех патентов завершена.")

if __name__ == "__main__":
    main()
