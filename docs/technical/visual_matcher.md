# Visual Matcher — модуль визуального сравнения профилей ВКонтакте

## 1. Назначение
Модуль `VisualMatcher` осуществляет сравнение визуальных данных (фотографий) двух профилей ВКонтакте с целью определения идентичности личности. Модуль использует:
- **Распознавание лиц** (face_recognition / MediaPipe) для сравнения аватаров и всех фотографий
- **Сравнение метаданных** фотографий (id, дата, лайки, комментарии) для выявления идентичных изображений
- **Анализ активности** (activity_similarity) — схожесть паттернов лайков/комментариев

**Вход:** два профиля (с аватарами) и/или списки фотографий  
**Выход:** `visual_score` ∈ [0, 1] + детали (face_similarity, identical_photos_count, activity_similarity)

## 2. Архитектурные принципы
- **Модульность**: отдельные методы для аватаров (`compare_avatars`) и коллекций (`compare_photo_collections`, `compare_all_photos`).
- **Graceful degradation**: если лицо не найдено на аватаре — переходит к сравнению всех фотографий.
- **Ограничение вычислительной сложности**: `max_comparisons` ограничивает количество пар фото для сравнения лиц (чтобы не дожидаться бесконечности).
- **Кеширование**: `lru_cache` для `get_avatar_url` (извлечение URL наилучшего качества).
- **Поддержка нескольких бэкендов** распознавания лиц (face_recognition, MediaPipe) через `face_recognition_engine`.

## 3. Логика функционирования

### 3.1 Сравнение аватаров (`compare_avatars`)
1. Извлекаем URL аватара профиля (`p1.get('photo_200')`). При необходимости используем `get_best_photo_url` (если есть несколько размеров).
2. Скачиваем аватарки во временные файлы (если они не локальные).
3. Загружаем изображения, извлекаем face encodings через `face_recognition_engine`.
4. Сравниваем encodings:
   - Если обнаружены лица на обоих аватарах → вычисляем `face_distance` → `face_similarity = 1 - distance`
   - `face_match = (face_similarity >= 60%)` (настраиваемый порог)
5. Возвращаем `{'face_comparison': {success, face_similarity, face_match, method}}`

### 3.2 Сравнение всех фотографий (`compare_all_photos`)
Вызывается, если на аватарах лица не найдены или similarity < 60%.
1. Получаем списки `photos1`, `photos2` (данные из VK API).
2. Ограничиваем первую N фотографий (по умолчанию 50) и для каждой — вложенный цикл по второй коллекции (макс 50) → максимум 2500 сравнений, но параметр `max_comparisons` ограничивает (например, 300).
3. Для каждой пары:
   - Извлекаем URL (через `get_avatar_url`).
   - Скачиваем временные файлы.
   - Сравниваем лица → получаем `face_similarity`.
   - Отслеживаем `max_similarity` среди всех пар.
4. Возвращает `{'max_similarity': float, 'total_comparisons': int}`.

### 3.3 Анализ коллекций фотографий (`compare_photo_collections`)
Сравнивает **метаданные** фотографий без face recognition (быстро).
1. Для каждой коллекции строим `set` идентификаторов на основе:
   - `photo['id']` (уникальный ID фото в VK)
   - Опционально: комбинация `(date, likes_count, comments_count)` — если ID нет
2. `identical_photos_count = |set1 ∩ set2|` — полностью совпадающие снимки.
3. `activity_similarity`:
   - Собираем все `likes` и `comments` по двум профилям.
   - Нормализуем: `norm1 = (sum_likes1, sum_comments1)`, `norm2` аналогично.
   - Сравниваем через cosine similarity или отношение: `activity_similarity = min(norm1, norm2) / max(norm1, norm2)` (по каждому из показателей и далее усредняем).
4. Возвращает `{'identical_photos_count': int, 'activity_similarity': float (0..1)}`.

## 4. Рабочий процесс (workflow) в `_analyze_visual` (ProfileComparer)

