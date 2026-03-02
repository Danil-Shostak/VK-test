# data_preparer.py
# Подготовка данных для экспорта

from datetime import datetime

class DataPreparer:
    @staticmethod
    def prepare_user_data(user):
        """Подготавливает данные пользователя для экспорта"""
        if not user:
            return None
        
        data = {
            "metadata": {
                "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "profile_url": f"https://vk.com/{user.get('domain', user.get('id'))}",
                "profile_id": user.get('id')
            },
            "basic_info": {},
            "personal_info": {},
            "contacts": {},
            "interests": {},
            "education_career": {},
            "statistics": {},
            "online_status": {},
            "raw_data": user
        }
        
        # Основная информация
        basic_fields = ['id', 'first_name', 'last_name', 'domain', 'screen_name', 'nickname']
        for field in basic_fields:
            if field in user and user[field]:
                data['basic_info'][field] = user[field]
        
        if 'sex' in user:
            sex_map = {1: 'Женский', 2: 'Мужской', 0: 'Не указан'}
            data['basic_info']['sex'] = sex_map.get(user['sex'], 'Не указан')
        
        if 'bdate' in user:
            data['basic_info']['birth_date'] = user['bdate']
        
        if 'city' in user and 'title' in user['city']:
            data['basic_info']['city'] = user['city']['title']
        if 'country' in user and 'title' in user['country']:
            data['basic_info']['country'] = user['country']['title']
        
        # Личная информация
        personal_fields = ['about', 'status', 'home_town']
        for field in personal_fields:
            if field in user and user[field]:
                data['personal_info'][field] = user[field]
        
        # Контакты
        contact_fields = ['site', 'instagram', 'facebook', 'twitter', 'skype']
        for field in contact_fields:
            if field in user and user[field]:
                if field == 'instagram':
                    data['contacts']['instagram'] = f"https://instagram.com/{user[field]}"
                elif field == 'facebook':
                    data['contacts']['facebook'] = f"https://facebook.com/{user[field]}"
                elif field == 'twitter':
                    data['contacts']['twitter'] = f"https://twitter.com/{user[field]}"
                else:
                    data['contacts'][field] = user[field]
        
        # Интересы
        interest_fields = ['activities', 'interests', 'music', 'movies', 'books', 'games', 'quotes']
        for field in interest_fields:
            if field in user and user[field]:
                data['interests'][field] = user[field]
        
        # Образование и карьера
        if 'education' in user:
            data['education_career']['education'] = user['education']
        if 'career' in user:
            data['education_career']['career'] = user['career'][:5]
        if 'universities' in user:
            data['education_career']['universities'] = user['universities']
        if 'schools' in user:
            data['education_career']['schools'] = user['schools']
        
        # Статистика
        if 'counters' in user:
            data['statistics']['counters'] = user['counters']
        if 'followers_count' in user:
            data['statistics']['followers_count'] = user['followers_count']
        
        # Онлайн статус
        data['online_status']['online'] = user.get('online', 0)
        if 'last_seen' in user:
            data['online_status']['last_seen'] = {
                'time': user['last_seen']['time'],
                'platform': user['last_seen'].get('platform', 0)
            }
        
        # Фото
        if 'photo_max_orig' in user:
            data['basic_info']['photo'] = user['photo_max_orig']
        
        # Приватность
        data['basic_info']['is_closed'] = user.get('is_closed', False)
        data['basic_info']['verified'] = user.get('verified', False)
        
        return data