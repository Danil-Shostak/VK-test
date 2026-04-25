# Friends Matcher — модуль анализа социальных связей (друзей)

## 1. Назначение
Модуль `FriendsMatcher` осуществляет сравнение списков друзей двух профилей ВКонтакте. Основная цель — оценить степень пересечения социальных кругов, что является сильным индикатором принадлежности профилей одному человеку (или близким людям).

**Вход:** два объекта `friends_data` из VK API (словари с ключом `items`)  
**Выход:** словарь с метриками пересечения и итоговой оценкой `friend_overlap_score` ∈ [0, 1]

## 2. Архитектурные принципы
- **Чистые данные**: модуль оперирует только списками ID друзей; не хранит состояние.
- **Set-based операции**: все вычисления пересечений выполняются через `set` для O(1) lookup.
- **Нормализация на уровне ID**: ID друзей — уникальные числовые идентификаторы, не требуют нормализации.
- **Отсутствие внешних зависимостей**: только стандартная библиотека (`collections.Counter`).
- **Статистический подход**: оценка строится на базе Jaccard index с корректировками на размеры списков.

## 3. Логика функционирования

### Извлечение данных
1. `extract_friend_ids(friends_data)` → `Set[int]`:
   - Проверяет `friends_data` и наличие ключа `'items'`
   - Извлекает `friend['id']` для каждого элемента
   - Возвращает множество ID

2. `extract_friend_info(friends_data)` → `List[Dict]`:
   - Для каждого друга извлекает: `id`, `first_name`, `last_name`, `sex`, `bdate`, `city`, `online`, `common_count`, `relation`
   - Используется для детального анализа (не для итоговой оценки в `ProfileComparer`)

### Сравнение (`compare_friends`)
**Шаг 1 — Множества ID**
```python
ids1 = extract_friend_ids(friends1)
ids2 = extract_friend_ids(friends2)
```

**Шаг 2 — Пересечение**
```python
common_ids = ids1 & ids2
common_count = len(common_ids)
```

**Шаг 3 — Jaccard index**
```python
union = ids1 | ids2
jaccard_index = common_count / len(union) if union else 0.0
```

**Шаг 4 — Процент от каждого списка**
```python
percent_of_1 = common_count / len(ids1) if ids1 else 0
percent_of_2 = common_count / len(ids2) if ids2 else 0
```

**Шаг 5 — Базовая оценка**
`base_score = jaccard_index` (0..1)

**Шаг 6 — Бонусы**:
- Если `common_count >= 10` → `base_score = min(1.0, base_score + 0.2)`
- Если `common_count >= 5` → `base_score = min(1.0, base_score + 0.1)`

**Шаг 7 — Штраф за несбалансированные размеры**:
```python
if len(ids1) > 0 and len(ids2) > 0:
    size_ratio = min(len(ids1), len(ids2)) / max(len(ids1), len(ids2))
    base_score *= size_ratio  # снижает оценку, если списки сильно различаются
```

**Шаг 8 — Финальный `friend_overlap_score`**
```python
friend_overlap_score = min(1.0, base_score)
```

**Шаг 9 — Интерпретация** (`_interpret_friend_score`)
| Общих друзей | Интерпретация |
|---|---|
| ≥20 | "Очень сильное пересечение друзей" |
| ≥10 | "Сильное пересечение друзей" |
| ≥5 | "Значительное пересечение друзей" |
| ≥1 | "Есть общие друзья" |
| 0 | "Нет общих друзей" |

## 4. Рабочий процесс (workflow)
```
compare_friends(friends1, friends2)
│
├─► ids1 = extract_friend_ids(friends1)  # Set[int]
├─► ids2 = extract_friend_ids(friends2)
│
├─► common_ids = ids1 ∩ ids2
├─► common_count = |common_ids|
│
├─► union = ids1 ∪ ids2
├─► jaccard_index = |common_ids| / |union|
│
├─► percent_of_1 = common_count / |ids1|
├─► percent_of_2 = common_count / |ids2|
│
├─► base_score = jaccard_index
│
├─► Бонус:
│   ├─► если common_count ≥ 10: base_score += 0.2
│   └─► если common_count ≥ 5: base_score += 0.1
│
├─► Штраф за размер:
│   size_ratio = min(|ids1|,|ids2|) / max(|ids1|,|ids2|)
│   base_score *= size_ratio
│
├─► friend_overlap_score = min(1.0, base_score)
│
└─► interpretation = _interpret_friend_score(common_count, jaccard_index)
```