```
_analyze_visual(p1, p2, ph1, ph2)
│
├─► 1. Сравнение аватаров
│   avatar_result = visual_matcher.compare_avatars(p1, p2)
│   ├─► face_similarity = avatar_result['face_similarity'] (если есть)
│   └─► face_match = avatar_result['face_match']
│
├─► 2. Если (face_similarity==0 ИЛИ face_match=False) И есть photos1, photos2:
│   all_photos_result = visual_matcher.compare_all_photos(ph1, ph2, max_comparisons=300)
│   all_photos_similarity = all_photos_result['max_similarity']
│
├─► 3. Если есть ph1 и ph2:
│   photo_collection_result = visual_matcher.compare_photo_collections(ph1, ph2)
│   identical_photos = photo_collection_result['identical_photos_count']
│   activity_similarity = photo_collection_result['activity_similarity']
│
├─► 4. Определяем итоговый visual_score:
│   best_face_similarity = max(face_similarity, all_photos_similarity)
│   visual_score = best_face_similarity / 100.0
│
│   # БОНУС за много идентичных фото (признак одного аккаунта)
│   if identical_photos >= 10:
│       visual_score = max(visual_score, 0.8)
│   elif identical_photos >= 5:
│       visual_score = max(visual_score, 0.6)
│   elif identical_photos >= 3:
│       visual_score = max(visual_score, 0.5)
│
│   # Если нет совпадений по лицам, но есть activity_similarity
│   if visual_score == 0.0 and activity_similarity > 0:
│       visual_score = activity_similarity * 0.7
│
├─► 5. Интерпретация:
│   if identical_photos >= 10: "Найдено X идентичных фотографий — вероятно один аккаунт"
│   elif best_face_similarity >= 80: "Очень высокая схожесть лиц"
│   elif best_face_similarity >= 60: "Высокая схожесть лиц"
│   elif identical_photos > 0: "Найдено X идентичных фотографий"
│   elif activity_similarity > 0.7: "Похожая активность на фотографиях"
│   else: "Низкое визуальное сходство"
│
└─► return {
        'score': visual_score,
        'face_similarity': best_face_similarity,
        'face_match': best_face_similarity >= 60,
        'face_method': ...,
        'identical_photos': identical_photos,
        'activity_similarity': activity_similarity,
        'all_photos_comparisons': int,
        'interpretation': str
    }
```

## 5. Технические механизмы

### Извлечение URL аватара (`get_avatar_url`)
Ищет в `photo` объекте:
- `'url'` — прямая ссылка
- `'sizes'` — список размеров, выбирает наибольший
- Если `'orig_photo'` есть — это оригинал

### Скачивание фото (`download_avatar`)
- Скачивает по URL во временный файл.
- Возвращает `True` при успехе, иначе `False`.
- Использует `requests` с User-Agent и таймаутом.

### Face Recognition
- **FaceRecognitionEngine** (из `face_recognition_module.py`):
  - Загружает модель (dlib или MediaPipe)
  - `extract_face_encoding(image_path)` → 128‑dim vector
  - `compare_faces(encoding1, encoding2)` → similarity %
- **Параметры**:
  - `tolerance=0.6` для face_recognition (default)
  - `model='small'` или `'large'`

### Activity Similarity
- Суммирует все `likes` и `comments` по каждой коллекции.
- Нормализует делением на максимальное значение (min-max scaling).
- Итог: `(1 - |likes1_norm - likes2_norm|) * (1 - |comments1_norm - comments2_norm|)` → [0,1].

### Identical Photos
- Сравнение множеств `photo_ids`. Если VK API возвращает одинаковые ID → 100% совпадение.
- Если ID нет, fallback: сравнение по `(date, likes_count, comments_count)`.

## 6. Входные/выходные данные
- **Вход**:
  - `p1, p2`: Dict с ключами `first_name`, `last_name`, `photo_200` (URL)
  - `ph1, ph2`: List[Dict] — список фотографий (каждый dict с `id`, `date`, `likes`, `comments`, `sizes` и т.д.)
