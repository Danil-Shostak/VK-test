# Правила именования и стиля кода

## 1. Общие правила

### 1.1. Язык
- **Код**: английский (переменные, классы, функции, комментарии в коде)
- **Документация и комментарии для пользователей**: русский
- **Сообщения в консоль/лог**: русский (для понимания результатов)

### 1.2. Форматирование
- **Отступы**: 4 пробела (никаких табов)
- **Максимальная длина строки**: 100 символов
- **Пробелы**: вокруг операторов, после запятых, вокруг `=` в параметрах и присваиваниях
- **Пустые строки**: отделять логические блоки одной пустой строкой
- **Конец файла**: одна пустая строка

### 1.3. Кодировка
- UTF-8 без BOM

### 1.4. Импорты
- Группировать в порядке:
  1. Стандартная библиотека Python
  2. Внешние зависимости (pip)
  3. Локальные модули проекта
- Каждая группа отделена пустой строкой
- Импортировать конкретные классы/функции, а не `*`
```python
import re
import json
from pathlib import Path

import numpy as np
import requests

from src.utils.logger import get_logger
from src.matchers.name_matcher import NameMatcher
```

## 2. Именование

### 2.1. Классы (CapWords / CamelCase)
- Начинаются с заглавной буквы
- Каждое слово с заглавной
- Не использовать подчеркивания (кроме `_` для приватных членов)

```python
class NameMatcher:          # ✅ Верно
class name_matcher:         # ❌ Неверно
class Name_Matcher:         # ❌ Неверно

class HTTPResponse:         # ✅ Аббревиатуры в верхнем регистре
class HttpResponse:         # ❌ Не смешивайте регистр внутри слова
```

### 2.2. Функции и методы (snake_case)
- Все строчные буквы
- Слова разделяются нижним подчеркиванием
- Имена должны быть глаголами или глагольными оборотами

```python
def compare_names():        # ✅ Верно
    pass

def CompareNames():         # ❌ Неверно
    pass

def compareNames():         # ❌ Неверно
    pass
```

### 2.3. Переменные (snake_case)
- Все строчные буквы
- Слова разделяются нижним подчеркиванием
- Избегать однобуквенных имен (кроме счетчиков в циклах)
- Булевы переменные начинать с `is_`, `has_`, `can_`, `should_`

```python
user_id = 123               # ✅ Верно
userID = 123                # ❌ Неверно
userId = 123                # ❌ Неверно

has_data = False            # ✅ Верно
data_exists = False         # ❌ (has_ лучше передает смысл)

for i in range(10):         # ✅ i — допустимо в цикле
    pass
```

### 2.4. Константы (SCREAMING_SNAKE_CASE)
- Все заглавные буквы
- Слова разделяются нижним подчеркиванием
- Объявлять на уровне модуля или в верхней части класса

```python
MAX_RETRIES = 3             # ✅ Верно
MAX_RETRIES = 3             # ✅ Верно
max_retries = 3             # ❌ Неверно
```

### 2.5. Приватные члены
- Один ведущий подчеркивание
- Использовать только внутри класса (конвенция, не защита)

```python
class Matcher:
    def __init__(self):
        self._cache = {}     # ✅ Верно
        self.__private = 0   # ❌ Избегать двойного подчеркивания (name mangling)
```

### 2.6. Пакеты и модули
- Имена строчными буквами
- Можно использовать короткие слова или аббревиатуры без подчеркивания, если они читаемы

```python
src/matchers/name_matcher.py  # ✅ Верно
src/matchers/nameMatcher.py   # ❌ Неверно
src/matchers/NameMatcher.py   # ❌ Неверно
```

## 3. Стиль кода

### 3.1. Строки
- Использовать одинарные кавычки `'` по умолчанию
- Двойные `'` использовать, если внутри одинарные
- Тройные кавычки `'''` или `"""` — только для docstring

```python
name = 'Иван'                # ✅ Верно
message = "Don't panic"      # ✅ Верно
```

### 3.2. Форматирование строк
- Предпочитать f-строки (Python 3.6+)
- Избегать `%` и `.format()` без необходимости

```python
name = 'Иван'
age = 25
message = f'{name} ({age} лет)'  # ✅ Верно
message = '{} ({} лет)'.format(name, age)  # ❌ Избегать
```

### 3.3. Условия и циклы

#### Сравнения с None
```python
if value is None:            # ✅ Верно
    pass

if value == None:            # ❌ Неверно
    pass
```

#### Пустые контейнеры
```python
if not items:                # ✅ Верно (предпочтительно)
    pass

if len(items) == 0:          # ❌ Неверно
    pass
```

#### Списки и множества
```python
# ✅ Верно — list comprehension
squares = [x**2 for x in range(10) if x % 2 == 0]

# ❌ Неверно — цикл с append
squares = []
for x in range(10):
    if x % 2 == 0:
        squares.append(x**2)
```

#### Циклы
```python
for i, item in enumerate(items):  # ✅ Верно — если нужен индекс
    process(i, item)

for item in items:                 # ✅ Верно
    process(item)
```

### 3.4. Функции

#### Документация (docstring)
- Все публичные функции и классы должны иметь docstring
- Формат: Google style или NumPy style (выберите один)
- Первая строка — краткое описание
- Пустая строка после первой строки
- Разделы: Args, Returns, Raises, Examples

```python
def compare_names(name1: str, name2: str) -> float:
    """Сравнивает два имени с использованием множества метрик.

    Выполняет нормализацию, проверку точного совпадения,
    фонетическое сравнение и расчет Jaccard индекса.

    Args:
        name1: Первое имя (строка)
        name2: Второе имя (строка)

    Returns:
        float: Оценка сходства в диапазоне [0, 1].
              1.0 — полное совпадение, 0.0 — различаются.

    Raises:
        ValueError: Если одна из строк пустая.

    Examples:
        >>> compare_names('Иван', 'Иван')
        1.0
        >>> compare_names('Иван', 'Петр')
        0.15
    """
    pass
```

