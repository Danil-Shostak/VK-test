# vk_api_client.py
# Работа с VK API

import requests
import time
from config import VK_TOKEN, API_VERSION
from utils import extract_user_id_from_url

class VKApiClient:
    def __init__(self, token=VK_TOKEN):
        self.token = token
        self.api_url = "https://api.vk.com/method/"
        self.version = API_VERSION
    
    def _request(self, method, params):
        """Базовый метод для запросов к API"""
        params.update({
            'access_token': self.token,
            'v': self.version
        })
        
        try:
            response = requests.get(self.api_url + method, params=params)
            data = response.json()
            
            if 'error' in data:
                print(f"❌ Ошибка API: {data['error']['error_msg']}")
                if data['error'].get('error_code') == 5:
                    print("   ❗ Токен недействителен или отсутствует.")
                return None
            
            return data.get('response')
        except Exception as e:
            print(f"❌ Ошибка при запросе: {e}")
            return None
    
    def resolve_screen_name(self, screen_name):
        """Преобразует screen_name в ID"""
        params = {'screen_names': screen_name}
        response = self._request('utils.resolveScreenName', params)
        if response and response[0]:
            return str(response[0]['object_id'])
        return screen_name
    
    def get_user_info(self, user_input):
        """Получает информацию о пользователе"""
        user_id = extract_user_id_from_url(user_input)
        
        if not user_id:
            print("❌ Не удалось распознать ссылку или ID")
            return None
        
        print(f"🔍 Ищем пользователя: {user_id}")
        
        if not user_id.isdigit():
            resolved_id = self.resolve_screen_name(user_id)
            if resolved_id != user_id:
                print(f"📝 Screen name '{user_id}' соответствует ID: {resolved_id}")
                user_id = resolved_id
        
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
            return response[0]
        else:
            print("❌ Пользователь не найден")
            return None