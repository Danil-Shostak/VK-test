# Geo Matcher — модуль геолокационного сравнения

## 1. Назначение
Модуль `GeoMatcher` отвечает за сравнение географических данных (городов, стран) между двумя профилями ВКонтакте. Он осуществляет:
- Нормализацию названий городов и стран
- Семантическое сопоставление синонимов ("СПб" ↔ "Санкт-Петербург")
- Расчёт точного совпадения и нормализованного совпадения
- Определение совпадения страны и региона
- Вычисление расстояния between two cities (Haversine formula)
- Генерацию итоговой оценки геолокационного сходства (0–1)

**Вход:** `location1, location2` (названия городов), необязательно `country1, country2`  
**Выход:** словарь с метриками и `final_score`

## 2. Архитектурные принципы
- **Статические словари**: `CITY_ALIASES` (синонимы городов), `CITY_COORDS` (координаты ~300 городов), `REGION_MAP` (регионы РФ/СНГ), `COUNTRY_ALIASES` (синонимы стран).
- **Двухэтапное сравнение**: сначала точное строковое совпадение после нормализации, затем нечёткое (fuzzy) для неточных совпадений.
- **Разделение ответственности**:
  - `normalize_city()` — приводит город к каноническому виду
  - `normalize_country()` — аналогично для стран
  - `compare_locations()` — оркестратор сравнения
- **Безопасность типов**: методы обрабатывают `None`, числа, строки; приводят к строке при необходимости.
- **Кеширование**: `lru_cache` на `normalize_city` и `normalize_country` для ускорения повторных вызовов.

## 3. Логика функционирования

### Нормализация города (`normalize_city`)
1. Если `city` — `None` → возврат `""`
2. Приведение к строке, если `city` не `str` (например, `int` ID города)
3. `city.strip().lower()`
4. Проверка в `self.city_normalized` (предварительно построенный словарь синонимов):
   - Если найдено → возвращаем каноническое название
   - Иначе: удаляем префиксы "г.", "город" и повторим проверку
5. Возвращаем очищенную строку

### Сравнение локаций (`compare_locations`)
**Шаг 1 — Точное совпадение**  
`exact_match = (str(location1).strip().lower() == str(location2).strip().lower())`

**Шаг 2 — Нормализованное совпадение**  
`norm1 = normalize_city(location1)`, `norm2 = normalize_city(location2)`  
`normalized_match = (norm1 == norm2)`

**Шаг 3 — Страна** (если переданы `country1, country2`)  
`norm_country1 = normalize_country(country1)`, аналог для `country2`  
`same_country = (norm_country1 == norm_country2)`

**Шаг 4 — Регион**  
`region1 = get_region(norm1)` — определяем регион по нормализованному названию города через `REGION_MAP`  
`same_region = (region1 is not None and region1 == region2)`

**Шаг 5 — Расстояние**  
Если есть координаты обоих городов в `CITY_COORDS`:
```python
distance_km = haversine_distance(lat1, lon1, lat2, lon2)
```
Иначе `None`

**Шаг 6 — Итоговая оценка** (`final_score`)
| Условие | final_score |
|---------|-------------|
| `exact_match` | 1.0 |
| `normalized_match` | 0.95 |
| `same_country and same_region` | 0.8 |
| `same_country` и `distance_km < 50` | 0.7 |
| `same_country` и `distance_km < 200` | 0.5 |
| `same_country` и `distance_km < 500` | 0.3 |
| `same_country` (расстояние неизвестно) | 0.4 |
| `same_region` (без совпадения страны) | 0.6 |
| Иначе: `fuzzy_match(location1, location2) * 0.5` | от 0 до 0.5 |

## 4. Рабочий процесс (workflow)
```
compare_locations(loc1, loc2, country1=None, country2=None)
│
├─► Обработка крайних случаев (оба пусты → 0.0; один пуст → 0.1)
│
├─► exact_match = (str(loc1).lower() == str(loc2).lower())
│
├─► norm1 = normalize_city(loc1)
│   ├─► Приведение к строке, strip, lower
│   ├─► Проверка в CITY_ALIASES → каноническое имя
│   └─► Удаление "г.", "город"
│
├─► norm2 = normalize_city(loc2)
│
├─► normalized_match = (norm1 == norm2)
│
├─► Если заданы country1/2:
│   ├─► norm_country1 = normalize_country(country1)
│   ├─► norm_country2 = normalize_country(country2)
│   └─► same_country = (norm_country1 == norm_country2)
│
├─► region1 = get_region(norm1)  # lookup в REGION_MAP
│   region2 = get_region(norm2)
│   same_region = (region1 == region2)
│
├─► coords1 = CITY_COORDS.get(norm1), coords2 = CITY_COORDS.get(norm2)
│   если оба → distance_km = haversine(lat1, lon1, lat2, lon2)
│
└─► Агрегация final_score по таблице приоритетов (см. выше)
```

