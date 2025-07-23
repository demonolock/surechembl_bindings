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
    s = re.sub(r"\b(about|approx\.?)\b", "", s)  # Удаляем "about", "approx"
    s = s.replace(" ", "").replace("x", "*").replace("×", "*").replace("~", "")
    s = s.replace("≦", "<=").replace("≧", ">=")  # Заменяем unicode символы

    # 2. Обработка "±" - берем значение до знака
    if "±" in s or "+-" in s or "-+" in s:
        s = re.split(r"±|\+-|-\+", s)[0]

    # 3. Обработка диапазонов "to" и "-" (берем верхнее значение)
    # Сначала очищаем от единиц измерения, чтобы не мешали
    range_parts = []
    if "to" in s:
        range_parts = s.split("to")
    elif "-" in s and "e-" not in s:
        range_parts = s.split("-")

    if len(range_parts) == 2:
        try:
            # Очищаем вторую часть от всего, кроме цифр и точки
            upper_bound_str = re.sub(r"[^0-9.]", "", range_parts[1])
            return float(upper_bound_str)
        except (ValueError, IndexError):
            pass  # Если не удалось, пробуем другие методы

    # 4. Удаляем операторы сравнения и запятые-разделители
    s = re.sub(r"[<>=]", "", s)
    s = s.replace(",", "")

    # 5. Обработка научной нотации
    match = re.search(r"(\d*\.?\d*)\*?10\^\{?(-?\d+)\}?", s)
    if match:
        try:
            base = float(match.group(1)) if match.group(1) else 1.0
            exponent = int(match.group(2))
            return base * (10 ** exponent)
        except OverflowError:
            return None  # Слишком большое число

    if "e" in s:
        try:
            return float(s)
        except ValueError:
            pass

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

        conversion_factors = {"nM": 1, "uM": 1000, "mM": 1000000, "pM": 0.001}
        multiplier = conversion_factors[unit_name]
        final_value = value_float * multiplier

    # Шаг 6: Фильтрация по диапазону реалистичных значений
    if final_value is None or not (0.001 <= final_value <= 100000):
        return None

    # Обновляем исходную строку, сохраняя все остальные поля
    row["binding_metric"] = metric_name
    row["value"] = final_value
    row["unit"] = final_unit

    # Шаг 7: Фильтрация по имени молекулы
    molecule_name = row.get("molecule_name")
    if molecule_name:
        name_lower = molecule_name.lower().strip()
        # Фильтр 1: Слишком короткие имена
        if len(name_lower) <= 2:
            return None
        # Фильтр 2: Общие имена с номерами (например, "Compound 2", "compounds of formula I")
        generic_pattern = r"^(compound|example|intermediate|formula|preparation|synthesis|product|molecule|agent|ligand|inhibitor|analog|derivative|substance|composition|material)s?\s+(?:of\s+formula\s+)?(?:no\.\s*)?(\d+|[ivxldcm]+).*"
        if re.match(generic_pattern, name_lower):
            return None

        # Фильтр 3: Слишком общие имена (например, "antibody")
        generic_names = {"antibody", "antibodies", "nanobody", "nanobodies"}
        if name_lower in generic_names:
            return None

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
    input_file = os.path.join(dir_path, "input/test_data.json")
    output_file = os.path.join(dir_path, "output/test_normalized_data.json")

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