- **Выход**: `Dict[str, any]`
```python
{
    'score': float,                  # 0..1 (финальный visual_score)
    'has_data': bool,
    'face_similarity': float,        # 0..100 (%)
    'face_match': bool,              # >=60%
    'face_method': str,              # 'avatar' или 'face_recognition_all_photos'
    'identical_photos': int,         # кол-во совпадающих фото
    'activity_similarity': float,    # 0..1
    'all_photos_comparisons': int,   # сколько пар сравнили
    'interpretation': str
}
```

## 7. Взаимодействие с другими модулями
- **ProfileComparer**: вызывается из `_analyze_visual`, вклад в финальную оценку (вес 25%).
- **Utils**: `download_image` из `utils.py`; `tempfile` для временных файлов.
- **FaceRecognitionEngine**: инжектируется в `VisualMatcher` через конструктор.

## 8. Пример использования
```python
from src.matchers.visual_matcher import VisualMatcher

vm = VisualMatcher()
p1 = {'first_name': 'Иван', 'last_name': 'Петров', 'photo_200': 'https://...'}
p2 = {'first_name': 'Иван', 'last_name': 'Петров', 'photo_200': 'https://...'}
ph1 = [{'id': 1, 'date': 1600000000, 'likes': {'count': 10}, 'comments': {'count': 2}, 'sizes': []}]
ph2 = [{'id': 1, 'date': 1600000000, 'likes': {'count': 10}, 'comments': {'count': 2}, 'sizes': []}]

result = vm.compare(p1, p2, photos1=ph1, photos2=ph2)
print(result['score'])  # 0.8 если 10+ идентичных фото
```

## 9. Ограничения
- **Требуются фотографии с лицами**. Если на всех фото нет лиц (текст, логотипы), face_similarity = 0, но может сработать activity_similarity или identical_photos.
- **Скорость**: сравнение всех пар лиц — O(N1·N2). При 1000 фото × 1000 → 1M сравнений, что неприемлемо. Ограничение `max_comparisons` решает проблему, но может пропустить совпадения.
- **Качество распознавания**: зависит от моделей (dlib/MediaPipe). Плохое освещение, поворот, маска — снижают точность.
- **Зависимость от наличия метаданных**: `identical_photos` требует ID фото или полных метаданных; если API возвращает только URL без ID, сравнение по метаданным невозможно.
- **Временные файлы**: скачивание фото создаёт файлы на диске; нужно чистить после использования.

## 10. Возможные улучшения
- **Пакетная обработка лиц**: вычислять encodings для всех фото один раз, кешировать.
- **Использовать хеши изображений** (perceptual hash, pHash) вместо метаданных для identical_photos.
- **Учитывать не только ID, но и CRC32 содержимого** фото (если доступно).
- **Взвешивание по качеству фото**: более высокий вес для frontal faces, высокого разрешения.
- **Параллелизм**: многопоточное сравнение фото (ThreadPoolExecutor).
- **Кеширование encodings** на диск (pickle) для повторных вызовов.

## 11. Производительность
- Сравнение аватаров: O(1)
- `compare_all_photos` с `max_comparisons=300`: O(300) вызовов face_recognition → 1-2 сек.
- `compare_photo_collections`: O(N1+N2) для построения set'ов.
- Память: загрузка изображений в память (до 1MB каждое).

## 12. Тестирование
```python
# Тест 1: идентичные фото
assert vm.compare_photo_collections(
    [{'id': 1, 'date': 100, 'likes': {'count': 5}, 'comments': {'count': 1}}],
    [{'id': 1, 'date': 100, 'likes': {'count': 5}, 'comments': {'count': 1}}]
)['identical_photos_count'] == 1

# Тест 2: activity_similarity
ph1 = [{'likes': {'count': 10}, 'comments': {'count': 2}}]
ph2 = [{'likes': {'count': 10}, 'comments': {'count': 2}}]
assert vm.compare_photo_collections(ph1, ph2)['activity_similarity'] == 1.0
```

## 13. Отладка
Модуль печатает в консоль (через `print`):
- Процесс сравнения аватаров
- Количество сравнений всех фото
- Максимальное сходство
- Количество идентичных фото и activity_similarity

В продакшене заменить на `logging.debug`.
