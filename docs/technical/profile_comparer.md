# Profile Comparer — оркестратор сравнения профилей ВКонтакте

## 1. Назначение
`ProfileComparer` — главный координатор системы. Он объединяет результаты всех модулей сравнения (`name_matcher`, `geo_matcher`, `friends_matcher`, `social_geo_analyzer`, `visual_matcher`, `content_matcher`, `demographics_matcher`) и вычисляет итоговую вероятность совпадения двух профилей.

**Вход:** два профиля + опциональные данные (друзья, фотографии)  
**Выход:** структурированный результат с `final['percentage']` (0–100%), детализацией по каждому фактору и текстовой интерпретацией.

## 2. Архитектурные принципы
- **Весовая модель**: каждый фактор имеет вес (по умолчанию суммарно 100%). Веса настраиваемы через `custom_weights`.
- **Модульность**: каждый анализатор — отдельный класс; `ProfileComparer` только聚合.
- **Graceful degradation**: если для какого‑то фактора нет данных (`has_data=False`), его `score = 0` и confidence снижается.
- **Централизованное логирование**: `print`‑вывод на каждом этапе (можно заменить на `logging`).
- **Кеширование**: нет (каждый вызов независим).

## 3. Логика функционирования

### 3.1 Инициализация
```python
def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
    self.name_matcher = NameMatcher()
    self.geo_matcher = GeoMatcher()
    self.friends_matcher = FriendsMatcher()
    self.content_matcher = ContentMatcher()
    self.visual_matcher = VisualMatcher()
    self.demographics_matcher = DemographicsMatcher()
    self.social_geo_analyzer = SocialGeoAnalyzer(geo_matcher=self.geo_matcher)

    self.weights = self.DEFAULT_WEIGHTS.copy()
    if custom_weights:
        self.weights.update(custom_weights)
        # перенормируем, чтобы сумма ≈1
        total = sum(self.weights.values())
        for k in self.weights:
            self.weights[k] /= total
```

**Веса по умолчанию**:
| Ключ | Вес | Фактор |
|------|-----|--------|
| `name` | 0.15 | Имя + фамилия |
| `visual` | 0.25 | Визуальное сходство |
| `friends` | 0.20 | Общие друзья |
| `social_geo` | 0.07 | География соцсетей |
| `geolocation` | 0.08 | Город профиля |
| `content` | 0.15 | Контент/интересы |
| `demographics` | 0.10 | Демография |
| **Σ** | **1.00** | |

### 3.2 Основной метод `compare_profiles`
```
compare_profiles(p1, p2, friends1_data=None, friends2_data=None, photos1_data=None, photos2_data=None)
│
├─► 0. Подготовка: извлечь из профилей имя, гео, демографию, фото (аватары)
│
├─► 1. Анализ имени
│   name_result = self._analyze_name(p1, p2)
│   └─► compare_names(first_name1, first_name2) и compare_names(last_name1, last_name2)
│        → объединяем: score = max(first_score, last_score)
│
├─► 2. Анализ геолокации профилей
│   geo_result = self._analyze_geolocation(p1, p2)
│   └─► compare_locations(city1, city2, country1, country2)
│
├─► 3. Анализ друзей
│   friends_result = self._analyze_friends(friends1_data, friends2_data)
│   └─► compare_friends() → friend_overlap_score, jaccard, common_count
│
├─► 4. Анализ социально‑гео (НОВЫЙ)
│   social_geo_result = self._analyze_social_geo(friends1_data, friends2_data)
│   └─► analyze_social_geo_overlap() → geo_cluster_similarity
│
├─► 5. Анализ контента
│   content_result = self._analyze_content(p1, p2)
│   └─► extract_interests + compare_interests + стилистика
│
├─► 6. Анализ демографии
│   demo_result = self._analyze_demographics(p1, p2)
│   └─► compare_demographics() → overall_demographics_score
│
├─► 7. Визуальный анализ
│   visual_result = self._analyze_visual(p1, p2, photos1_data, photos2_data)
│   └─► compare_avatars + compare_all_photos + compare_photo_collections
│
├─► 8. Объединение результатов
│   analysis = {
        'name': name_result,
        'geolocation': geo_result,
        'friends': friends_result,
        'social_geo': social_geo_result,
        'content': content_result,
        'demographics': demo_result,
        'visual': visual_result
    }
│
├─► 9. Взвешенные суммы
│   weighted_scores = self._calculate_weighted_scores(analysis)
│   overall_score = sum(weighted_scores.values())
│   percentage = round(overall_score * 100, 1)
│
├─► 10. Confidence (уверенность)
│   confidence = self._calculate_confidence(analysis)
│
├─► 11. Интерпретация
│   interpretation = self._interpret_overall(percentage, confidence)
│
└─► return {
        'final': {
            'percentage': percentage,
            'interpretation': interpretation,
            'confidence': confidence,
            'data_quality': {...}
        },
        'analysis': analysis,
        'scores': weighted_scores,
        'breakdown': self._generate_detailed_breakdown(analysis)
    }
```

