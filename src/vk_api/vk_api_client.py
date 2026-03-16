# vk_api_client.py
# Работа с VK API

import requests
import time
from typing import Optional, Dict, Any, List
from src.utils.config import VK_TOKEN, API_VERSION, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY
from src.utils.utils import extract_user_id_from_url
from src.utils.logger import get_logger

# Создаем логгер
logger = get_logger(__name__)

class VKApiClient:
    """
    Клиент для работы с VK API
    
    Обеспечивает:
    - Автоматические повторные попытки при ошибках
    - Логирование запросов
    - Обработку ошибок API
    """
    
    def __init__(self, token: str = VK_TOKEN):
        self.token = token
        self.api_url = "https://api.vk.com/method/"
        self.version = API_VERSION
        self.timeout = REQUEST_TIMEOUT
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
    
    def _request(self, method: str, params: Dict[str, Any], retry_count: int = 0) -> Optional[Any]:
        """
        Базовый метод для запросов к API с поддержкой повторных попыток
        
        Args:
            method: Название метода API
            params: Параметры запроса
            retry_count: Счетчик повторных попыток
        
        Returns:
            Ответ API или None при ошибке
        """
        params.update({
            'access_token': self.token,
            'v': self.version
        })
        
        try:
            logger.debug(f"API request: {method}, params: {params}")
            response = requests.get(
                self.api_url + method, 
                params=params, 
                timeout=self.timeout
            )
            data = response.json()
            
            if 'error' in data:
                error = data['error']
                error_msg = error.get('error_msg', 'Unknown error')
                error_code = error.get('error_code', 0)
                
                logger.warning(f"API error {error_code}: {error_msg}")
                
                # Обработка конкретных ошибок
                if error_code == 5:
                    logger.error("Токен недействителен или отсутствует. Проверьте VK_TOKEN в config.py")
                elif error_code == 6:
                    # Слишком много запросов - пробуем повторить
                    if retry_count < self.max_retries:
                        logger.info(f"Превышен лимит запросов, повторная попытка {retry_count + 1}/{self.max_retries}")
                        time.sleep(self.retry_delay * (retry_count + 1))
                        return self._request(method, params, retry_count + 1)
                elif error_code == 18:
                    logger.error("Пользователь удален или заблокирован")
                elif error_code == 30:
                    logger.error("Профиль приватный")
                
                return None
            
            logger.debug(f"API response success: {method}")
            return data.get('response')
            
        except requests.exceptions.Timeout:
            logger.error(f"Превышен таймаут при запросе к {method}")
            if retry_count < self.max_retries:
                logger.info(f"Повторная попытка {retry_count + 1}/{self.max_retries}")
                time.sleep(self.retry_delay)
                return self._request(method, params, retry_count + 1)
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе {method}: {e}")
            if retry_count < self.max_retries:
                logger.info(f"Повторная попытка {retry_count + 1}/{self.max_retries}")
                time.sleep(self.retry_delay)
                return self._request(method, params, retry_count + 1)
            return None
        
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе {method}: {e}")
            return None
    
    def resolve_screen_name(self, screen_name: str) -> Optional[str]:
        """
        Преобразует screen_name в ID
        
        Args:
            screen_name: Короткое имя пользователя (domain)
        
        Returns:
            ID пользователя или исходное значение при ошибке
        """
        logger.debug(f"Resolving screen name: {screen_name}")
        params = {'screen_names': screen_name}
        response = self._request('utils.resolveScreenName', params)
        
        if response and len(response) > 0:
            result_id = str(response[0]['object_id'])
            logger.debug(f"Screen name resolved: {screen_name} -> {result_id}")
            return result_id
        
        logger.warning(f"Не удалось разрешить screen_name: {screen_name}")
        return screen_name
    
    def get_user_info(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о пользователе
        
        Args:
            user_input: URL, ID или domain пользователя
        
        Returns:
            Словарь с данными пользователя или None
        """
        user_id = extract_user_id_from_url(user_input)
        
        if not user_id:
            logger.error(f"Не удалось распознать ссылку или ID: {user_input}")
            return None
        
        logger.info(f"Поиск пользователя: {user_id}")
        
        # Разрешаем screen_name в ID
        if not user_id.isdigit():
            resolved_id = self.resolve_screen_name(user_id)
            if resolved_id != user_id:
                logger.info(f"Screen name '{user_id}' соответствует ID: {resolved_id}")
                user_id = resolved_id
        
        # Запрашиваем расширенные данные о пользователе
        fields = [
            'id', 'first_name', 'last_name', 'sex', 'bdate', 'city', 'country',
            'photo_max', 'photo_max_orig', 'has_photo', 'online', 'online_mobile',
            'domain', 'nickname', 'screen_name', 'maiden_name',
            'friend_status', 'can_access_closed', 'is_closed',
            'about', 'activities', 'books', 'games', 'interests', 'movies', 'music', 'quotes',
            'career', 'military', 'education', 'universities', 'schools',
            'occupation', 'personal', 'relatives', 'home_town', 'status', 'last_seen',
            'site', 'verified', 'followers_count', 'counters',
            'instagram', 'facebook', 'twitter', 'skype'
        ]
        
        params = {
            'user_ids': user_id,
            'fields': ','.join(fields),
            'lang': 'ru'
        }
        
        response = self._request('users.get', params)
        
        if response and len(response) > 0:
            user_data = response[0]
            logger.info(f"Пользователь найден: {user_data.get('first_name')} {user_data.get('last_name')} (ID: {user_data.get('id')})")
            return user_data
        else:
            logger.warning(f"Пользователь не найден: {user_id}")
            return None