## 5. Технические механизмы

### Нормализация
```python
def normalize_city(self, city):
    if city is None: return ""
    if not isinstance(city, str): city = str(city)
    city = city.strip().lower()
    # Префикс "г." или "город"
    city = re.sub(r'^(г\.?|город)\s+', '', city)
    # Поиск в словаре синонимов
    return self.city_normalized.get(city, city)
```
`self.city_normalized` строится один раз в `__init__` из `CITY_ALIASES`:
```python
self.city_normalized = {}
for canonical, aliases in CITY_ALIASES.items():
    for alias in aliases:
        self.city_normalized[alias] = canonical
```

### Расстояние Хаверайна
```python
def haversine_distance(self, lat1, lon1, lat2, lon2):
    R = 6371  # км
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c
```

### Fuzzy match городов (fallback)
Если ни одно точных совпадений не сработало, используется `SequenceMatcher` по первым 5 символам нормализованных названий:
```python
ratio = SequenceMatcher(None, norm1[:5], norm2[:5]).ratio()
```
Это помогает при опечатках в начале названия.

## 6. Входные/выходные данные
- **Вход**:
  - `location1, location2`: `str | int | None` (название города или ID)
  - `country1, country2`: необязательные `str | None`
- **Выход**: `Dict[str, any]`
```python
{
    'exact_match': bool,
    'normalized_match': bool,
    'same_country': bool,
    'same_region': bool,
    'region1': str | None,
    'region2': str | None,
    'distance_km': float | None,
    'final_score': float,  # 0..1
    'details': str         # пояснение
}
```

## 7. Взаимодействие с другими модулями
- **ProfileComparer**: вызывается из `_analyze_geolocation` для оценки совпадения городов.
- **SocialGeoAnalyzer**: использует `get_city_coords` для геокодирования друзей.
- **Config**: не используется напрямую.

## 8. Пример использования
```python
from src.matchers.geo_matcher import GeoMatcher

gm = GeoMatcher()
result = gm.compare_locations("Минск", "Минск")
print(result['final_score'])  # 1.0 (точное совпадение)

result2 = gm.compare_locations("СПб", "Санкт-Петербург")
print(result2['normalized_match'])  # True (синоним)
print(result2['final_score'])  # 0.95

result3 = gm.compare_locations("Москва", "Санкт-Петербург")
print(result3['distance_km'])  # ~700 км
print(result3['final_score'])  # 0.3 (дальние города)
```

## 9. Ограничения
- **Работает только с городами из `CITY_COORDS`** (~300 городов РФ/СНГ). Если города нет в словаре, `distance_km = None`, что снижает `final_score`.
- **Регионы** (`REGION_MAP`) покрывают только РФ/СНГ; для других стран `region = None`.
- **Нет fuzzy поиска** по списку городов (только сравнение нормализованных строк). Несопоставимые написания (например, "Новосибирск" vs "Нск") не будут распознаны.
- **Транслитерация** не применяется (только нормализация). Если город записан латиницей, а другой — кириллицей, они не будут совпадать, если оба не попадут в `CITY_ALIASES`.
- **Кеширование без Limitation**: `lru_cache` бесконечен; при большом потоке возможны утечки памяти (в продакшене использовать `cachetools.LRUCache`).

## 10. Словари данных
- `CITY_ALIASES`: словарь `{canonical_name: [alias1, alias2, ...]}`. Пример: `"Москва": ["мск", "столица"]`.
- `CITY_COORDS`: `{normalized_city: (lat, lon)}`.
- `REGION_MAP`: `{normalized_city: region_name}` (например, "москва": "московская область").
- `COUNTRY_ALIASES`: аналогично для стран.

## 11. Производительность
- Нормализация: O(1) (словарный lookup)
- Fuzzy match: O(1) (первые 5 символов)
- Haversine: O(1)
- Параллелизм не используется; модуль работает синхронно.

## 12. Тестирование
Классические тестовые случаи:
```python
assert gm.compare_locations("Москва", "Москва")['final_score'] == 1.0
assert gm.compare_locations("СПб", "Санкт-Петербург")['normalized_match'] == True
assert gm.compare_locations("Москва", "Санкт-Петербург")['distance_km'] < 800
assert gm.compare_locations("г. Москва", "Москва")['normalized_match'] == True
```
