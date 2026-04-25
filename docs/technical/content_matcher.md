# Content Matcher — модуль анализа текстового контента профилей ВКонтакте

## 1. Назначение
Модуль `ContentMatcher` сравнивает текстовые поля профилей ВКонтакте (статус, о себе, интересы, любимая музыка, фильмы, книги, игры, цитаты) с целью оценки сходства интересов, стиля письма и личностных маркеров. Может выявлять совпадения по стилистике и контенту, что дополнительно усиливает/ослабляет общую вероятность совпадения профилей.

**Вход:** два профиля (Dict с текстовыми полями)  
**Выход:** `content_score` ∈ [0, 1] + детали (общие интересы, стилистическое сходство, personal markers)

## 2. Архитектурные принципы
- **Модульность**: разделён на извлечение интересов (`extract_interests`), извлечение фич текста (`extract_text_features`), сравнение интересов (`compare_interests`) и полный анализ (`analyze`).
- **Статистический подход**: использует bag-of-words, Jaccard index, простые статистики текста.
- **Языковая независимость**: правила извлечения интересов работают для любого языка (разделители `[,;]`), но персональные маркеры заточены под русский.
- **Кеширование**: `lru_cache` на `extract_interests` для ускорения повторных вызовов с одинаковыми профилями.

## 3. Логика функционирования

### 3.1 Извлечение интересов (`extract_interests`)
1. Для профиля собираются поля: `activities`, `interests`, `music`, `movies`, `books`, `games`, `quotes`.
2. Для каждого поля:
   - Если значение существует и не пустое → привести к строке.
   - Разбить на отдельные элементы по разделителям `[,;]`.
   - Удалить пробелы, отфильтровать элементы короче 3 символов.
   - Добавить в `set` интересов (уникальные).
3. Возвращается `Set[str]` интересов профиля.

### 3.2 Извлечение фич текста (`_extract_text_features`)
Принимает строку `text` (например, статус или «о себе») и возвращает статистику:
- `word_count`, `char_count`
- `avg_word_length` (средняя длина слова)
- `uppercase_ratio` (доля заглавных букв в тексте)
- `punctuation_ratio` (доля знаков препинания)
- `emoji_count`, `emoji_types` (список категорий эмодзи)
- `sentence_count`, `avg_sentence_length`
- `personal_markers`: Counter по категориям (formal, informal, age_indicators, gender_indicators, professional_terms)

**Алгоритм**:
- Разбиение на слова: `text.split()`
- Подсчёт заглавных: `sum(1 for c in text if c.isupper()) / len(text)`
- Пунктуация: вхождение в строку `'.,!?;:'`
- Эмодзи: регулярное выражение `self.emoji_pattern` (unicode ranges).
- Предложения: `re.split(r'[.!?]+', text)`
- Персональные маркеры: для каждой категории `PERSONAL_MARKERS` подсчитать, сколько слов текста совпадает с маркерами.

### 3.3 Сравнение интересов (`compare_interests`)
1. `interests1 = extract_interests(profile1)`
2. `interests2 = extract_interests(profile2)`
3. `common = interests1 ∩ interests2`
4. `union = interests1 ∪ interests2`
5. `interest_overlap = len(common) / len(union)` (Jaccard)
6. Возвращает `{'common_interests': list(common), 'interest_overlap': float, 'score': float}`

### 3.4 Полный анализ (`analyze`)
Вызывается из `ProfileComparer._analyze_content`.
1. Извлекает тексты из профиля (`_combine_text_fields`): объединяет `status`, `about`, `activities`, `interests` (текстовые поля) в одну строку для стилистики.
2. Для каждого профиля вычисляет `features = extract_text_features(combined_text)`.
3. Сравнивает интересы через `compare_interests` → `interest_similarity`.
4. Сравнивает стили:
   - `style_similarity` = 1 - нормализованное расстояние между векторами фич.
   - Простейший вариант: cosinusная схожесть между векторами `[avg_word_length, uppercase_ratio, punctuation_ratio, avg_sentence_length]` + `personal_markers` (Jaccard).
5. Комбинирует: `content_score = (interest_similarity * 0.6) + (style_similarity * 0.4)`
6. Интерпретация:
   - ≥0.7: "Высокое сходство контента"
   - ≥0.4: "Умеренное сходство контента"
   - иначе: "Контент различается"

## 4. Рабочий процесс (workflow)
```
analyze(p1, p2)  # вызывается из ProfileComparer._analyze_content
│
├─► interests1 = extract_interests(p1)
├─► interests2 = extract_interests(p2)
│   └─► Для каждого поля из INTEREST_FIELDS:
│        если поле есть и не пусто → разбить по [,;] → добавить в set
│
├─► common = interests1 ∩ interests2
├─► union = interests1 ∪ interests2
├─► interest_overlap = |common| / |union|  (Jaccard)
│
├─► text1 = _combine_text_fields(p1)  # конкатенация status+about+...
├─► text2 = _combine_text_fields(p2)
│
├─► features1 = extract_text_features(text1)
├─► features2 = extract_text_features(text2)
│
├─► style_similarity = _compare_style(features1, features2)
│   └─► vector1 = [avg_word_length, uppercase_ratio, punctuation_ratio, avg_sentence_len]
│       + one-hot для personal_markers categories
│       -> cosine_similarity(vector1, vector2)
│
├─► content_score = interest_overlap * 0.6 + style_similarity * 0.4
│
└─► interpretation = {
        'common_interests': list(common),
        'interest_overlap': interest_overlap,
        'style_similarity': style_similarity,
        'score': content_score,
        'has_data': bool(interests1 и interests2),
        'interpretation': "Высокое/Умеренное/Низкое сходство контента"
    }
```

