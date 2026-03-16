# VK Parser - Техническая документация

## Содержание

1. [Введение](#введение)
2. [Архитектура](#архитектура)
3. [Конфигурация](#конфигурация)
4. [API компоненты](#api-компоненты)
5. [Система идентификации](#система-идентификации)
6. [Алгоритмы сравнения](#алгоритмы-сравнения)
7. [Обработка ошибок](#обработка-ошибок)
8. [Безопасность](#безопасность)
9. [Тестирование](#тестирование)
10. [Развертывание](#развертывание)

---

## Введение

VK Parser - это комплексная система для анализа профилей ВКонтакте, состоящая из двух основных компонентов:

1. **Парсер профилей** - сбор и сохранение данных о пользователях
2. **Система идентификации** - сравнение профилей для определения совпадений

### Основные характеристики

- **Язык**: Python 3.8+
- **API**: VK API v5.131
- **Зависимости**:Минимальные (только requests)
- **Лицензия**: MIT

---

## Архитектура

### Диаграмма компонентов

```
┌─────────────────────────────────────────────────────────────────┐
│                         VK Parser                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐  │
│  │   main.py    │────▶│  vk_api_     │────▶│    output    │  │
│  │ (Entry Point)│     │   client.py  │     │  generators  │  │
│  └──────────────┘     └──────────────┘     └──────────────┘  │
│         │                     │                     │           │
│         ▼                     ▼                     ▼           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Core Modules                         │   │
│  │  • photo_handler.py    • friends_handler.py           │   │
│  │  • data_preparer.py    • file_exporters.py             │   │
│  │  • html_generator.py   • utils.py                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Identity Comparison System                │   │
│  │  • identity_checker.py    • profile_comparer.py        │   │
│  │  • name_matcher.py       • geo_matcher.py              │   │
│  │  • friends_matcher.py    • content_matcher.py          │   │
│  │  • demographics_matcher • visual_matcher.py            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            Face Recognition (Optional)                 │   │
│  │  • face_recognition_module.py                          │   │
│  │  • opencv_face_recognition.py                          │   │
│  │  • mediapipe_face_recognition.py                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Поток данных

1. Пользователь запускает `main.py` или `run_identity_checker.py`
2. `vk_api_client.py` выполняет запросы к VK API
3. Данные обрабатываются специализированными модулями
4. Результаты сохраняются в файлы или используются для сравнения

---

## Конфигурация

### Файл config.py

```python
# VK API
VK_TOKEN = os.environ.get('VK_TOKEN')  # Приоритет: env > token.txt > default
API_VERSION = '5.131'

# Лимиты
MAX_PHOTOS_PER_REQUEST = 200
MAX_FRIENDS_PER_REQUEST = 5000
RESULTS_FOLDER = "vk_results"

# Настройки сети
REQUEST_TIMEOUT = 10          # Таймаут запроса (сек)
MAX_RETRIES = 3              # Макс. попыток при ошибке
RETRY_DELAY = 1              # Задержка между попытками (сек)

# Логирование
LOG_LEVEL = 'INFO'           # DEBUG, INFO, WARNING, ERROR
LOG_FILE = 'vk_parser.log'
```

### Настройка через переменные окружения

```bash
export VK_TOKEN="ваш_токен"
export LOG_LEVEL="DEBUG"
export LOG_FILE="/var/log/vk_parser.log"
```

---

## API компоненты

### VKApiClient

Основной класс для работы с VK API.

**Основные методы:**

```python
# Инициализация
api = VKApiClient(token="токен")

# Получение информации о пользователе
user = api.get_user_info("vk.com/id123456789")

# Разрешение short name в ID
user_id = api.resolve_screen_name("durov")
```

**Особенности:**
- Автоматические повторные попытки при ошибках сети
- Логирование всех запросов
- Обработка ошибок API (коды ошибок 5, 6, 18, 30)

### PhotoHandler

```python
handler = PhotoHandler(api_client)

# Получить все фотографии
photos = handler.get_all_photos(user_id)

# Скачать фотографии
downloaded = handler.download_photos(photos, save_dir, user_name)
```

### FriendsHandler

```python
handler = FriendsHandler(api_client)

# Получить всех друзей
friends = handler.get_all_friends(user_id)

# Проанализировать статистику (статический метод)
stats = FriendsHandler.analyze_friends_stats(friends_list)
```

---

## Система идентификации

### ProfileComparer

Главный класс для комплексного сравнения профилей.

```python
comparer = ProfileComparer()

result = comparer.compare_profiles(
    profile1_data,
    profile2_data,
    friends1_data=...,
    friends2_data=...,
    photos1_data=...,
    photos2_data=...
)
```

### Веса факторов

| Фактор | Вес | Описание |
|--------|-----|----------|
| Имя | 15% | Точное и нечеткое совпадение |
| Фото | 25% | Визуальное сравнение лиц |
| Друзья | 25% | Общие друзья и связи |
| Геолокация | 10% | Город, страна |
| Контент | 15% | Интересы, стиль |
| Демография | 10% | Возраст, образование |

### Формула расчета

```
final_score = Σ(weight_i × score_i) + bonuses
```

Бонусы начисляются за:
- Сильное совпадение по имени (>90%)
- Значительное пересечение друзей (>20%)
- Точное совпадение геолокации

---

## Алгоритмы сравнения

### NameMatcher

- Точное совпадение
- Нечеткое сопоставление (SequenceMatcher)
- Фонетический анализ (Soundex-like)
- Словарь вариаций русских имен

### GeoMatcher

- Нормализация названий городов
- Распознавание сокращений (Москва=МСК, СПб=Питер)
- Учет часовых поясов

### FriendsMatcher

- Коэффициент Жаккара
- Процент общих друзей
- Анализ "общих друзей"

### ContentMatcher

- Анализ интересов (пересечение множеств)
- Стиль написания (формальность, экспрессивность)
- Персональные маркеры

### DemographicsMatcher

- Сравнение дат рождения
- Образование и карьера
- Семейное положение

### VisualMatcher

- Сравнение аватарок профилей
- Интеграция с face_recognition/OpenCV/MediaPipe
- Fallback при отсутствии библиотек

---

## Обработка ошибок

### Типы ошибок

1. **Ошибки API**
   - Код 5: Недействительный токен
   - Код 6: Превышен лимит запросов
   - Код 18: Пользователь удален
   - Код 30: Профиль приватный

2. **Ошибки сети**
   - Таймаут
   - Потеря соединения

3. **Ошибки данных**
   - Отсутствующие поля
   - Неверный формат

### Стратегия обработки

- Повторные попытки (MAX_RETRIES)
- Логирование всех ошибок
-Graceful degradation при отсутствии optional библиотек

---

## Безопасность

### Рекомендации

1. **Хранение токена**
   - Использовать переменные окружения
   - Не commitить токен в репозиторий
   - Использовать `.gitignore`

2. **Ограничение доступа**
   - Не хранить персональные данные дольше необходимого
   - Использовать шифрование при передаче

3. **Правовые аспекты**
   - Соблюдать Terms of Service VK
   - Использовать только для легальных целей

---

## Тестирование

### Проверка синтаксиса

```bash
python -m py_compile main.py
python -m py_compile identity_checker.py
# и т.д.
```

### Тестирование API

```bash
python -c "from vk_api_client import VKApiClient; api = VKApiClient(); print(api.get_user_info('durov'))"
```

---

## Развертывание

### Локальное развертывание

```bash
# Клонирование
git clone <repo>
cd vk-parser

# Установка зависимостей
pip install -r requirements.txt

# Настройка токена
echo "ваш_токен" > token.txt

# Запуск
python main.py
```

### Docker (опционально)

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

---

## Глоссарий

| Термин | Описание |
|--------|----------|
| VK API | Программный интерфейс ВКонтакте |
| Screen name | Короткое имя пользователя (domain) |
| Face encoding | Вектор признаков лица (128 чисел) |
| Jaccard index | Коэффициент пересечения множеств |

---

## Ссылки

- [Документация VK API](https://vk.com/dev/manuals)
- [face_recognition](https://github.com/ageitgey/face_recognition)
- [OpenCV](https://docs.opencv.org/)
- [MediaPipe](https://google.github.io/mediapipe/)