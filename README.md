# VК Identity Checker — Система идентификации и сравнения профилей ВКонтакте

## 📋 О проекте

**VК Identity Checker** — это интеллектуальная система для глубокого сравнения профилей ВКонтакте. Система анализирует множество факторов и вычисляет итоговую вероятность совпадения (0–100%). Designed для обнаружения дубликатов, подтверждения личности и анализа социальных связей.

---

## 🎯 Ключевые возможности

### 1. Сравнение имён (`name_matcher.py`)
- Нормализация: удаление пунктуации, регистронезависимость, поддержка кириллицы/латиницы
- Метрики:
  - Точное совпадение
  - Fuzzy ratio (difflib)
  - **Jaccard similarity** на уровне символов
  - Расстояние Левенштейна
  - Фонетика: Soundex, Metaphone
  - Вариации имён (Ксюша → Ксения), транслитерация (Kate → Кейт)
- Динамический пороговый расчет итогового балла

### 2. Геолокация (`geo_matcher.py`)
- **Семантическое сопоставление** городов-синонимов ("СПб" ↔ "Санкт-Петербург" ↔ "Питер")
- Нормализация: "г. Москва" → "Москва"
- Точное совпадение города/страны
- Поддержка координат для ~300 городов РФ/СНГ (`CITY_COORDS`)
- Расчёт расстояния Хаверасайна

### 3. Социально-географический анализ (`social_geo_analyzer.py`) ✨ новый
Географическая структура friend-сети:
- **Геокодирование** друзей: город → (lat, lon)
- **Центроид** сети (средние координаты)
- **Расстояние** между центроидами двух профилей
- **Плотность пересечения**:
  - `overlap_1_in_2`: % друзей профиля1 в радиусе R от центроида профиля2
  - `mutual_overlap`: min(overlap_1_in_2, overlap_2_in_1) — симметричная метрика
- **Адаптивный радиус**: `R = 100 км + distance × 0.5` (макс 300 км)
- **Оценка схожести гео-кластеров**: комбинация расстояния и плотности с порогами:
  - Если расстояние <20 км и overlap <0.1 → минимальный балл (аномалия)
  - При overlap ≥0.5 → высокий балл, независимо от расстояния

### 4. Анализ друзей (`friends_matcher.py`)
- Количество общих друзей
- **Коэффициент Жаккара** по ID друзей
- Бонус за большое количество общих
- Штраф за сильно разные размеры списков

### 5. Визуальное сравнение (`visual_matcher.py`)
- Сравнение аватаров (face_recognition)
- Сравнение всех фотографий (парный поиск, до 300 сравнений)
- Анализ коллекций (метаданные):
  - `identical_photos_count` — полностью совпадающие фото (id, дата, лайки)
  - `activity_similarity` — схожесть активности (лайки/комментарии)
- **Автоматический бонус** за множество идентичных фото:
  - ≥10 фото → `visual_score ≥ 0.8`
  - ≥5 фото → `≥0.6`
  - ≥3 фото → `≥0.5`

### 6. Контент (`content_matcher.py`)
- Извлечение интересов из полей: `activities`, `interests`, `music`, `movies`, `books`, `games`, `quotes`
- Сравнение интересов (Jaccard)
- Анализ стиля текстов (формальность, эмоциональность)
- Персональные маркеры (словия-указатели на возраст/пол/профессию)

### 7. Демография (`demographics_matcher.py`)
- Дата рождения, пол, семейное положение
- Образование (университет, факультет)
- Работа (компания, должность)
- Родной город

---

## 🏗 Архитектура

```
project/
├── src/
│   ├── matchers/           # Модули сравнения
│   │   ├── name_matcher.py
│   │   ├── geo_matcher.py
│   │   ├── friends_matcher.py
│   │   ├── social_geo_analyzer.py   ✨
│   │   ├── visual_matcher.py
│   │   ├── content_matcher.py
│   │   ├── demographics_matcher.py
│   │   ├── profile_comparer.py      # Оркестратор
│   │   └── __init__.py
│   ├── core/               # Ядро (CLI)
│   ├── handlers/           # Обработчики VK данных
│   ├── utils/              # Конфиг, логгер, вспомогательные
│   └── vk_api/             # Клиент API ВК
├── web/
│   ├── app.py              # Flask приложение
│   ├── requirements.txt
│   └── templates/          # HTML шаблоны (Bootstrap 4)
├── README.md
├── CHANGELOG.md
└── install_deps.bat
```

### Веса факторов (по умолчанию)

| Фактор | Вес | Описание |
|--------|-----|---------|
| Имя | 15% | full name similarity |
| Фотографии | 25% | face + identical photos |
| Друзья | 20% | common friends + Jaccard |
| Гео соцсетей | **7%** | centroid distance + overlap |
| Геолокация (профиль) | 8% | city + country match |
| Контент | 15% | interests + writing style |
| Демография | 10% | birth date, sex, edu, work |
| **Σ** | **100%** | |

Веса можно переопределить при создании `ProfileComparer(custom_weights={...})`.

---

## 🚀 Установка и запуск

### Требования
- Python 3.8–3.12
- Зависимости: `pip install -r web/requirements.txt`

### Быстрый старт (веб-интерфейс)

