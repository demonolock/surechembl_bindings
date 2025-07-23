### Интеграция в пайплайн


```python
# В главном скрипте пайплайна
from data_normalization.normalize_data import normalize_data
from some_module import get_raw_data

# 1. Получить сырые данные с предыдущего шага
raw_data = get_raw_data() 

# 2. Вызвать функцию нормализации
cleaned_data = normalize_data(raw_data)

# 3. Передать очищенные данные на следующий этап
process_further(cleaned_data)
```
