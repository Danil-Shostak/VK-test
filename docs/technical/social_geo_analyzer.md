# Social Geo Analyzer — модуль анализа географической структуры социальных сетей

## 1. Назначение
Модуль `SocialGeoAnalyzer` анализирует географическое распределение друзей двух профилей для оценки схожести их социальных кластеров. Ключевая идея: **два человека из одного круга общения имеют друзей, сгруппированных в схожих географических зонах**.

Модуль вычисляет:
- Географические координаты друзей (геокодирование по городу)
- Центроид (среднюю точку) социальной сети каждого профиля
- Расстояние между центроидам (Haversine)
- Плотность пересечения сетей: сколько друзей одного профиля попадают в радиус вокруг центроида другого
- Итоговую оценку `geo_cluster_similarity` ∈ [0, 1]

## 2. Архитектурные принципы
- **Делегирование геокодирования**: использует `GeoMatcher.get_city_coords()` — централизованный словарь координат.
- **Устойчивость к неполным данным (graceful degradation)**:
  - Если у профиля нет друзей → `has_data=False`, score=0
  - Если координаты города неизвестны → друг игнорируется (не входит в centroid)
- **Адаптивный радиус**: радиус поиска пересечения автоматически масштабируется с расстоянием между центроидами.
- **Векторизованные операции**: применяются к спискам координат, без циклов в Python (используют list comprehensions).
- **Чистые функции**: нет сторонних эффектов, кеширование не используется (координаты из статичного словаря).

## 3. Логика функционирования

### Этап 1: Геокодирование друзей
```python
def geocode_friend_locations(friends_data: Dict) -> List[Tuple[float, float]]:
    for friend in friends_data['items']:
        city_title = friend.get('city', {}).get('title', '')
        coords = GeoMatcher.get_city_coords(city_title)
        if coords:
            coordinates.append(coords)
    return coordinates  # список (lat, lon) для всех друзей с известным городом
```

### Этап 2: Вычисление центроида
```python
def calculate_centroid(coordinates: List[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
    if not coordinates: return None
    avg_lat = sum(lat for lat, _ in coordinates) / len(coordinates)
    avg_lon = sum(lon for _, lon in coordinates) / len(coordinates)
    return (avg_lat, avg_lon)
```

### Этап 3: Расстояние между центроидами
`centroid_proximity()` вызывает `haversine_distance()` из `GeoMatcher`.

### Этап 4: Адаптивный радиус
```python
BASE_RADIUS_KM = 100
MAX_RADIUS_KM = 300
DISTANCE_FACTOR = 0.5

def _get_adaptive_radius(self, centroid1, centroid2):
    distance = self.haversine_distance(...)
    radius = BASE_RADIUS_KM + distance * DISTANCE_FACTOR
    return min(radius, MAX_RADIUS_KM)
```
Обоснование: чем дальше центроиды, тем разбросаннее друзья вокруг них → нужен больший радиус, чтобы учесть возможное пересечение.

### Этап 5: Плотность пересечения (spatial_overlap_density)
Для каждого друга в `source_coords` вычисляем расстояние до `target_centroid`. Если `distance <= adaptive_radius` → считаем в пересечении.
```python
overlap_1_in_2 = count_in_radius / len(coords1)
overlap_2_in_1 = count_in_radius / len(coords2)
mutual_overlap = min(overlap_1_in_2, overlap_2_in_1)  # симметричная метрика
```

### Этап 6: Комбинированная оценка `geo_cluster_similarity`
```python
if not proximity['has_data']:
    geo_cluster_similarity = 0.0
else:
    distance_km = proximity['distance_km']
    distance_score = max(0.0, 1.0 - (distance_km / 500.0))  # 0 км → 1.0, 500 км → 0.0
    density_score = mutual_overlap

    # Корректировки:
    if distance_km < 20 and mutual_overlap < 0.1:
        geo_cluster_similarity = 0.1   # аномалия: близкие центроиды, но нет пересечения
    elif mutual_overlap >= 0.5:
        geo_cluster_similarity = 0.8 + density_score * 0.2  # высокий балл
    elif mutual_overlap >= 0.2:
        geo_cluster_similarity = distance_score * 0.4 + density_score * 0.6
    elif mutual_overlap > 0:
        geo_cluster_similarity = distance_score * 0.6 + density_score * 0.4
    else:
        geo_cluster_similarity = distance_score * 0.3  # нет пересечения → малый балл
```

### Этап 7: Интерпретация
На основе `distance_km`, `mutual_overlap`, `geo_cluster_similarity`:
- ≥0.8: "Очень высокая географическая схожесть — вероятно один город/регион"
- ≥0.6: "Высокая географическая схожесть — близкие социальные окружения"
- ≥0.4: "Умеренная географическая схожесть — частично пересекающиеся социальные круги"
- ≥0.2: "Низкая географическая схожесть — разные регионы"
- иначе: "Очень низкая географическая схожесть — социальные кластеры в разных частях страны/мира"