### 3.3 Вспомогательные методы
- `_analyze_name(p1, p2)`:
  - `first_score = name_matcher.compare_names(p1['first_name'], p2['first_name'])['final_score']`
  - `last_score = name_matcher.compare_names(p1['last_name'], p2['last_name'])['final_score']`
  - `score = max(first_score, last_score)` (если один из них совпадает сильно — достаточно)
- `_analyze_geolocation(p1, p2)`:
  - `city1 = p1.get('city', {}).get('title', '')`
  - `city2 = p2.get('city', {}).get('title', '')`
  - `country1 = p1.get('country', {}).get('title', '')` (аналогично)
  - Вызов `geo_matcher.compare_locations(city1, city2, country1, country2)`
  - `score = result['final_score']`
- `_analyze_friends(f1, f2)`:
  - Если `f1`/`f2` — `None` → `has_data=False, score=0`
  - Иначе `friends_matcher.compare_friends(f1, f2)` → `friend_overlap_score`
- `_analyze_social_geo(f1, f2)` → аналогично `friends`.
- `_analyze_content(p1, p2)` → `content_matcher.analyze(p1, p2)['score']`
- `_analyze_demographics(p1, p2)` → `demographics_matcher.compare_demographics(p1, p2)['overall_demographics_score']`
- `_analyze_visual(p1, p2, ph1, ph2)` → резульат `visual_matcher.compare()` (или вызов отдельных методов)
- `_calculate_weighted_scores(analysis)`:
  ```python
  scores = {}
  for factor, weight in self.weights.items():
      raw = analysis[factor]['score']
      scores[factor] = raw * weight
  return scores
  ```
- `_generate_detailed_breakdown(analysis)` → список словарей для отображения в UI.
- `_calculate_confidence(analysis)` → "Высокая уверенность" / "Средняя уверенность" / "Низкая уверенность" на основе `has_data` по каждому фактору.
- `_interpret_overall(percentage, confidence)` → текстовый вердикт (например, "Практически точно тот же человек").

## 4. Рабочий процесс (workflow)

См. п.3.2. Граф вызовов:

```
compare_profiles()
    │
    ├─► _analyze_name()
    │     └─► NameMatcher.compare_names() ×2 → max()
    │
    ├─► _analyze_geolocation()
    │     └─► GeoMatcher.compare_locations()
    │
    ├─► _analyze_friends()
    │     └─► FriendsMatcher.compare_friends()
    │
    ├─► _analyze_social_geo()
    │     └─► SocialGeoAnalyzer.analyze_social_geo_overlap() → geo_cluster_similarity
    │
    ├─► _analyze_content()
    │     └─► ContentMatcher.analyze()
    │
    ├─► _analyze_demographics()
    │     └─► DemographicsMatcher.compare_demographics()
    │
    ├─► _analyze_visual()
    │     ├─► VisualMatcher.compare_avatars()
    │     ├─► VisualMatcher.compare_all_photos() (опционально)
    │     └─► VisualMatcher.compare_photo_collections()
    │
    ├─► _calculate_weighted_scores() → weighted dict
    │
    ├─► overall = Σ(score_i × weight_i)
    │
    ├─► confidence = _calculate_confidence()
    │
    └─► interpretation = _interpret_overall()
```

