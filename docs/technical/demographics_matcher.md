# Demographics Matcher — модуль сравнения демографических данных профилей

## 1. Назначение
Модуль `DemographicsMatcher` сравнивает демографические поля профилей ВКонтакте: дата рождения, пол, семейное положение, образование, карьеру, родной город. Оценка используется как один из факторов в итоговой вероятности совпадения профилей.

**Вход:** два пользовательских профиля (dict)  
**Выход:** словарь с оценочными показателями по каждому полю и общей демографической схожестью `overall_demographics_score` ∈ [0, 1].

## 2. Архитектурные принципы
- **Полевое сравнение**: каждое демографическое поле сравнивается независимо с собственной логикой и весами.
- **Обработка отсутствующих данных**: если поле не заполнено у одного или обоих профилей — `score` по умолчанию 0.0 или 0.5 в частичных случаях.
- **Нормализация строк**: приведение к нижнему регистру, обработка `None`/числовых значений.
- **Устойчивость к типу**: все строковые поля приводятся к `str` перед вызовом `.lower()`.

## 3. Логика функционирования

### 3.1 Структура результата `compare_demographics(user1, user2)`
```python
{
    'birth_date': {
        'match': bool,          # совпадение даты рождения
        'score': float,         # 1.0 если совпали, иначе 0.0
        'value1': str, 'value2': str
    },
    'sex': {
        'match': bool,
        'score': 1.0 или 0.0
    },
    'family_status': {...},         # аналогично
    'education': {...},             # сравнение по университету/факультету
    'career': {
        'common_companies': set,    # общие компании
        'common_positions': set,    # общие должности
        'score': float              # Jaccard по компаниям и должностям
    },
    'home_town': {
        'match': bool,
        'score': 1.0 или 0.0
    },
    'overall_demographics_score': float,  # среднее по всем score, где определён результат
    'interpretation': str
}
```

### 3.2 Подробно по полям

#### Дата рождения (`birth_date`)
- Формат: `"DD.MM.YYYY"` или `"DD.MM"` или `"YYYY"`.
- Нормализация: если есть только день и месяц, сравниваем `"DD.MM"`; если год — сравниваем год.
- Если оба полных: сравнение полной строки после нормализации.
- `score = 1.0` если совпадают, иначе `0.0`.

#### Пол (`sex`)
- VK: `1` — женский, `2` — мужской, `0` — неизвестен.
- Сравнение: `user1['sex'] == user2['sex']` (если оба не 0).
- Если один или оба 0 → `score=0.0` (недостаточно данных).

#### Семейное положение (`relation`)
- VK: `1–8` (не женат/не замужем, есть друг/подруга, помолвлен, женат/замужем, всё сложно, в активном поиске, влюблён, в гражданском браке).
- Прямое сравнение чисел.
- `score = 1.0` при совпадении, иначе `0.0`.

#### Образование (`education`)
Поля: `university`, `university_name`, `faculty`, `faculty_name`, `graduation`.
- Сравнение по нескольким полям:
  - Для каждого из `university`, `university_name`, `faculty`, `faculty_name`:
    - Привести к строке, lower()
    - Добавить в `results` список (если значение есть)
  - Сравниваем множества: `common = set1 ∩ set2`
  - `score = len(common) / total_fields_compared` (процент совпавших полей).
  - Если нет данных по обоим — `score=0.0`.

#### Карьера (`career`)
- `career` — список мест работы: `[{'company': str, 'position': str, ...}]`.
- Строим множества `companies1`, `positions1` и аналогично для профиля2.
- `common_companies = companies1 ∩ companies2`
- `common_positions = positions1 ∩ positions2`
- `score = (|common_companies| / |union|) * 0.5 + (|common_positions| / |union|) * 0.5` (среднее Jaccard по компаниям и должностям).
- Если оба пусты → `score=0.0`.

#### Родной город (`home_town`)
- Строка (название города).
- Сравнение: `home_town1.lower() == home_town2.lower()`.
- Приведение к строке, если число.
- `score = 1.0` при совпадении, иначе `0.0`.