## 5. Технические механизмы

### Set операции
Использование `set` позволяет:
- Быстрое вычисление пересечения (`&`) — O(min(|A|,|B|))
- Объединение (`|`) для Jaccard
- Разность (`-`) для уникальных друзей (не используется в текущем скоре, но доступно)

### Корректировка на размер списка
`size_ratio` предотвращает завышение оценки, когда один профиль имеет 5 друзей из 5 общих (100%), а второй — 500 друзей с 5 общими (1%). Без этого `jaccard` уже учтёт дисбаланс (Jaccard = 5/500 = 0.01), но дополнительное умножение на `size_ratio` снижает влияние абсолютного количества общих друзей при несбалансированных списках.

### Бонус за количество
Прямой прирост 0.2 за ≥10 общих друзей нужен для сильно пересекающихся кругов (несколько общих из сотен — всё равно существенно).

### Ограничения `_interpret_friend_score`
Интерпретация зависит только от `common_count`, а не от `jaccard_index`. Это упрощение; в будущем можно учитывать `percent_of_1/2`.

## 6. Входные/выходные данные
- **Вход**:
  - `friends1: Dict` — должны содержать `'items'` со списком друзей, каждый с `'id'`
  - `friends2: Dict` — аналогично
- **Выход**: `Dict[str, any]`
```python
{
    'common_friends': List[Dict],      # полные данные об общих друзьях
    'common_friend_ids': List[int],    # ID общих друзей
    'common_count': int,
    'total_friends_1': int,
    'total_friends_2': int,
    'unique_to_1': List[int],
    'unique_to_2': List[int],
    'jaccard_index': float,            # 0..1
    'percent_of_1': float,
    'percent_of_2': float,
    'friend_overlap_score': float,     # 0..1 (финальный)
    'interpretation': str
}
```

## 7. Взаимодействие с другими модулями
- **ProfileComparer**: вызывается из `_analyze_friends`, результат используется в агрегации (вес 20%).
- **SocialGeoAnalyzer**: не связан напрямую.
- **Utils**: не используется.

## 8. Пример использования
```python
from src.matchers.friends_matcher import FriendsMatcher

fm = FriendsMatcher()
f1 = {'items': [{'id': 1}, {'id': 2}, {'id': 3}]}
f2 = {'items': [{'id': 2}, {'id': 3}, {'id': 4}]}
result = fm.compare_friends(f1, f2)

print(result['common_count'])     # 2 (ID 2 и 3)
print(result['jaccard_index'])    # 2 / 4 = 0.5
print(result['friend_overlap_score'])  # 0.6 (с бонусом за 2 общих? нет, бонус от 5)
```

## 9. Ограничения
- **Только ID**: сравнение идёт только по ID, а не по другим полям (имя, город). Если ID разные, но это один человек с двумя аккаунтами, система это не учтёт. Однако социальные связи (общие друзья) обычно коррелируют с ID.
- **Нет ponderation по силе связи**: все друзья считаются одинаково, хотя close friends vs distant friends могут отличаться (VK не предоставляет вес связи).
- **API ограничения**: VK API возвращает максимум 5000 друзей; если у профиля >5000, данные неполные → оценка смещается.
- **Приватные друзья**: если друг скрыл список друзей, его ID не попадет в `items`, что снижает `coords_count` в `social_geo_analyzer`.

## 10. Возможные улучшения
- Учитывать уровень дружбы (если API возвращает `friend_status`: 0/1/2/3).
- Учитывать взаимность (друзья-друзья vs подписчики).
- Использовать не только ID, но и нормализованные имена/фамилии для доп. проверки.
- Добавить метрику «общие группы» (common groups).

## 11. Производительность
- Время: O(|ids1| + |ids2|) на построение множеств + O(min) на пересечение.
- Память: O(|ids1| + |ids2|) для хранения set'ов.
- Для 5000 друзей каждый — нормально.
