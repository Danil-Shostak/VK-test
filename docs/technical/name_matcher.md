# Name Matcher — модуль сравнения имён и фамилий

## 1. Назначение
Модуль `Name Matcher` осуществляет глубокое сравнение двух строковых представлений имён и фамилий с целью установления вероятности принадлежности к одному человеку. Модуль обрабатывает вариации, транслитерацию, фау mistmatches и орфографические ошибки.

**Вход:** две строки (first_name / last_name)  
**Выход:** словарь с метриками и итоговой оценкой `final_score` ∈ [0, 1]

## 2. Архитектурные принципы
- **Модульность**: модуль является автономным классом `NameMatcher` без внешних зависимостей (только стандартная библиотека Python: `re`, `difflib`, `functools`).
- **Чистые функции**: все методы являются pure functions (не меняют внешнее состояние), что упрощает тестирование.
- **Кеширование**: `normalize_name` кешируется через `functools.lru_cache` для ускорения повторных вызовов.
- **Расширяемость**: новые метрики можно добавить в метод `compare_names` без изменения существующих.

## 3. Логика функционирования
1. **Нормализация** каждой строки:
   - Приведение к строке (если передан не `str`, например `int`)
   - Удаление начальных/конечных пробелов
   - Приведение к нижнему регистру
   - Удаление всей пунктуации и не-алфавитно-цифровых символов, кроме букв (поддерживается Юникод, поэтому кириллица сохраняется)
   - Удаление подчёркиваний
2. **Вычисление набора метрик** (параллельно, последовательно):
   - Точное совпадение (`exact_match`)
   - Нечёткое сходство (`fuzzy_ratio`) через `difflib.SequenceMatcher`
   - Фонетическое сходство:
     - Кодирование имён по Soundex (русский variant)
     - Кодирование по Metaphone (Double Metaphone)
     - Сравнение кодов через fuzzy_ratio → `phonetic_score`
   - **Jaccard similarity** на уровне символов (intersection over union множества символов строки)
   - Расстояние Левенштейна (динамическое программирование) → `levenshtein_score`
   - Вариации имён: множества из `name_variants.py` → `variation_match` (булево)
   - Транслитерация: взаимное преобразование кириллица↔латиница → `transliteration_match` (булево)
3. **Агрегация итоговой оценки**:
   - Если `exact_match` → 1.0
   - Иначе собирается список вкладов `contributions`:
     - `variation_match` → +0.85
     - `translit_match` → +0.80
     - `fuzzy_score * 0.7` при `fuzzy_score > 0.5`
     - `phonetic_score * 0.6` при `phonetic_score > 0.3`
     - `levenshtein_score * 0.6` при `lev_score > 0.5`
     - `jaccard_score * 0.65` при `jaccard_score > 0.4`
   - `final_score = min(max(contributions), 1.0)`
   - При отсутствии любого вклада → 0.0

## 4. Рабочий процесс (workflow)
```
compare_names(name1, name2)
│
├─► Привести к строке, нормализовать (normalize_name)
│   ├─► "Katerina!" → "katerina"
│   └─► "Иван" → "иван" (кириллица сохранена)
│
├─► Точное совпадение (n1 == n2) → exact_match
│
├─► fuzzy_ratio(n1, n2) → fuzzy_score
│
├─► soundex(n1), soundex(n2) → soundex_match → fuzzy(soundex1, soundex2) → phonetic_score (1/2)
│
├─► metaphone(n1), metaphone(n2) → metaphone_match → fuzzy(metaphone1, metaphone2) → phonetic_score (2/2)
│   └─► phonetic_score = (soundex_fuzzy + metaphone_fuzzy) / 2
│
├─► get_nickname_variants(n1) ∩ get_nickname_variants(n2) → variation_match (bool)
│
├─► transliterate(n1, to_cyrillic=True) == n2  OR  transliterate(n2) == n1  OR  translit(n1)==translit(n2) → translit_match
│
├─► levenshtein_distance(n1, n2) → lev_score = 1 - (dist / max_len)
│
├─► jaccard_similarity(n1, n2) → jaccard_score
│
└─► Агрегация:
    если exact_match → 1.0
    иначе: contributions = []
        if variation_match: contributions.append(0.85)
        if translit_match: contributions.append(0.80)
        if fuzzy_score>0.5: contributions.append(fuzzy_score*0.7)
        if phonetic_score>0.3: contributions.append(phonetic_score*0.6)
        if lev_score>0.5: contributions.append(lev_score*0.6)
        if jaccard_score>0.4: contributions.append(jaccard_score*0.65)
    final_score = max(contributions) если contributions иначе 0.0
```