### 3.3 Агрегация общей оценки (`overall_demographics_score`)
- Берём все `score` из полей `birth_date`, `sex`, `family_status`, `education`, `career`, `home_town`.
- Исключаем те, где `score == 0` из-за отсутствия данных? В текущей реализации включаются все, но если данных нет, `score=0` — это штраф.
- `overall = sum(scores) / len(scores)` (среднее арифметическое).

### 3.4 Интерпретация (`_interpret_demographics`)
На основе `overall_score`:
- ≥0.8: "Очень высокое демографическое совпадение"
- ≥0.6: "Высокое демографическое совпадение"
- ≥0.4: "Умеренное демографическое совпадение"
- ≥0.2: "Низкое демографическое совпадение"
- иначе: "Демографические данные различаются"

## 4. Рабочий процесс (workflow)
```
compare_demographics(user1, user2)
│
├─► БИО:
│   bdate1 = user1.get('bdate', '')
│   bdate2 = user2.get('bdate', '')
│   normalize_bdate → сравнить день+месяц или год
│   results['birth_date'] = {'match': match, 'score': 1.0 if match else 0.0, ...}
│
├─► ПОЛ:
│   sex1 = user1.get('sex', 0)
│   sex2 = user2.get('sex', 0)
│   match = (sex1 == sex2 and sex1 != 0)
│   results['sex'] = {'match': match, 'score': 1.0 if match else 0.0, ...}
│
├─► СЕМЕЙНОЕ ПОЛОЖЕНИЕ:
│   rel1 = user1.get('relation', 0)
│   rel2 = user2.get('relation', 0)
│   match = (rel1 == rel2 and rel1 != 0)
│
├─► ОБРАЗОВАНИЕ:
│   edu1 = user1.get('education', {})
│   edu2 = user2.get('education', {})
│   checked_fields = ['university', 'university_name', 'faculty', 'faculty_name']
│   Для каждого поля:
│       v1 = edu1.get(field, '')
│       v2 = edu2.get(field, '')
│       нормализовать к строке, lower()
│       добавить в списки list1, list2
│   common = set(list1) ∩ set(list2)
│   total = уникальные непустые поля
│   score = |common| / total если total > 0 иначе 0.0
│
├─► КАРЬЕРА:
│   career1 = user1.get('career', [])
│   career2 = user2.get('career', [])
│   companies1 = {str(job['company']).lower() for job in career1 if job.get('company')}
│   positions1 = {str(job['position']).lower() ...}
│   companies2, positions2 аналогично
│   common_companies = companies1 ∩ companies2
│   common_positions = positions1 ∩ positions2
│   union_comp = companies1 ∪ companies2
│   union_pos = positions1 ∪ positions2
│   comp_score = |common_companies| / |union_comp|
│   pos_score = |common_positions| / |union_pos|
│   results['career'] = {
│       'common_companies': list(common_companies),
│       'common_positions': list(common_positions),
│       'score': (comp_score + pos_score) / 2
│   }
│
├─► РОДНОЙ ГОРОД:
│   ht1 = str(user1.get('home_town', '')).lower().strip()
│   ht2 = str(user2.get('home_town', '')).lower().strip()
│   match = (ht1 == ht2 and ht1 != '')
│   results['home_town'] = {'match': match, 'score': 1.0 if match else 0.0, ...}
│
├─► АГРЕГАЦИЯ:
│   scores = [field_result['score'] for field_result in results.values() if 'score' in field_result]
│   overall = sum(scores) / len(scores) если scores иначе 0.0
│   results['overall_demographics_score'] = overall
│   results['interpretation'] = _interpret_demographics(overall)
│
└─► return results
```

## 5. Технические механизмы

### Нормализация
Все строковые значения приводятся к `str` (если передан `int`), затем:
```python
value = str(value).strip().lower()
```

### Обработка списков карьеры
- Используются генераторы множеств с проверкой `if job.get('company')` и `if job.get('position')`.
- Преобразование в `str` защищает от `int` (например, числового ID компании).

