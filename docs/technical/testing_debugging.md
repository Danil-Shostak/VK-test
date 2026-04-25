# Тестирование и дебаггинг

## 1. Обзор стратегии тестирования

Проект использует **многоуровневое тестирование**:
- **Unit-тесты** — изолированное тестирование матчеров
- **Integration-тесты** — тестирование `ProfileComparer` с мокнутыми матчерами
- **End-to-end тесты** — полный цикл: VK API → матчеры → результат

### 1.1. Инструменты
- `pytest` — фреймворк для запуска тестов
- `pytest-cov` — покрытие кода
- `pytest-mock` — мокирование зависимостей
- `requests-mock` — мокирование HTTP-запросов к VK API

## 2. Запуск тестов

### 2.1. Подготовка окружения
```bash
# Установка зависимостей для тестов
pip install -r requirements-dev.txt

# requirements-dev.txt содержит:
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
requests-mock>=1.11.0
mypy>=1.0.0
black>=23.0.0
flake8>=6.0.0
```

### 2.2. Базовые команды
```bash
# Запуск всех тестов
pytest

# Запуск тестов с покрытием
pytest --cov=src --cov-report=html

# Запуск тестов для конкретного модуля
pytest tests/test_name_matcher.py

# Запуск тестов с подробным выводом
pytest -v

# Запуск тестов с остановкой на первой ошибке
pytest -x
```

### 2.3. Структура директории тестов
```
tests/
├── unit/
│   ├── test_name_matcher.py
│   ├── test_geo_matcher.py
│   ├── test_friends_matcher.py
│   ├── test_social_geo_analyzer.py
│   ├── test_visual_matcher.py
│   ├── test_content_matcher.py
│   ├── test_demographics_matcher.py
│   └── test_profile_comparer.py
├── integration/
│   └── test_full_pipeline.py
├── fixtures/
│   ├── vk_profiles.py
│   ├── friends_data.py
│   ├── photos_data.py
│   └── test_data.json
└── conftest.py
```

## 3. Покрытие кода

### 3.1. Текущие метрики (цели)

| Модуль | Целевое покрытие | Текущее |
|--------|------------------|---------|
| name_matcher | 90% | — |
| geo_matcher | 90% | — |
| friends_matcher | 85% | — |
| social_geo_analyzer | 85% | — |
| visual_matcher | 80% | — |
| content_matcher | 85% | — |
| demographics_matcher | 90% | — |
| profile_comparer | 95% | — |
| **Общее** | **88%** | — |

### 3.2. Генерация отчета
```bash
# HTML-отчет
pytest --cov=src --cov-report=html:coverage_html

# Консольный отчет
pytest --cov=src --cov-report=term-missing

# XML для CI (Jenkins, GitLab CI)
pytest --cov=src --cov-report=xml:coverage.xml
```

## 4. Фикстуры (Fixtures)

### 4.1. Стандартные профили

`tests/fixtures/vk_profiles.py`:
```python
import pytest


@pytest.fixture
def profile_ivan():
    """Тестовый профиль: Иван Петров, Москва."""
    return {
        'first_name': 'Иван',
        'last_name': 'Петров',
        'bdate': '15.03.1995',
        'sex': 2,
        'city': {'title': 'Москва'},
        'country': {'title': 'Россия'},
        'home_town': 'Москва',
        'photo_200': 'https://example.com/photo.jpg',
        'status': 'Программист',
        'about': 'Люблю Python и кошек',
        'interests': 'книги, музыка, программирование',
        'education': {
            'university': 'МГУ',
            'faculty': 'ВМК'
        },
        'career': [
            {'company': 'Яндекс', 'position': 'Инженер'}
        ]
    }


@pytest.fixture
def profile_ivan_duplicate():
    """Тот же профиль — для тестов идентичности."""
    return {
        'first_name': 'Иван',
        'last_name': 'Петров',
        'bdate': '15.03.1995',
        'sex': 2,
        'city': {'title': 'Москва'},
        'country': {'title': 'Россия'},
        'home_town': 'Москва'
    }


@pytest.fixture
def profile_petya():
    """Другой профиль: Пётр Иванов, СПб."""
    return {
        'first_name': 'Пётр',
        'last_name': 'Иванов',
        'bdate': '20.07.1990',
        'sex': 2,
        'city': {'title': 'Санкт-Петербург'},
        'country': {'title': 'Россия'},
        'home_town': 'Санкт-Петербург'
    }
```

### 4.2. Данные друзей

