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
# from src.vk_api import VKAPIClient
# from src.matchers import ProfileComparer
#
# Версия: 1.0.0
# Автор: VK Identity Checker Team

__version__ = '1.0.0'
__author__ = 'VK Identity Checker Team'

from .core import main, run_analysis, IdentityChecker
from .vk_api import VKAPIClient
from .matchers import (
    NameMatcher,
    FriendsMatcher,
    GeoMatcher,
    DemographicsMatcher,
    VisualMatcher,
    ContentMatcher,
    ProfileComparer
)
from .face_recognition import (
    FaceRecognitionModule,
    OpenCVFaceRecognition,
    MediaPipeFaceRecognition
)
from .handlers import (
    PhotoHandler,
    FriendsHandler,
    JSONExporter,
    CSVExporter,
    TXTExporter
)
from .output import HTMLGenerator
from .utils import (
    load_json,
    save_json,
    ensure_dir,
    setup_logger,
    get_logger,
    Config,
    DataPreparer
)

__all__ = [
    # Core
    'main',
    'run_analysis', 
    'IdentityChecker',
    # VK API
    'VKAPIClient',
    # Matchers
    'NameMatcher',
    'FriendsMatcher',
    'GeoMatcher',
    'DemographicsMatcher',
    'VisualMatcher',
    'ContentMatcher',
    'ProfileComparer',
    # Face Recognition
    'FaceRecognitionModule',
    'OpenCVFaceRecognition',
    'MediaPipeFaceRecognition',
    # Handlers
    'PhotoHandler',
    'FriendsHandler',
    'JSONExporter',
    'CSVExporter',
    'TXTExporter',
    # Output
    'HTMLGenerator',
    # Utils
    'load_json',
    'save_json',
    'ensure_dir',
    'setup_logger',
    'get_logger',
    'Config',
    'DataPreparer'
]
