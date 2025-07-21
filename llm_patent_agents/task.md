# Итеративная Разработка Агента-Искателя

**Твоя роль:** Ты — AI-инженер. Твоя задача — пошагово создать Python-модуль для извлечения данных из патентов. Мы сосредоточимся исключительно на **Агенте-Искателе (Extractor Agent)**. QA и Mapper агенты будут добавлены позже. Ключевые требования — надежность, возможность отладки и подготовка к будущей интеграции.

## Обоснование Ключевых Архитектурных Решений

Прежде чем приступить к коду, пойми **почему** мы строим систему именно так. Это поможет тебе генерировать более качественный и осмысленный код.

1.  **Модульная и Изолированная Архитектура:**
    *   **Решение:** Весь код, отвечающий за работу агентов, инкапсулирован в одном файле (`patent_processor.py`) и предоставляет единственную публичную функцию (`process_patent_text`).
    *   **Обоснование:** Это критически важно для интеграции. Другие члены команды не должны знать о внутренней "магии" ваших агентов, о нарезке на куски или о промптах. Они будут вызывать твой код как "черный ящик": подали на вход текст патента и список молекул, получили на выходе готовый JSON. Это делает систему гибкой, а ваш модуль — легко заменяемым и тестируемым. `run_tests.py` выступает в роли первого "клиента" этого модуля.

2.  **Пайплайн-Воронка для Эффективности:**
    *   **Решение:** Применяем многоступенчатую фильтрацию в Python-коде (`_get_relevant_chunks`), чтобы отсеивать нерелевантные куски текста *до* отправки в LLM.
    *   **Обоснование:** Это решает техническую проблему (обход лимита токенов) и экономическую (минимизация затрат). Мы используем дешевые вычисления для тяжелой работы, а дорогие (LLM) — для тонкой.

3.  **Двухэтапный Агент-Искатель:**
    *   **Решение:** Агент сначала находит сырые упоминания (`FIND` шаг), а затем форматирует их в JSON (`FORMAT` шаг).
    *   **Обоснование:** Это декомпозирует задачу для LLM, что часто повышает точность. Модель сначала фокусируется на поиске, а затем — на структурировании, что снижает когнитивную нагрузку и количество ошибок.

4.  **Надежность и Устойчивость к Ошибкам:**
    *   **Решение:** Внедряем явную обработку сетевых ошибок с логикой повторных запросов (retry) и механизм "самоисправления" для невалидного JSON.
    *   **Обоснование:** Внешние API — ненадежны. LLM — недетерминированы. Система должна быть спроектирована так, чтобы выдерживать эти проблемы, а не падать при первой же ошибке.

5.  **Режим Отладки (Debug Mode):**
    *   **Решение:** Главная функция имеет флаг `debug`, который при активации сохраняет все промежуточные результаты (куски, сырые извлечения, ответы LLM) в отдельную папку.
    *   **Обоснование:** Это делает процесс прозрачным и превращает отладку из часов гадания в минуты анализа лог-файлов.

---

## Итеративный План Разработки

### Итерация 1: Базовый Каркас и API-вызов

**Цель:** Создать минимально работающий каркас, который может отправить один запрос к LLM и получить ответ.

1.  **Создай структуру проекта и файлы:**
    *   Папки: `llm-patent-agents/`, `tests/`, `tests/patents/`, `tests/answers/`, `debug_output/`.
    *   Пустые файлы: `config.py`, `patent_processor.py`, `run_tests.py`, `requirements.txt`.
    *   В `tests/patents/` положи файл `patent1.txt`. В `tests/answers/` создай пустой `answer1.json`.

2.  **Заполни `requirements.txt`:**
    ```
    openai
    pandas
    tqdm
    thefuzz
    python-Levenshtein
    ```

3.  **В файле `config.py` определи базовые константы и промпты:**
    ```python
    # config.py
    import os

    # --- API and Directory Configuration ---
    API_BASE_URL = "http://80.209.242.40:8000/v1"
    API_KEY = "dummy-key"
    MODEL_NAME = "llama-3.3-70b-instruct"
    TEMPERATURE = 0.0
    MAX_TOKENS_RESPONSE = 4096
    DEBUG_OUTPUT_DIR = "debug_output"

    # --- Error Handling Configuration ---
    API_RETRY_ATTEMPTS = 3
    API_RETRY_DELAY = 5  # seconds
    
    # --- Chunking and Pre-filtering Configuration ---
    METRIC_REGEX_PATTERN = r'\b(IC50|Ki|KB|EC50|Kd|inhibition|binding assay)\b'
    NEGATIVE_KEYWORDS_REGEX = r'\b(cytotoxicity|cell viability|cell growth|platelet count|viability assay|cytotoxic)\b'
    CHUNK_CONTEXT_SIZE = 1500
    CHUNK_OVERLAP = 300

    # --- Prompt Templates (in English) ---
    EXTRACTOR_FIND_PROMPT = """
    You are a research assistant. Your task is to identify and list all sentences or table rows from the provided text that appear to contain bioactivity data (IC50, Ki, KB, Kd, EC50) AND information about the protein target, such as its name, a UniProt ID, or a SEQ ID NO.
    Return ONLY the raw sentences/lines, one per line.

    --- Text Snippet to Analyze ---
    {text_chunk}
    ---
    """

    EXTRACTOR_FORMAT_PROMPT = """
    You are a data formatting specialist. Based on the list of raw sentences/lines provided below, convert each finding into a structured JSON object. The final output must be a single JSON list `[]`.

    Rules:
    1. Extract data EXACTLY as it is written. Do not change or normalize values.
    2. For the 'value' field, if the text contains an operator like '<10' or '>1000', extract it as a string, e.g., "<10".
    3. For "protein_target_name", include any context that might indicate a complex (e.g., "EGFR/ErbB2 dimer").
    4. For "molecule_context", extract the sentence describing the synthesis or structure of the molecule if it's near the activity data. This is crucial for mapping to a SMILES string later.

    JSON format for each object:
    {
        "molecule_name": "name or ID of the molecule, e.g., Example 5",
        "molecule_context": "sentence describing the molecule's synthesis or structure, if available, else null",
        "protein_target_name": "the name of the target protein as mentioned in the text",
        "protein_uniprot_id": "UniProt ID if available, else null",
        "protein_seq_id": "SEQ ID NO if available, else null",
        "binding_metric": "the metric type like IC50, Ki, KB, Kd, EC50",
        "value": "the numeric value as a string",
        "unit": "nM, uM, pM, or %"
    }

    --- Raw Sentences/Lines to Format ---
    {raw_mentions}
    ---
    """

    JSON_CORRECTION_PROMPT = """
    The following text is not a valid JSON. It has syntax errors.
    Please correct the text so it becomes a valid JSON list `[]` of objects, without changing the data content.
    Return ONLY the corrected, valid JSON.

    --- Invalid Text ---
    {invalid_json_text}
    ---
    """
    ```