## 5. Технические механизмы

### Обработка None/отсутствующих данных
Каждый `_analyze_*` метод возвращает словарь с ключами:
```python
{
    'score': 0.0,          # если нет данных
    'has_data': False,
    'interpretation': 'Нет данных ...'
}
```
Это гарантирует, что в `analysis` всегда есть все 7 ключей (`name`, `geolocation`, `friends`, `social_geo`, `content`, `demographics`, `visual`).

### Весовое суммирование
```python
def _calculate_weighted_scores(self, analysis):
    scores = {}
    raw_scores = {factor: analysis[factor]['score'] for factor in self.weights}
    for factor, weight in self.weights.items():
        scores[factor] = raw_scores[factor] * weight
    return scores
```
`overall_score = sum(scores.values())` гарантированно ∈ [0, 1] (если все score ∈ [0,1]).

### Confidence
Вычисляется как процент имеющихся данных:
```python
factors_present = sum(1 for a in analysis.values() if a.get('has_data'))
confidence_level = factors_present / len(analysis)  # 0..1
```
Текст: `"Высокая уверенность"` (≥0.7), `"Средняя уверенность"` (≥0.4), `"Низкая уверенность"` (иначе).

### Детальный breakdown (`_generate_detailed_breakdown`)
Создаёт список из 7 элементов (по одному на фактор) с полями:
`factor`, `name`, `weight`, `score`, `weighted_score`, `has_data`, `interpretation`.
Используется для отображения в шаблоне `comparison.html`.

## 6. Входные/выходные данные
- **Вход**:
  - `p1, p2`: `Dict` с базовыми полями профиля (`first_name`, `last_name`, `city`, `bdate`, `sex`, `photo_200`, ...).
  - `friends1_data, friends2_data`: `Dict` с ключом `'items'` (список друзей) или `None`.
  - `photos1_data, photos2_data`: `List[Dict]` (список фотографий) или `None`.
- **Выход**:
```python
{
    'final': {
        'percentage': float,      # 0-100
        'interpretation': str,
        'confidence': str,
        'data_quality': {...}
    },
    'analysis': {
        'name': {...},
        'geolocation': {...},
        'friends': {...},
        'social_geo': {...},
        'content': {...},
        'demographics': {...},
        'visual': {...}
    },
    'scores': {  # взвешенные
        'name': float,
        ...
    },
    'breakdown': [  # list of factor details
        {...}, ...
    ]
}
```

## 7. Взаимодействие с другими модулями
- **Зависит от всех matcher-модулей** (создаёт их экземпляры в `__init__`).
- **Не зависит от** `handlers`, `vk_api`, `core`.
- Использует `utils.py` только если нужно (не используется напрямую).

## 8. Пример использования
```python
from src.matchers.profile_comparer import ProfileComparer

comparer = ProfileComparer()

p1 = {'first_name': 'Иван', 'last_name': 'Петров', 'city': {'title': 'Москва'}, 'bdate': '15.03.1995', 'sex': 2}
p2 = {'first_name': 'Иван', 'last_name': 'Петров', 'city': {'title': 'Москва'}, 'bdate': '15.03.1995', 'sex': 2}

f1 = {'items': [{'city': {'title': 'Москва'}}]}
f2 = {'items': [{'city': {'title': 'Москва'}}]}

result = comparer.compare_profiles(p1, p2, friends1_data=f1, friends2_data=f2)

print(f"Вероятность: {result['final']['percentage']}%")
print(f"Интерпретация: {result['final']['interpretation']}")

for factor, data in result['analysis'].items():
    print(f"{factor}: {data.get('score', 0):.2%} — {data.get('interpretation', '')}")
```

## 9. Настройка весов
```python
custom_weights = {
    'name': 0.10,
    'visual': 0.30,
    'friends': 0.20,
    'social_geo': 0.10,
    'geolocation': 0.05,
    'content': 0.15,
    'demographics': 0.10
}
comparer = ProfileComparer(custom_weights=custom_weights)
```
Если сумма не 1, метод автоматически нормализует веса (сумма станет 1).

