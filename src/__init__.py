# VK Identity Checker
# Программный комплекс для анализа и сравнения профилей ВКонтакте
#
# Модульная архитектура проекта:
# ============================
#
# src/core              - Основные модули запуска и управления приложением
# src/vk_api            - Работа с API ВКонтакте
# src/matchers         - Модули сравнения профилей
# src/face_recognition - Распознавание лиц
# src/handlers         - Обработчики данных
# src/output           - Генерация отчетов
# src/utils            - Вспомогательные утилиты
#
# Использование:
# -----------
# from src.core import main
# from src.vk_api import VKApiClient
# from src.matchers import ProfileComparer
#
# Версия: 1.0.0
# Автор: VK Identity Checker Team 

__version__ = '1.0.0'
__author__ = 'VK Identity Checker Team'

# Не импортируем все модули при загрузке - используйте прямые импорты
# Например: from src.vk_api.vk_api_client import VKApiClient