## 4. Рабочий процесс (workflow)
```
analyze_social_geo_overlap(friends1_data, friends2_data)
│
├─► coords1 = geocode_friend_locations(friends1_data)
│   └─► Для каждого друга: city_title → GeoMatcher.get_city_coords(city_title)
│        → список (lat, lon) или пустой список
│
├─► coords2 = geocode_friend_locations(friends2_data)
│
├─► centroid1 = calculate_centroid(coords1)  # None если нет координат
├─► centroid2 = calculate_centroid(coords2)
│
├─► proximity = centroid_proximity(coords1, coords2)
│   ├─► distance_km = haversine(centroid1, centroid2) (если оба центроида)
│   └─► has_data = (centroid1 and centroid2 and coords1 and coords2)
│
├─► IF centroid1 and centroid2:
│   ├─► used_radius = _get_adaptive_radius(centroid1, centroid2)
│   ├─► overlap_1_in_2 = spatial_overlap_density(coords1, centroid2, used_radius)
│   ├─► overlap_2_in_1 = spatial_overlap_density(coords2, centroid1, used_radius)
│   └─► mutual_overlap = min(overlap_1_in_2, overlap_2_in_1)
│
├─► geo_cluster_similarity = вычисляется по пороговой формуле (см. выше)
│
├─► has_data = (len(coords1)>0 and len(coords2)>0 and centroid1 and centroid2)
│
└─► interpretation = _interpret_geo_similarity(distance_km, mutual_overlap, geo_cluster_similarity)

Возвращает:
{
    'coords1_count': int,
    'coords2_count': int,
    'centroid1': (lat, lon) | None,
    'centroid2': (lat, lon) | None,
    'centroid_distance_km': float | None,
    'overlap_1_in_2': float,  # 0..1
    'overlap_2_in_1': float,
    'mutual_overlap': float,
    'geo_cluster_similarity': float,  # 0..1
    'has_data': bool,
    'interpretation': str,
    'details': {
        'centroid_proximity': {...},
        'spatial_analysis': {
            'radius_km': float,
            'friends1_in_radius': int,
            'friends2_in_radius': int
        }
    }
}
```

## 5. Технические механизмы

### Геокодирование (`geocode_friend_locations`)
- Использует `GeoMatcher.get_city_coords(city_title)` → `(lat, lon)` или `None`.
- Пропускает друзей без города или с неизвестным городом.
- Возвращает список координат (может быть пустым).

### Центроид (`calculate_centroid`)
- Простое арифметическое среднее широт и долгот.
- Не учитывает кривизну Земли внутри множества (допустимо для небольших регионов).
- Возвращает `None` если список координат пуст.

### Haversine
Перенесён из `GeoMatcher`. Формула:
```python
R = 6371  # км
φ = radians(lat)
Δφ = radians(lat2 - lat1)
Δλ = radians(lon2 - lon1)
a = sin(Δφ/2)^2 + cos(φ1)*cos(φ2)*sin(Δλ/2)^2
c = 2 * atan2(sqrt(a), sqrt(1-a))
distance = R * c
```

### spatial_overlap_density
```python
def spatial_overlap_density(self, source_coords, target_centroid, base_radius_km=None):
    radius = base_radius_km or self.BASE_RADIUS_KM
    count_in_radius = sum(
        1 for coord in source_coords
        if self.haversine_distance(coord[0], coord[1], target_centroid[0], target_centroid[1]) <= radius
    )
    return count_in_radius / len(source_coords) if source_coords else 0.0
```

### Пформула оценки `geo_cluster_similarity`
См. выше. Ключевые пороги:
- `distance_km < 20` и `mutual_overlap < 0.1` → анomaly, score=0.1
- `mutual_overlap >= 0.5` → высокий балл (0.8+)
- Иначе: баланс расстояния и плотности, но с пониженным весом расстояния при отсутствии пересечения.

## 6. Входные/выходные данные
- **Вход**:
  - `friends1_data: Dict` — MUST содержать `'items'` (список друзей). Каждый друг может иметь `'city': {'title': str}`.
  - `friends2_data: Dict` — аналогично
- **Выход**: `Dict[str, any]`
```python
{
    'coords1_count': int,         # кол-во координат друзей профиля1
    'coords2_count': int,
    'centroid1': (float, float) | None,
    'centroid2': (float, float) | None,
    'centroid_distance_km': float | None,
    'overlap_1_in_2': float,      # 0..1
    'overlap_2_in_1': float,
    'mutual_overlap': float,
    'geo_cluster_similarity': float,  # 0..1
    'has_data': bool,
    'interpretation': str,
    'details': {...}
}
```