## 10. Ограничения
- **Фиксированная последовательность анализа**: все модули вызываются всегда, даже если профиль не содержит данных для какого‑то модуля (но внутренне каждый модуль обрабатывает `None`).
- **Пороги жёстко закодированы** в каждом модуле; глобальные пороги (например, `name_fuzzy_threshold`) нельзя изменить через `ProfileComparer`.
- **Нет кеширования** результатов анализа одного профиля — при повторном вызове с теми же данными вычисления заново.
- **Синхронность**: `compare_profiles` блокирующий; для веб‑сервера с большим числом запросов рекомендуется кешировать результаты или использовать asynchronous workers (например, via `asyncio.to_thread`).
- **Зависимость от качества входных данных**: если `friends_data` пришло пустое, `social_geo` и `friends` дадут 0, что сильно снизит итог.

## 11. Возможные улучшения
- **Динамическое отключение модулей**: если данные отсутствуют, пропускать вызов (сейчас вызывается, но возвращает `has_data=False`).
- **Кеширование** по хешу входных данных (`p1`, `p2`, `friends`, `photos`) для быстрого повтора.
- **Параллельные вычисления**: запуск `_analyze_*` в пуле потоков (ThreadPool) для ускорения на многопроцессорных системах.
- **Более сложная интерпретация**: учитывать не только `percentage`, но и `confidence`, и "подозрительные" паттерны (например, высокий `name_score` и нулевой `visual_score`).
- **Логирование**: заменить `print` на `logging` с разными уровнями (DEBUG, INFO, WARNING).

## 12. Производительность
- **Name, Geo, Content, Demographics**: O(1) – мгновенно.
- **Friends**: O(N) по количеству друзей (N ≤ 5000).
- **Social Geo**: O(N) геокодирование + O(N) centroid + O(N) overlap density → до ~0.1 сек при 5000 друзьях.
- **Visual**: самое медленное — сравнение фото. `max_comparisons=300` ограничивает до ~2–3 сек.
- **Итого**:典型 вызов ~0.5–5 секунд в зависимости от количества фото и друзей.

## 13. Тестирование
```python
pc = ProfileComparer()
# Идентичные профили
p = {'first_name': 'Анна', 'last_name': 'Смирнова', 'city': {'title': 'СПб'}, 'sex': 1}
result = pc.compare_profiles(p, p)
assert result['final']['percentage'] == 100.0

# Разные имена, один город
p2 = {'first_name': 'Иван', 'last_name': 'Иванов', 'city': {'title': 'СПб'}, 'sex': 2}
result2 = pc.compare_profiles(p, p2)
assert result2['final']['percentage'] < 50
```

## 14. Отладка
При запуске `compare_profiles` выводятся отладочные строки:
```
📛 Анализ имени...
🌍 Анализ геолокации...
👥 Анализ друзей...
🗺️ Анализ географии социальных кластеров...
📝 Анализ контента...
📊 Анализ демографии...
📸 Визуальный анализ...
   Сравнение аватарок профилей...
   ...
⚖️ Расчет итоговой оценки...
```
В каждом `_analyze_*` есть `print` с деталями (identical_photos, activity_similarity, jaccard и т.д.). Для продакшена заменить на `logging.getLogger(__name__)`.

## 15. Расширение
Чтобы добавить новый фактор:
1. Создать модуль-матчер с методом `compare(...)` → возвращает `score` ∈ [0,1].
2. Добавить экземпляр в `__init__` (`self.new_matcher = NewMatcher()`).
3. Добавить `_analyze_new()` метод, вызывающий `new_matcher.compare`.
4. Добавить ключ `'new'` в `DEFAULT_WEIGHTS`.
5. Добавить строку в `_generate_detailed_breakdown`.
6. Добавить вызов `_analyze_new` в `compare_profiles` в нужном месте.
7. Обновить шаблон `comparison.html` для отображения нового фактора (опционально).
