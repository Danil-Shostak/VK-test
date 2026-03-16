# friends_handler.py
# Работа с друзьями

import time
from datetime import datetime
from src.utils.utils import get_platform_name

class FriendsHandler:
    def __init__(self, api_client):
        self.api = api_client
    
    def get_all_friends(self, user_id, max_count=5000):
        """Получает полный список друзей"""
        all_friends = []
        offset = 0
        count_per_request = 5000
        
        print(f"\n👥 Загрузка списка друзей пользователя {user_id}...")
        
        # Сначала получаем общее количество
        params = {'user_id': user_id, 'count': 1}
        response = self.api._request('friends.get', params)
        
        if not response:
            return None
        
        total_count = response.get('count', 0)
        print(f"   Всего друзей: {total_count}")
        
        if total_count == 0:
            print("   У пользователя нет друзей")
            return {'count': 0, 'items': []}
        
        fields = [
            'first_name', 'last_name', 'sex', 'bdate', 'city', 'country',
            'photo_100', 'online', 'last_seen', 'status', 'followers_count',
            'common_count', 'relation', 'universities', 'schools', 'occupation'
        ]
        
        while offset < min(total_count, max_count):
            params = {
                'user_id': user_id,
                'fields': ','.join(fields),
                'offset': offset,
                'count': min(count_per_request, max_count - offset)
            }
            
            response = self.api._request('friends.get', params)
            
            if not response:
                break
            
            items = response.get('items', [])
            all_friends.extend(items)
            print(f"   Загружено {len(all_friends)} из {total_count} друзей...")
            
            if len(items) < count_per_request:
                break
                
            offset += len(items)
            time.sleep(0.3)
        
        print(f"✅ Загружено {len(all_friends)} друзей")
        return {
            'count': len(all_friends),
            'total': total_count,
            'items': all_friends
        }
    
    @staticmethod
    def analyze_friends_stats(friends_list):
        """Анализирует статистику по друзьям (статический метод)"""
        if not friends_list:
            return {}
        
        stats = {}
        
        # Пол
        sex_count = {1: 0, 2: 0, 0: 0}
        for friend in friends_list:
            sex = friend.get('sex', 0)
            sex_count[sex] = sex_count.get(sex, 0) + 1
        
        stats['sex'] = {
            'female': sex_count[1],
            'male': sex_count[2],
            'unknown': sex_count[0]
        }
        
        # Онлайн
        online_count = sum(1 for f in friends_list if f.get('online', 0))
        stats['online'] = online_count
        
        # Города
        cities = {}
        for friend in friends_list:
            city = friend.get('city', {}).get('title', 'Не указан')
            cities[city] = cities.get(city, 0) + 1
        
        stats['cities'] = dict(sorted(cities.items(), 
                                      key=lambda x: x[1], 
                                      reverse=True)[:10])
        
        # Возраст
        current_year = datetime.now().year
        ages = []
        for friend in friends_list:
            bdate = friend.get('bdate', '')
            if bdate and len(bdate.split('.')) == 3:
                try:
                    year = int(bdate.split('.')[2])
                    age = current_year - year
                    if 14 <= age <= 100:
                        ages.append(age)
                except:
                    pass
        
        if ages:
            stats['avg_age'] = sum(ages) / len(ages)
        
        return stats