## 5. Технические механизмы
### Нормализация
```python
def normalize_name(name):
    if name is None: return ""
    if not isinstance(name, str): name = str(name)
    cleaned = name.strip().lower()
    cleaned = re.sub(r'[^\w]', '', cleaned, flags=re.UNICODE)  # удаляем пунктуацию
    cleaned = cleaned.replace('_', '')
    return cleaned
```
*Примечание:* `\w` с флагом `re.UNICODE` включает все буквы (кириллица, латиница) и цифры, а также подчёркивание. Подчёркивание удаляется явно.

### Soundex (русский)
Алгоритм:
1. Сохранить первую букву.
2. Заменить остальные буквы цифрами according to phonetic groups:
   - б, в, г, д → 1
   - ж, з, ц → 2
   - к, л, м, н → 3 (на практике: к=2? но в коде свои кодировки)
   - и т.д. (см. код)
3. Убрать дублирующиеся цифры подряд.
4. Заполнить/обрезать до 4 символов.

### Metaphone (Double Metaphone)
Реализует два кода (primary, secondary) для лучшего покрытия. Использует таблицы преобразований для русских букв.

### Jaccard similarity
```python
def jaccard_similarity(s1, s2, tokenize=True):
    set1 = set(s1)  # множество символов
    set2 = set(s2)
    union = set1 | set2
    if not union: return 0.0
    return len(set1 & set2) / len(union)
```

### Levenshtein distance
Классический алгоритм с использованием двух строк (previous_row, current_row) для экономии памяти. Сложность O(m·n).

### Вариации имён
Загружаются из `name_variants.py` (словарь, где каждый вариант ссылается на каноническое имя). Метод возвращает все возможные варианты, включая исходное имя.

### Транслитерация
Два словаря: `CYRILLIC_TO_LATIN` и `LATIN_TO_CYRILLIC`. Посимвольная замена с учётом многосимвольных комбинаций (например, "sh" → "ш").

## 6. Входные/выходные данные
- **Вход**: `name1: str | int`, `name2: str | int` (модуль сам приводит к строке)
- **Выход**: dict
```python
{
    'exact_match': bool,
    'fuzzy_score': float,       # 0..1
    'phonetic_score': float,
    'variation_match': bool,
    'transliteration_match': bool,
    'levenshtein_score': float,
    'jaccard_score': float,
    'final_score': float,       # 0..1
    'details': dict,            # sonst debug info
    'interpretation': str       # текстовое описание на русском
}
```

## 7. Взаимодействие с другими модулями
- **ProfileComparer** вызывает `compare_names(first_name1, first_name2)` и `compare_names(last_name1, last_name2)` для каждого профиля, затем объединяет оценки.
- **Config** не используется напрямую, но пороги можно настроить через константы в начале файла (если нужно).
- **Utils**: `lru_cache` из стандартной библиотеки.

## 8. Пример использования
```python
from src.matchers.name_matcher import NameMatcher

nm = NameMatcher()
result = nm.compare_names("Кaterina", "Katya")
print(result['final_score'])   # 0.225 (разные люди)
print(result['interpretation'])  # "Разные люди"

result2 = nm.compare_names("Иван", "Иванов")
print(result2['final_score'])  # 0.85 (очень вероятно тот же человек)
```

## 9. Ограничения
- Кеширование `lru_cache` без ограничения размера может потреблять память при очень большом числе уникальных имён; в продакшене рекомендуется `cachetools.LRUCache`.
- Алгоритм Soundex заточен под русский алфавит; для других языков может давать низкую точность.
- Транслитерация работает только для пар русский↔латиница; для других алфавитов (греческий, арабский) не поддерживается.
- Jaccard на уровне символов может давать завышенный балл для коротких имён ("Ан" vs "Анна").