4.  **В файле `patent_processor.py` создай базовую логику:**
    *   Импорты: `openai`, `json`, `time`, `logging`, `config`.
    *   Настрой простой логгер.
    *   Создай функцию `_call_llm(prompt: str) -> str | None`. Она должна инициализировать клиент `OpenAI` и сделать один API-вызов в блоке `try-except`.
    *   Создай класс `_ExtractorAgent`. Реализуй метод `run(self, text_chunk: str) -> list[dict]`. Пока что он будет одноэтапным: сразу вызывать `_call_llm` с `EXTRACTOR_FORMAT_PROMPT`.
    *   Создай пустую главную функцию: `def process_patent_text(...): pass`.

5.  **В файле `run_tests.py` напиши простой скрипт для запуска:**
    *   Прочитай `patent1.txt`, возьми первые 3000 символов.
    *   Импортируй `_ExtractorAgent` из `patent_processor` (временно, для теста).
    *   Создай экземпляр агента и вызови его метод `run()`.
    *   Распечатай результат в консоль.

---

### Итерация 2: Реализация "Воронки" — Нарезка и Предварительная Фильтрация

**Цель:** Научить модуль обрабатывать полный текст патента, эффективно отсеивая шум.

1.  **В файле `patent_processor.py` реализуй функцию нарезки:**
    *   Создай функцию `_get_relevant_chunks(text: str) -> list[str]`.
    *   **Логика:**
        1.  Используй `re.finditer` и `config.METRIC_REGEX_PATTERN` для поиска всех позиций метрик.
        2.  Создай интервалы с учетом `config.CHUNK_CONTEXT_SIZE` и `config.CHUNK_OVERLAP`.
        3.  Объедини пересекающиеся интервалы.
        4.  Извлеки текст для каждого итогового интервала.
        5.  Примени негативный фильтр с `config.NEGATIVE_KEYWORDS_REGEX`.
        6.  Верни финальный список отфильтрованных кусков.

2.  **Обнови главную функцию `process_patent_text`:**
    *   **Сигнатура:** `def process_patent_text(patent_text: str, associated_molecules: list[dict], patent_id: str, debug: bool = False) -> list[dict]:`
    *   **Логика:**
        1.  Вызови `_get_relevant_chunks(patent_text)`.
        2.  Если `debug=True`, создай папку `debug_output/{patent_id}` и сохрани куски в `01_chunks.json`.
        3.  Создай экземпляр `_ExtractorAgent`.
        4.  Создай пустой список `all_extracted_data = []`.
        5.  В цикле (`tqdm`) пройди по каждому куску, вызови `agent.run(chunk)` и добавь результат в `all_extracted_data`.
        6.  Верни `all_extracted_data`.

3.  **Обнови `run_tests.py`:**
    *   Теперь он должен читать **весь** текст `patent1.txt`.
    *   Вызывать `process_patent_text(patent_text, [], patent_id="patent1", debug=True)`.
    *   Распечатать итоговый результат и проверить наличие файлов в `debug_output`.

---

### Итерация 3: Повышение Надежности и Внедрение Двухэтапности

**Цель:** Сделать агент устойчивым к ошибкам и реализовать двухэтапный процесс извлечения.

1.  **В файле `patent_processor.py` обнови `_call_llm`:**
    *   Добавь цикл `for _ in range(config.API_RETRY_ATTEMPTS):` с `time.sleep(config.API_RETRY_DELAY)` для обработки сетевых ошибок.

2.  **В файле `patent_processor.py` обнови `_ExtractorAgent.run()`:**
    *   **Реализуй двухэтапный процесс:**
        1.  **Шаг 1: Поиск.** Вызови `_call_llm` с `EXTRACTOR_FIND_PROMPT`. Получи `raw_mentions`.
        2.  **Шаг 2: Форматирование.** Если `raw_mentions`, вызови `_call_llm` с `EXTRACTOR_FORMAT_PROMPT`.
    *   **Реализуй самоисправление JSON:**
        *   В `try-except json.JSONDecodeError` после Шага 2:
            1.  Сформируй промпт `config.JSON_CORRECTION_PROMPT`.
            2.  Сделай еще один вызов `_call_llm`.
            3.  Снова попробуй распарсить JSON.

3.  **Обнови `process_patent_text` для отладки:**
    *   Если `debug=True`, добавь сохранение "сырых" упоминаний (`raw_mentions`) и финального JSON от агента в папку отладки (`02_extractor_outputs.jsonl`).