## 5. Технические механизмы

### Извлечение интересов
```python
def extract_interests(self, profile_data: Dict) -> Set[str]:
    interests = set()
    for field in self.INTEREST_FIELDS:
        if field in profile_data and profile_data[field]:
            value = profile_data[field]
            if not isinstance(value, str):
                value = str(value)
            items = re.split(r'[,;]', value.lower())
            for item in items:
                cleaned = item.strip()
                if len(cleaned) > 2:
                    interests.add(cleaned)
    return interests
```

### Статистика текста
- Эмодзи: `self.emoji_pattern.findall(text)` → подсчёт.
- Персональные маркеры: `PERSONAL_MARKERS` — словарь категорий → списка маркеров. Для каждой категории: `sum(1 for m in markers if m in text_lower)`.

### Сравнение стиля
```python
def _compare_style(self, features1, features2):
    # numerical features
    vec1 = np.array([features1['avg_word_length'], features1['uppercase_ratio'],
                     features1['punctuation_ratio'], features1['avg_sentence_length']])
    vec2 = np.array([...])
    num_sim = 1 - np.linalg.norm(vec1 - vec2) / (np.linalg.norm(vec1) + np.linalg.norm(vec2) + 1e-9)
    # personal markers: Jaccard
    markers1 = set(features1['personal_markers'].keys())
    markers2 = set(features2['personal_markers'].keys())
    marker_sim = len(markers1 & markers2) / len(markers1 | markers2) if markers1 | markers2 else 0
    return (num_sim * 0.6 + marker_sim * 0.4)
```
(В текущей реализации могут быть упрощения, но общий принцип сохраняется.)

## 6. Входные/выходные данные
- **Вход**: `profile1: Dict`, `profile2: Dict`. Ожидаемые ключи: `status`, `about`, `activities`, `interests`, `music`, `movies`, `books`, `games`, `quotes` (все optional).
- **Выход**:
```python
{
    'score': float,                 # 0..1 content_score
    'has_data': bool,
    'common_interests': List[str],
    'interest_overlap': float,      # 0..1
    'style_similarity': float,      # 0..1
    'interpretation': str
}
```

## 7. Взаимодействие с другими модулями
- **ProfileComparer**: вызывается из `_analyze_content`, вес 15%.
- **Utils**: не используется напрямую.
- **Config**: нет зависимостей.

## 8. Пример использования
```python
from src.matchers.content_matcher import ContentMatcher

cm = ContentMatcher()
p1 = {'interests': 'книги, музыка, фильмы', 'music': 'рок, классика'}
p2 = {'interests': 'музыка, кино, литература', 'books': 'научная фантастика'}

result = cm.analyze(p1, p2)
print(result['common_interests'])  # ['музыка'] (после нормализации)
print(result['score'])  # ~0.35
```

## 9. Ограничения
- **Язык маркеров**: `PERSONAL_MARKERS` составлен для русского языка; для других языков может не работать.
- **Простота сравнения стиля**: используется базовые статистики, без NLP (лемматизация, стемминг). Точность низкая.
- **Нет весов для разных типов контента**: `status` и `books` weigh одинаково, хотя `books` может быть более информативным.
- **Разделители интересов** только `[,;]`. Если пользователь разделяет интересы другими символами (слэш, тире), они не разобьются.
- **Нет обработки stopwords**: в `personal_markers` уже отобранные слова, но в интересах stopwords не удаляются, что можетinflate Jaccard.
- **Требует полного текста**: если поля пустые, `has_data=False` → score=0.

## 10. Возможные улучшения
- **Embeddings**: использовать pre-trained word2vec/fasttext для векторизации текста и косинусного расстояния.
- **TF-IDF** + косинус для стиля.
- **Расширить `PERSONAL_MARKERS`** на другие языки.
- **Учесть тематику** через LDA или тематическое моделирование.
- **Вес полей**: `interests` и `music` важнее `quotes`; можно задать веса.
- **Обработка смайликов и эмодзи**: текущий `emoji_pattern` покрывает основные, но может не хватать редких.

## 11. Производительность
- `extract_interests`: O(total_chars) — быстро.
- `extract_text_features`: O(len(text)) — один проход по символам.
- `compare_interests`: O(|set1| + |set2|) — быстро.
- Полный анализ: O(N) где N — общая длина текстов.

## 12. Тестирование
```python
cm = ContentMatcher()
p_empty = {}
p1 = {'interests': 'книги, музыка, фильмы'}
p2 = {'interests': 'музыка, кино, литература'}
res = cm.analyze(p1, p2)
assert res['score'] >= 0 and res['score'] <= 1
assert 'музыка' in res['common_interests']
```

## 13. Отладка
При `debug=True` в `analyze` выводятся:
- Извлечённые интересы (set)
- Статистики текстов (средняя длина слова, uppercase_ratio)
- personal_markers counts