#### Типизация (Type hints)
- Обязательно для публичных API
- Указывать для аргументов и возвращаемого значения
- Использовать `Optional`, `List`, `Dict`, `Tuple` из `typing`

```python
from typing import List, Dict, Optional, Tuple

def process_items(items: List[str], 
                  config: Optional[Dict] = None) -> Tuple[str, int]:
    """Обрабатывает список элементов."""
    pass
```

#### Длина функций
- Не более 50 строк кода (включая docstring)
- Если функция длиннее — разбить на подфункции
- Одна функция — одна ответственность

#### Аргументы функций
- Не более 5 позиционных аргументов
- Если больше — использовать `**kwargs` или объект конфигурации
- Избегать аргументов со значениями по умолчанию, изменяемых типов (списки, словари)

```python
# ❌ Неверно — мутабельный аргумент по умолчанию
def add_item(item, items=[]):
    items.append(item)
    return items

# ✅ Верно
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

### 3.5. Классы

```python
class NameMatcher:
    """Модуль сравнения имен и фамилий.

    Атрибуты:
        cache: Кэш результатов нормализации.
    """

    DEFAULT_THRESHOLD: float = 0.5

    def __init__(self, threshold: Optional[float] = None):
        """Инициализация матчера.

        Args:
            threshold: Порог сходства (опционально).
        """
        self.threshold = threshold or self.DEFAULT_THRESHOLD

    def compare_names(self, name1: str, name2: str) -> float:
        """Сравнивает два имени."""
        pass
```

### 3.6. Исключения

- Создавать собственные исключения при необходимости
- Не использовать `except:` без указания типа
- Логировать исключения перед пробросом выше

```python
class MatcherError(Exception):
    """Базовое исключение для ошибок матчеров."""
    pass

try:
    process_data(data)
except ValueError as e:
    logger.error(f"Ошибка валидации: {e}")
    raise MatcherError("Не удалось обработать данные") from e
```

## 4. Оформление

### 4.1. Комментарии
- Комментировать «почему», а не «что» (код должен быть самодокументированным)
- Избегать очевидных комментариев

```python
# ❌ Неверно — очевидно
x = x + 1  # увеличиваем x на 1

# ✅ Верно — объясняем почему
x = x + 1  # коррекция смещения после нормализации
```

### 4.2. TODO-комментарии
Разрешены, но с указанием автора и даты:
```python
# TODO(ivanov, 2024-03-01): реализовать кэширование
```

### 4.3. Отладочный код
- Удалять `print()` перед коммитом
- Использовать `logging.debug()` вместо `print()`
- Для временной отладки: `# debug:` перед строкой

## 5. Тестирование

### 5.1. Структура тестов
- Файлы: `tests/test_<module>.py`
- Классы: `Test<Class>`, `Test<Class>_<feature>`
- Методы: `test_<behavior>_<condition>_returns_<result>`

### 5.2. Пример
```python
import pytest
from src.matchers.name_matcher import NameMatcher


class TestNameMatcher:
    """Тесты для NameMatcher."""

    def test_compare_names_identical_returns_one(self):
        """Идентичные имена возвращают 1.0."""
        matcher = NameMatcher()
        result = matcher.compare_names('Иван', 'Иван')
        assert result == 1.0

    def test_compare_names_empty_raises_error(self):
        """Пустое имя вызывает ошибку."""
        matcher = NameMatcher()
        with pytest.raises(ValueError):
            matcher.compare_names('', 'Иван')
```

## 6. Версионирование и коммиты

### 6.1. Сообщения коммитов
Формат: `<тип>(<область>): <описание>`

Типы:
- `feat` — новая функциональность
- `fix` — исправление ошибки
- `refactor` — рефакторинг без изменения поведения
- `docs` — изменения в документации
- `test` — добавление/изменение тестов
- `chore` — обслуживание проекта

Примеры:
```
feat(name_matcher): добавлена транслитерация
fix(geo_matcher): исправлен расчет расстояния
refactor(profile_comparer): вынесены веса в константы
docs(readme): обновлен раздел установки
```

### 6.2. Ветки
- `main` — стабильная версия
- `develop` — текущая разработка
- `feature/<имя>` — новая функциональность
- `fix/<имя>` — исправления

## 7. Инструменты и автоматизация

### 7.1. Линтеры
- `black` — автоформатирование
- `isort` — сортировка импортов
- `flake8` — проверка стиля
- `mypy` — проверка типов

### 7.2. Pre-commit хуки
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
```

## 8. Шаблоны

### 8.1. Шаблон модуля
```python
"""Модуль <назначение>.

<Краткое описание функционала и архитектуры>
"""

from typing import Dict, List, Optional


class <ClassName>:
    """<Краткое описание класса.>

    <Подробности>
    """

    def __init__(self, ...):
        """Инициализация."""
        pass

    def main_method(self, ...) -> ...:
        """Основной метод."""
        pass
```

### 8.2. Шаблон теста
```python
"""Тесты для модуля <module>."""

import pytest
from src.<module> import <Class>


class Test<Class>:
    """Тесты для <Class>."""

    def test_<behavior>_<condition>_returns_<result>(self):
        """<Описание>."""
        # arrange
        # act
        # assert
```

## 9. Запреты строгие

- [ ] Не использовать `print()` в продакшен-коде
- [ ] Не использовать `*` в импортах
- [ ] Не использовать `except:` без указания типа
- [ ] Не изменять глобальные переменные из функций
- [ ] Не писать комментарии на транслите
- [ ] Не превышать 100 символов в строке без необходимости