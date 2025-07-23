
Порядок запуска:

1. Поиск подходящих patent_number
filter/src/__main__.py
2. Извлекаем метрики из description патентов
get_measures_from_patent/pipeline.py
3. Заменяем алиасы на имена молекул
alias_to_name/pipeline.py
4. Добавляем в данные inchi_key и sequence по именам молекулы и таргета
bindingdb/enrich_data/add_inchi_key_and_sequence.py
5. Форматируем в вид пригодный для скрипта расчета корреляции
bindingdb/enrich_data/json_to_bindingdb.py