### Оценка образования
- Учитываются 4 поля; сравнение идёт по множественному совпадению. Например, совпали `university` и `faculty` → 2/4 = 0.5.
- Не учитывает градации (не следует, что `university` важнее `faculty`).

### Оценка карьеры
- Jaccard для компаний и должостей вносят равный вклад.
- Если один из set пуст → `|union| = 0` → score = 0 (штраф за отсутствие данных).

## 6. Входные/выходные данные
- **Вход**: `user1: Dict`, `user2: Dict`. Ожидаемые ключи: `bdate`, `sex`, `relation`, `education` (dict), `career` (list), `home_town`.
- **Выход**:
```python
{
    'birth_date': {...},
    'sex': {...},
    'family_status': {...},
    'education': {
        'score': float,
        'matches': [...],
        'university1': str, 'university2': str, ...
    },
    'career': {
        'common_companies': List[str],
        'common_positions': List[str],
        'score': float
    },
    'home_town': {...},
    'overall_demographics_score': float,
    'interpretation': str
}
```

## 7. Взаимодействие с другими модулями
- **ProfileComparer**: вызывается из `_analyze_demographics`, вес 10%.
- **Utils**: нет.
- **Config**: нет.

## 8. Пример использования
```python
from src.matchers.demographics_matcher import DemographicsMatcher

dm = DemographicsMatcher()
u1 = {
    'bdate': '15.03.1995',
    'sex': 2,
    'relation': 1,
    'education': {'university': 'МГУ', 'faculty': 'ВМК'},
    'career': [{'company': 'Яндекс', 'position': 'Инженер'}],
    'home_town': 'Москва'
}
u2 = {
    'bdate': '15.03.1995',
    'sex': 2,
    'relation': 1,
    'education': {'university': 'МГУ', 'faculty': 'ВМК'},
    'career': [{'company': 'Яндекс', 'position': 'Разработчик'}],
    'home_town': 'Москва'
}
result = dm.compare_demographics(u1, u2)
print(result['overall_demographics_score'])  # ~0.9 (почти всё совпадает)
```

## 9. Ограничения
- **Форматы дат**: только `DD.MM.YYYY`, `DD.MM`, `YYYY`. Другие форматы (ISO: `1995-03-15`) не парсятся → `score=0`.
- **Строгая эквивалентность**: `"МГУ"` vs `"Московский государственный университет"` — разные строки, не совпадут.
- **Карьера**: учитываются только компании и должности, но не периоды работы. Если один работал в Яньде 2010–2020, второй 2020–2023 — совпадение по компании даёт полный балл, хотя реально пересечения нет.
- **Нормализация**: нет стемминга/лемматизации для русского; `"инженер"` vs `"инженера"` — разные строки.
- **Отсутствующие поля** → 0 в overall, что сильно штрафует.

## 10. Возможные улучшения
- **Расширенный парсинг дат**: использовать `dateutil.parser` для любых форматов.
- **Семантическое сравнение** названий вузов/компаний через внешний справочник (например, `"МГУ"` ↔ `"МГУ им. Ломоносова"`).
- **Учёт временных интервалов** в карьере (пересечение периодов работы).
- **Взвешивание полей**: `birth_date` и `sex` — высокий вес, `home_town` — средний, `career` — низкий.
- **Лемматизация** для русских слов (pymorphy2) → нормализация `"инженера"` → `"инженер"`.
- **Нечёткое сравнение** для строковых полей (fuzzy ratio) вместо точного равенства.

## 11. Производительность
- Все операции O(N) по количеству полей/элементов.
- Множества (set) дают O(1) lookup.
- Для карьеры до 10 мест работы — мгновенно.

## 12. Тестирование
```python
dm = DemographicsMatcher()
u1 = {'bdate': '01.01.1990', 'sex': 2}
u2 = {'bdate': '01.01.1990', 'sex': 2}
r = dm.compare_demographics(u1, u2)
assert r['birth_date']['score'] == 1.0
assert r['sex']['score'] == 1.0
assert r['overall_demographics_score'] == 1.0
```

## 13. Отладка
Метод `compare_demographics` не содержит prints; использовать logging при необходимости.
