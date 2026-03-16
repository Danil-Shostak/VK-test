# config.py
# Конфигурация VK Parser
import os

# VK API токен
# Приоритет: 1) переменная окружения 2) файл token.txt 3) значение по умолчанию
VK_TOKEN = os.environ.get('VK_TOKEN')

# Если токен не найден в переменной окружения, пробуем считать из файла
if not VK_TOKEN:
    token_file = os.path.join(os.path.dirname(__file__), 'token.txt')
    if os.path.exists(token_file):
        with open(token_file, 'r', encoding='utf-8') as f:
            VK_TOKEN = f.read().strip()

# Если токен все еще не найден - используем значение по умолчанию (для совместимости)
if not VK_TOKEN:
    VK_TOKEN = "vk1.a.placeholder_token"

API_VERSION = '5.131'
MAX_PHOTOS_PER_REQUEST = 200
MAX_FRIENDS_PER_REQUEST = 5000
RESULTS_FOLDER = "results"

# Настройки логирования
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.environ.get('LOG_FILE', 'vk_parser.log')

# Настройки времени ожидания (секунды)
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3
RETRY_DELAY = 1

# Папка для временных файлов
TEMP_FOLDER = "temp_avatars"