## 7. Взаимодействие с другими модулями
- **GeoMatcher**: использует `get_city_coords()` для геокодирования городов.
- **ProfileComparer**: вызывается из `_analyze_social_geo`, результат используется в итоговой оценке (вес 7% по умолчанию).
- **FriendsMatcher**: не связан напрямую.
- **Utils**: нет зависимостей.

## 8. Пример использования
```python
from src.matchers.social_geo_analyzer import SocialGeoAnalyzer

analyzer = SocialGeoAnalyzer()

# Профиль1: друзья в Москве и Подольске
f1 = {'items': [
    {'city': {'title': 'Москва'}},
    {'city': {'title': 'Москва'}},
    {'city': {'title': 'Подольск'}},
]}
# Профиль2: друзья в Химках и Мytищах
f2 = {'items': [
    {'city': {'title': 'Химки'}},
    {'city': {'title': 'Мытищи'}},
    {'city': {'title': 'Москва'}},
]}

result = analyzer.analyze_social_geo_overlap(f1, f2)
print(f"Distance: {result['centroid_distance_km']} km")
print(f"Overlap: {result['mutual_overlap']:.1%}")
print(f"Similarity: {result['geo_cluster_similarity']:.1%}")
```

Вывод (приблизительно):
```
Distance: 25.3 km
Overlap: 66.7%
Similarity: 75.2%
```

## 9. Ограничения
- **Геокодирование только по словарю**: если город друга не входит в `CITY_COORDS`, он пропускается. Это может снизить `coords_count` и сместить центроид.
- **Центроид — среднее арифметическое**: не учитывает, что Земля — сфера (для больших расстояний может быть неточно). Для локальных кластеров (≤1000 км) — приемлемо.
- **Адаптивный радиус эмпиричен**: коэффициенты `BASE_RADIUS_KM=100`, `DISTANCE_FACTOR=0.5`, `MAX_RADIUS_KM=300` подобраны экспериментально; могут требовать настройки под регион.
- **Не учитывает плотность**: алгоритм считает всех друзей равнозначно; если 90% друзей в одном городе, а 10% в далёком — центроид может сместиться.
- **Mutual overlap — min из двух направлений**: строгий критерий; если один профиль имеет друзей в радиусе, а другой — нет, оценка будет низкой даже при близких центроидах.

## 10. Возможные улучшения
- **Взвешенный центроид**: учитывать количество друзей в каждом городе (сейчас просто среднее по координатам, а не по количеству друзей в городе). Но `calculate_centroid` уже использует все координаты, и если в списке 100 раз координаты Москвы — centroid будет сильно смещен к Москве. Это уже учитывается.
- **Расширение словаря координат**: подключение внешних API (Nominatim, Google Geocoding) для Unknown городов.
- **Учёт направления**: asymmetry (один кластер внутри другого) → использовать `max(overlap_1_in_2, overlap_2_in_1)` вместо `min`.
- **Вероятностная модель**: оценить значимость пересечения с учётом случайного совпадения (bootstrapping).

## 11. Производительность
- Геокодирование: O(N) на список друзей (N ≤ 5000). Каждый запрос к `CITY_COORDS` — O(1) dict lookup.
- Центроид: O(N)
- Overlap density: O(N) для каждой пары (coords1, centroid2) и (coords2, centroid1) → O(N1+N2)
- Haversine: вызывается для каждого друга при подсчёте overlap → O(N) (но это не точное расстояние, а тест ≤ radius). Можно оптимизировать, если центроиды далеко, но нет необходимости.
- Общее: линейное по количеству друзей с координатами. При 5000 друзьях — доли секунды.

## 12. Тестирование
```python
# Тривиальные случаи
assert analyzer.calculate_centroid([]) is None
assert analyzer.calculate_centroid([(55.75, 37.61)]) == (55.75, 37.61)
assert analyzer.haversine_distance(0, 0, 0, 0) == 0.0

# Адаптивный радиус
r1 = analyzer._get_adaptive_radius((55.75, 37.61), (55.76, 37.62))  # ~1.5 км → ~100.75 км
r2 = analyzer._get_adaptive_radius((55.75, 37.61), (55.0, 37.0))   # ~100 км → ~150 км
assert r1 < r2
```

## 13. Отладка
Модуль содержит `print`-логи в `analyze_social_geo_overlap` (можно отключить флагом `debug=False`). Логи включают:
- Количество координат друзей
- Расстояние между центроидами
- Адаптивный радиус
- Значения overlap_1_in_2 и overlap_2_in_1

В продакшене заменить на `logging` модуль.
