def get_patents_ids(file_path: str) -> set[str]:
    """
    Читает файл со словами (по одному слову на строку) и возвращает список слов.

    :param file_path: Путь к файлу со словами
    :return: Список слов из файла
    """
    word_list = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                word = line.strip()  # Удаляем пробелы и переносы строк
                if word:  # Добавляем только непустые строки
                    word_list.add(word)
        return word_list
    except FileNotFoundError:
        print(f"Ошибка: Файл '{file_path}' не найден.")
        return set()
    except Exception as e:
        print(f"Произошла ошибка при чтении файла: {e}")
        return set()