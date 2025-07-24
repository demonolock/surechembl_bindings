import json
import os
import re
import math

# Шаг 2: Нормализация строки со значением (value)
def normalize_value(value_str):
    """
    Преобразует сложноформатированную строку `value` в единое числовое значение (float).
    Улучшенная версия для обработки сложных случаев.
    """
    if not isinstance(value_str, str):
        return None

    s = value_str.lower().strip()

    # 1. Предварительная очистка от текста и специальных символов
    s = re.sub(
        r"\b(about|approx\.?|at least|or less|or greater|or higher|or more)\b", "", s
    )
    s = (
        s.replace(" ", "")
        .replace("x", "*")
        .replace("×", "*")
        .replace("~", "")
        .replace("−", "-")
    )
    s = s.replace("≦", "<=").replace("≧", ">=")
    s = s.replace(
        "*10-", "*10^-"
    )  # Стандартизация научной нотации для корректного парсинга

    # Обработка "between X and Y"
    if "between" in s and "and" in s:
        parts = s.split("and")
        if len(parts) == 2:
            s = parts[0]  # Берем первое, меньшее значение

    # 2. Обработка "±" - берем значение до знака
    if "±" in s or "+-" in s or "-+" in s:
        s = re.split(r"±|\+-|-\+", s)[0]

    # 3. Обработка научной нотации (ПРИОРИТЕТ)
    match = re.search(r"(\d*\.?\d*)\*?10\^\{?(-?\d+)\}?", s)
    if match:
        try:
            base = float(match.group(1)) if match.group(1) else 1.0
            exponent = int(match.group(2))
            return base * (10 ** exponent)
        except OverflowError:
            return None  # Слишком большое число

    if "e" in s and not re.search(r"\d-e", s):  # Проверяем, что это не часть диапазона
        try:
            return float(s)
        except ValueError:
            pass

    # 4. Обработка диапазонов "to", "-", "and" (ПОСЛЕ научной нотации)
    range_parts = []
    if "to" in s:
        range_parts = s.split("to")
    elif "-" in s:
        # Проверяем, что дефис не является частью числа (например, в научной нотации)
        if not re.search(r"e-", s):
            range_parts = s.split("-")
    elif "and" in s:
        range_parts = s.split("and")

    if len(range_parts) == 2:
        try:
            # Очищаем первую часть от всего, кроме цифр и точки
            lower_bound_str = re.sub(r"[^0-9.]", "", range_parts[0])
            return float(lower_bound_str)
        except (ValueError, IndexError):
            pass  # Если не удалось, пробуем другие методы

    # 5. Удаляем операторы сравнения и запятые-разделители
    s = re.sub(r"[<>=]", "", s)
    s = s.replace(",", "")

    # 6. Финальная попытка прямого преобразования
    try:
        # Очищаем от оставшихся нечисловых символов
        final_str = re.sub(r"[^0-9.]", "", s)
        if final_str:
            return float(final_str)
    except ValueError:
        return None

    return None


# Шаг 4: Нормализация названия метрики (binding_metric)
def normalize_metric_name(metric_str):
    """
    Приводит все варианты написания метрик к одному из четырех стандартных видов,
    используя регулярные выражения для большей гибкости.
    """
    if not isinstance(metric_str, str):
        return None

    s = metric_str.lower().strip().replace("₅₀", "50")

    # Словарь: {регулярное выражение: стандартное имя}
    metric_patterns = {
        r"^(p|log)?\s*ic\s*[-]?\s*50": "IC50",
        r"^(p|log)?\s*ki": "Ki",
        r"^(p|log)?\s*kd": "Kd",
        r"^(p|log)?\s*ec\s*[-]?\s*50": "EC50",
    }

    for pattern, name in metric_patterns.items():
        if re.search(pattern, s):
            return name

    return None


# Шаг 5 (часть): Нормализация единиц измерения (unit) для линейных метрик
def normalize_unit_name(unit_str):
    """
    Приводит все варианты написания unit к стандартному виду,
    используя регулярные выражения.
    """
    if not isinstance(unit_str, str):
        return None

    s = unit_str.lower().strip()

    # Словарь: {регулярное выражение: стандартное имя}
    unit_patterns = {
        r"^nano\s*molar$|^nm$": "nM",
        r"^micro\s*molar$|^[uμµ]m$": "uM",
        r"^milli\s*molar$|^mm$": "mM",
        r"^pico\s*molar$|^pm$": "pM",
        r"^molar$|^m$": "M",
    }

    for pattern, name in unit_patterns.items():
        if re.search(pattern, s):
            return name

    return None


def process_row(row):
    """
    Обрабатывает одну строку данных в соответствии с планом.
    """
    if not isinstance(row, dict):
        return None

    original_metric = row.get("binding_metric")
    original_value_str = row.get("value")
    original_unit = row.get("unit")

    # Шаг 3: Определение типа метрики (логарифмическая или линейная)
    is_logarithmic = False
    if isinstance(original_metric, str):
        metric_lower = original_metric.lower()
        if metric_lower.startswith("p") or metric_lower.startswith("log"):
            is_logarithmic = True
    if isinstance(original_value_str, str) and "log" in original_value_str.lower():
        is_logarithmic = True

    # Шаг 2: Нормализация значения
    value_float = normalize_value(original_value_str)
    if value_float is None:
        return None

    # Шаг 4: Нормализация названия метрики
    metric_name = normalize_metric_name(original_metric)
    if metric_name is None:
        return None

    # Шаг 5: Финальная обработка и конвертация
    final_value = None
    final_unit = "nM"

    if is_logarithmic:
        # Применяем формулу для логарифмических значений
        final_value = (10 ** -value_float) * 1e9
    else:
        # Обработка линейных значений
        unit_name = normalize_unit_name(original_unit)
        if unit_name is None:
            return None  # Фильтруем, если unit не поддерживается

        conversion_factors = {
            "nM": 1,
            "uM": 1000,
            "mM": 1000000,
            "pM": 0.001,
            "M": 1000000000,
        }
        multiplier = conversion_factors[unit_name]
        final_value = value_float * multiplier

    # Шаг 6: Фильтрация по диапазону реалистичных значений
    if final_value is None or not (0.001 <= final_value <= 100000):
        return None

    # Обновляем исходную строку, сохраняя все остальные поля
    row["binding_metric"] = metric_name
    row["value"] = final_value
    row["unit"] = final_unit

    # Фильтруем строки, если какие-то из ключевых полей отсутствуют
    essential_keys = ["molecule_name", "protein_target_name", "patent_number"]
    if any(row.get(key) is None for key in essential_keys):
        return None

    return row


def normalize_data(data):
    """
    Принимает список словарей (сырые данные) и возвращает
    очищенный и отфильтрованный список словарей.
    """
    normalized_data = []
    for row in data:
        processed = process_row(row)
        if processed:
            normalized_data.append(processed)
    return normalized_data


def main():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(dir_path, "/home/vshepard/hackaton_life/final_final/final_old_23_07.json")
    output_file = os.path.join(dir_path, "output/final_normalized_data.json")

    os.makedirs(os.path.join(dir_path, "output"), exist_ok=True)

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            input_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading input file: {e}")
        return

    # Используем новую функцию для обработки данных
    final_data = normalize_data(input_data)

    print(f"Total rows processed: {len(input_data)}")
    print(f"Total rows after normalization and filtering: {len(final_data)}")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

    print(f"Normalized data saved to {output_file}")


if __name__ == "__main__":
    main()