`tests/fixtures/friends_data.py`:
```python
import pytest


@pytest.fixture
def friends_overlap():
    """Друзья с пересечением."""
    friends1 = {
        'items': [
            {'id': 1, 'city': {'title': 'Москва'}},
            {'id': 2, 'city': {'title': 'Москва'}},
            {'id': 3, 'city': {'title': 'Санкт-Петербург'}}
        ]
    }
    friends2 = {
        'items': [
            {'id': 2, 'city': {'title': 'Москва'}},
            {'id': 3, 'city': {'title': 'Санкт-Петербург'}},
            {'id': 4, 'city': {'title': 'Новосибирск'}}
        ]
    }
    return friends1, friends2


@pytest.fixture
def friends_no_overlap():
    """Друзья без пересечений."""
    return (
        {'items': [{'id': 1}, {'id': 2}]},
        {'items': [{'id': 3}, {'id': 4}]}
    )
```

### 4.3. Фотографии

`tests/fixtures/photos_data.py`:
```python
import pytest


@pytest.fixture
def identical_photos():
    """Идентичные фотографии (один ID)."""
    return (
        [{'id': 1, 'date': 1000, 'likes': {'count': 10}, 'comments': {'count': 2}}],
        [{'id': 1, 'date': 1000, 'likes': {'count': 10}, 'comments': {'count': 2}}]
    )


@pytest.fixture
def different_photos():
    """Разные фотографии."""
    return (
        [{'id': 1, 'date': 1000}, {'id': 2, 'date': 2000}],
        [{'id': 3, 'date': 3000}, {'id': 4, 'date': 4000}]
    )
```

## 5. Примеры тестов

### 5.1. Unit-тест для NameMatcher

`tests/unit/test_name_matcher.py`:
```python
import pytest
from src.matchers.name_matcher import NameMatcher


class TestNameMatcher:
    """Тесты для NameMatcher."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.matcher = NameMatcher()

    def test_compare_names_identical(self):
        """Идентичные имена возвращают 1.0."""
        result = self.matcher.compare_names('Иван', 'Иван')
        assert result['final_score'] == 1.0
        assert result['exact_match'] is True

    def test_compare_names_case_insensitive(self):
        """Регистр не имеет значения."""
        result = self.matcher.compare_names('ИВАН', 'иван')
        assert result['final_score'] == 1.0

    def test_compare_names_transliteration(self):
        """Транслитерация работает."""
        result = self.matcher.compare_names('Katya', 'Катя')
        assert result['transliteration_match'] is True
        assert result['final_score'] > 0.8

    def test_compare_names_none(self):
        """None обрабатывается корректно."""
        result = self.matcher.compare_names(None, 'Иван')
        assert result['final_score'] == 0.0

    def test_compare_names_variation(self):
        """Вариации имён распознаются."""
        # "Саша" — вариант "Александр"
        result = self.matcher.compare_names('Саша', 'Александр')
        assert result['variation_match'] is True
        assert result['final_score'] >= 0.85

    def test_compare_names_empty_string(self):
        """Пустые строки не ломают систему."""
        result = self.matcher.compare_names('', '')
        assert result['final_score'] == 0.0
```

### 5.2. Unit-тест для ProfileComparer

`tests/unit/test_profile_comparer.py`:
```python
import pytest
from unittest.mock import MagicMock, patch
from src.matchers.profile_comparer import ProfileComparer


class TestProfileComparer:
    """Тесты для ProfileComparer."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.comparer = ProfileComparer()

    def test_compare_profiles_identical(self, profile_ivan, profile_ivan_duplicate):
        """Идентичные профили дают 100%."""
        result = self.comparer.compare_profiles(
            profile_ivan, profile_ivan_duplicate
        )
        assert result['final']['percentage'] == 100.0

    def test_compare_profiles_different(self, profile_ivan, profile_petya):
        """Разные профили дают < 50%."""
        result = self.comparer.compare_profiles(profile_ivan, profile_petya)
        assert result['final']['percentage'] <= 50

    def test_compare_profiles_missing_friends(self, profile_ivan, profile_petya):
        """Отсутствие данных друзей не ломает систему."""
        result = self.comparer.compare_profiles(
            profile_ivan, profile_petya, 
            friends1_data=None, friends2_data=None
        )
        assert 'analysis' in result
        assert result['analysis']['friends']['has_data'] is False

    @patch('src.matchers.profile_comparer.NameMatcher')
    def test_compare_profiles_with_mock(self, mock_name_matcher, 
                                         profile_ivan, profile_petya):
        """Мокаем NameMatcher для изоляции теста."""
        mock_instance = MagicMock()
        mock_instance.compare_names.return_value = {
            'final_score': 0.9, 'has_data': True
        }
        mock_name_matcher.return_value = mock_instance

        comparer = ProfileComparer()
        result = comparer.compare_profiles(profile_ivan, profile_petya)
        
        assert result['analysis']['name']['score'] == 0.9
```

### 5.3. Integration-тест