```bash
# Клонировать репозиторий
git clone <repo_url>
cd vk-identity-checker

# Установить зависимости
pip install -r web/requirements.txt

# Запустить Flask сервер
python web/app.py
# Сервер стартует на http://localhost:5000
```

### CLI режим

```bash
# Подготовить JSON-файлы с данными профилей
python -m src.core.run \
  --profile1 data/profile1.json \
  --profile2 data/profile2.json \
  [--friends1 data/friends1.json] \
  [--photos1 data/photos1.json]
```

### Программный API

```python
from src.matchers.profile_comparer import ProfileComparer

comparer = ProfileComparer()

result = comparer.compare_profiles(
    profile1, profile2,
    friends1_data=friends1,
    friends2_data=friends2,
    photos1_data=photos1,
    photos2_data=photos2
)

print(f"Вероятность: {result['final']['percentage']}%")
print(result['final']['interpretation'])
for factor, data in result['analysis'].items():
    print(f"  {factor}: {data.get('score', 0):.1%}")
```

---

## 📡 API Endpoints (Flask)

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/` | Главная страница (форма ввода ID профилей) |
| GET/POST | `/parse` | Парсинг профиля по ID/ссылке (асинхронный) |
| GET | `/parse/progress/<session_id>` | Прогресс парсинга (JSON) |
| GET | `/parse/result/<session_id>` | Результат парсинга (JSON) |
| GET/POST | `/compare` | Страница сравнения двух профилей |
| GET | `/comparison/<comparison_id>` | Детальный отчёт по сравнению |
| GET | `/profiles` | Список сохранённых профилей |
| GET | `/profile/<path:profile_path>` | Просмотр одного профиля |
| GET | `/photos/<path:filename>` | Просмотр фото |
| GET | `/static/photos/<path:profile>/<path:filename>` | Статические фото |

Пример запроса (cURL):
```bash
# Запустить сравнение (POST form)
curl -X POST http://localhost:5000/compare \
  -F "profile1_id=12345" \
  -F "profile2_id=67890"
```

---

## ⚙️ Конфигурация

### Переменные окружения
- `FLASK_ENV=development` — режим отладки
- `VK_TOKEN` — токен доступа ВК (если используется API)

### Настройки весов
```python
from src.matchers.profile_comparer import ProfileComparer

custom_weights = {
    'name': 0.20,
    'visual': 0.30,
    'friends': 0.15,
    'social_geo': 0.10,
    'geolocation': 0.05,
    'content': 0.10,
    'demographics': 0.10,
}
comparer = ProfileComparer(custom_weights=custom_weights)
```

### Пределы и параметры
- `MAX_COMPARISONS` в `config.py` — макс. кол-во пар фото для сравнения (по умолчанию 300)
- `BASE_RADIUS_KM`, `MAX_RADIUS_KM`, `DISTANCE_FACTOR` в `social_geo_analyzer.py` — настройки адаптивного радиуса

---

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest tests/

# Конкретный модуль
pytest tests/test_name_matcher.py

# Пайплайн на тестовых данных
python -m src.core.run --demo
```

---

## ⚠️ Ограничения и примечания

1. **Геокодирование**: работает только для городов из `CITY_COORDS` (~300 городов РФ/СНГ). Остальные города не будут распознаны → `None`.
2. **Распознавание лиц**: требует, чтобы на фото были видны лица. Не ограничено: может быть медленным на больших коллекциях.
3. **VK API**: требует токен с правами `friends,photos,status,about,interests`. Лимиты запросов: 3/сек.
4. **Точность**: система даёт **вероятность**, а не гарантию. Пороги можно настроить под задачу.
5. **Персональные данные**: использование должно соответствовать политике ВК и законодательству о защите ПДн.

---

## 📊 Алгоритм итоговой оценки

1. Каждый модуль возвращает `score` ∈ [0, 1] и `has_data`.
2. Недостающие данные → score = 0,但 confidence снижается.
3. Взвешенная сумма: `final = Σ(score_i × weight_i)`
4. Проценты: `percentage = round(final × 100, 1)`
5. Интерпретация на основе `percentage` и `confidence`.

---

## 📖 Документация модулей

- `name_matcher.py`: нормализация, Jaccard, Levenshtein, Soundex/Metaphone, вариации, транслитерация.
- `geo_matcher.py`: словарь синонимов городов, нормализация, расстояние Хаверасайна.
- `social_geo_analyzer.py`: геокодирование друзей, центроид, адаптивный радиус, плотность пересечения, интерпретация.
- `friends_matcher.py`: Jaccard по ID, бонусы/штрафы за размеры списков.
- `visual_matcher.py`: face_recognition (dlib/MediaPipe), сравнение коллекций, activity_similarity.
- `content_matcher.py`: извлечение интересов, стилистика, маркеры.
- `demographics_matcher.py`: сравнение Demo-полей, карьерный профиль.
- `profile_comparer.py`: агрегация, взвешивание, итоговая оценка.

---

## 🤝 Вклад

Пулл-реквесты приветствуются. Основные направления:
- Расширение `CITY_COORDS` (добавление городов)
- Улучшение алгоритмов (например, word embeddings для имён)
- Оптимизация скорость (кеширование, параллелизм)
- Тесты (pytest)

---

## 📄 Лицензия

Использование только в образовательных/исследовательских целях. Запрещено для массового сбора данных без согласия пользователей.

---