`tests/integration/test_full_pipeline.py`:
```python
import pytest
import requests_mock
from src.core.main import compare_two_profiles


class TestFullPipeline:
    """Тесты полного цикла."""

    def test_full_comparison_with_mocked_api(self, profile_ivan, profile_petya):
        """Полный цикл с моком VK API."""
        with requests_mock.Mocker() as m:
            # Мокаем API-вызовы
            m.get('https://api.vk.com/method/users.get',
                  json={'response': [{'first_name': 'Иван'}]})
            m.get('https://api.vk.com/method/friends.get',
                  json={'response': {'items': [1, 2, 3]}})

            result = compare_two_profiles(user_id1=1, user_id2=2)
            
            assert 'percentage' in result['final']
            assert result['final']['percentage'] >= 0
```

## 6. Дебаггинг

### 6.1. Логирование

Настройка логгера (`src/utils/logger.py`):
```python
import logging

def get_logger(name: str) -> logging.Logger:
    """Создает настроенный логгер."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    
    return logger

# Использование в коде
logger = get_logger(__name__)
logger.debug("Сравниваем профили...")
logger.info(f"Результат: {score}")
logger.warning("Нет данных о друзьях")
logger.error("Ошибка API", exc_info=True)
```

### 6.2. Точки останова (Debugging)

В VS Code добавьте `launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Tests",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/.venv/bin/pytest",
            "args": ["-xvs", "${file}"],
            "console": "integratedTerminal"
        },
        {
            "name": "Debug Main",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/src/core/main.py",
            "console": "integratedTerminal"
        }
    ]
}
```

### 6.3. Отладка в консоли

Вместо `print()` используйте `logging`:
```python
# ❌ Плохо
print(f"Score: {score}")

# ✅ Хорошо
logger.debug(f"Score: {score}")
```

Для временной отладки добавляйте `# TODO: удалить`:
```python
logger.debug(f"DEBUG: profile1={profile1}")  # TODO: удалить после исправления
```

### 6.4. Профилирование

Если тесты работают медленно:
```bash
# Установка
pip install line_profiler memory_profiler

# Профилирование строк
kernprof -l -v test_name_matcher.py
```

## 7. CI/CD Интеграция

### 7.1. GitHub Actions (.github/workflows/test.yml)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 src tests --count --max-line-length=100
    
    - name: Type checking with mypy
      run: |
        mypy src --ignore-missing-imports
    
    - name: Run tests with coverage
      run: |
        pytest --cov=src --cov-report=xml --cov-fail-under=80
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 7.2. GitLab CI (.gitlab-ci.yml)

```yaml
stages:
  - test
  - coverage

test:
  stage: test
  image: python:3.9
  script:
    - pip install -r requirements-dev.txt
    - pytest --cov=src
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

## 8. Метрики качества

### 8.1. Критерии приемки

- [ ] Покрытие кода ≥ 80%
- [ ] Все критические пути протестированы
- [ ] Нет падающих тестов на master
- [ ] Тесты выполняются < 2 минуты
- [ ] Нет известных security-уязвимостей

### 8.2. Инспекция кода перед коммитом

```bash
# Перед коммитом выполните:

# 1. Форматирование
black src/ tests/

# 2. Сортировка импортов
isort src/ tests/

# 3. Линтинг
flake8 src/ tests/

# 4. Проверка типов
mypy src/ --ignore-missing-imports

# 5. Тесты
pytest --tb=short
```

## 9. Типовые ошибки и их решение

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `ModuleNotFoundError` | Не установлены зависимости | `pip install -r requirements.txt` |
| `JSONDecodeError` | Некорректный ответ от VK API | Проверить токен, права доступа |
| `FaceRecognitionError` | Нет лиц на фото | Убедиться, что фото с лицами |
| `MemoryError` | Слишком много фото | Уменьшить `max_comparisons` |
| `KeyError: 'items'` | Неверный формат данных от API | Проверить структуру ответа VK API |

## 10. Документация по тестам

Каждый тест должен содержать:
- **Название**: описывает поведение и условия
- **Setup**: подготовка данных (фикстуры)
- **Action**: выполнение тестируемого кода
- **Assertion**: проверка ожидаемого результата
- **Teardown**: очистка (если нужно)

Пример хорошего названия:
- ✅ `test_compare_names_transliteration_returns_high_score`
- ❌ `test_name_1`

## 11. Полезные команды

```bash
# Запустить конкретный тест
pytest tests/test_name_matcher.py::TestNameMatcher::test_compare_names_identical -v

# Запустить тесты с подробным выводом
pytest -v --tb=short

# Покрытие только измененных файлов
pytest --cov=src --cov-report=term-missing --cov-fail-under=80 $(git diff --name-only HEAD~1 | grep -E '\.py$' | grep -v test)

# Генерация тестовых данных
python -c "import json; print(json.dumps(test_data, indent=2, ensure_ascii=False))" > fixture.json
```