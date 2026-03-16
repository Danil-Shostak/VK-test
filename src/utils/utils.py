# utils.py
# Вспомогательные функции

import re
from datetime import datetime

def extract_user_id_from_url(url):
    """
    Извлекает ID пользователя или screen_name из ссылки ВК
    """
    url = url.strip()
    
    patterns = [
        r'(?:https?://)?(?:www\.)?vk\.com/id(\d+)',
        r'(?:https?://)?(?:www\.)?vk\.com/([a-zA-Z0-9_.]+)',
        r'^id(\d+)$',
        r'^([a-zA-Z0-9_.]+)$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def format_date(timestamp):
    """Форматирует timestamp в дату"""
    return datetime.fromtimestamp(timestamp).strftime('%d.%m.%Y %H:%M')

def get_platform_name(platform_id):
    """Возвращает название платформы по ID"""
    platforms = {
        1: 'мобильной версии', 
        2: 'iPhone', 
        3: 'iPad', 
        4: 'Android', 
        5: 'Windows Phone', 
        6: 'Windows', 
        7: 'Web'
    }
    return platforms.get(platform_id, 'неизвестного устройства')

def format_user_info(user):
    """
    Форматирует и выводит информацию о пользователе в консоль
    """
    print("\n" + "="*60)
    print("📊 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ")
    print("="*60)
    
    if user.get('is_closed'):
        print("🔒 Профиль закрыт (доступна только базовая информация)")
        print(f"   can_access_closed: {user.get('can_access_closed', False)}")
    
    print("\n📋 ОСНОВНЫЕ ДАННЫЕ:")
    print("-"*40)
    
    basic_info = [
        ('ID', 'id'),
        ('Имя', 'first_name'),
        ('Фамилия', 'last_name'),
        ('Пол', 'sex', {1: 'Женский', 2: 'Мужской', 0: 'Не указан'}),
        ('Дата рождения', 'bdate'),
        ('Город', 'city', 'title'),
        ('Страна', 'country', 'title'),
        ('Ссылка', 'domain', lambda x: f"https://vk.com/{x}"),
        ('Статус', 'status'),
        ('О себе', 'about')
    ]
    
    for item in basic_info:
        field_name = item[0]
        field_key = item[1]
        
        if field_key in user and user[field_key]:
            value = user[field_key]
            
            if len(item) > 2:
                if isinstance(item[2], dict):
                    value = item[2].get(value, value)
                elif callable(item[2]):
                    value = item[2](value)
                elif isinstance(item[2], str) and isinstance(value, dict):
                    value = value.get(item[2], value)
            
            if value and str(value).strip():
                print(f"{field_name}: {value}")
    
    # Контакты
    contacts = {}
    if user.get('site'):
        contacts['Сайт'] = user['site']
    if user.get('instagram'):
        contacts['Instagram'] = f"https://instagram.com/{user['instagram']}"
    if user.get('facebook'):
        contacts['Facebook'] = f"https://facebook.com/{user['facebook']}"
    if user.get('twitter'):
        contacts['Twitter'] = f"https://twitter.com/{user['twitter']}"
    if user.get('skype'):
        contacts['Skype'] = user['skype']
    
    if contacts:
        print("\n📱 КОНТАКТЫ:")
        print("-"*40)
        for key, value in contacts.items():
            print(f"{key}: {value}")
    
    # Интересы
    interests = {}
    for field in ['activities', 'interests', 'music', 'movies', 'books', 'games', 'quotes']:
        if user.get(field):
            interests[field.capitalize()] = user[field]
    
    if interests:
        print("\n🎯 ИНТЕРЕСЫ:")
        print("-"*40)
        for key, value in interests.items():
            print(f"{key}: {value}")
    
    # Образование
    if user.get('education'):
        print("\n🎓 ОБРАЗОВАНИЕ:")
        print("-"*40)
        edu = user['education']
        if 'university' in edu:
            print(f"ВУЗ: {edu['university']}")
        if 'faculty' in edu:
            print(f"Факультет: {edu['faculty']}")
        if 'graduation' in edu:
            print(f"Год выпуска: {edu['graduation']}")
    
    # Карьера
    if user.get('career'):
        print("\n💼 КАРЬЕРА:")
        print("-"*40)
        for job in user['career'][:3]:
            company = job.get('company', '')
            position = job.get('position', '')
            if company and position:
                print(f"• {position} в {company}")
            elif company:
                print(f"• {company}")
    
    # Статистика
    if user.get('counters'):
        print("\n📈 СТАТИСТИКА:")
        print("-"*40)
        counters = user['counters']
        stat_fields = [
            ('Друзья', 'friends'),
            ('Подписчики', 'followers'),
            ('Фото', 'photos'),
            ('Видео', 'videos'),
            ('Аудио', 'audios'),
            ('Группы', 'groups'),
            ('Подарки', 'gifts')
        ]
        
        for name, key in stat_fields:
            if key in counters:
                print(f"{name}: {counters[key]}")
    
    if user.get('followers_count'):
        print(f"Подписчиков: {user['followers_count']}")
    
    # Онлайн статус
    print("\n🟢 ОНЛАЙН СТАТУС:")
    print("-"*40)
    if user.get('online', 0):
        online_status = "🟢 Онлайн"
        if user.get('online_mobile'):
            online_status += " (с мобильного)"
        if user.get('online_app'):
            online_status += f" (через приложение {user.get('online_app')})"
        print(online_status)
    else:
        if 'last_seen' in user:
            last_seen = datetime.fromtimestamp(user['last_seen']['time']).strftime('%d.%m.%Y %H:%M')
            platform = user['last_seen'].get('platform', 0)
            platforms = {
                1: 'мобильной версии', 
                2: 'iPhone', 
                3: 'iPad', 
                4: 'Android', 
                5: 'Windows Phone', 
                6: 'Windows', 
                7: 'Web'
            }
            platform_name = platforms.get(platform, 'неизвестного устройства')
            print(f"⚫ Был(а) {last_seen} с {platform_name}")
        else:
            print("⚫ Офлайн")
    
    # Фото профиля
    if user.get('photo_max_orig'):
        print("\n🖼️ ФОТО ПРОФИЛЯ:")
        print("-"*40)
        print(f"Ссылка: {user['photo_max_orig']}")
    
    # Верификация
    if user.get('verified'):
        print("\n✅ ПРОФИЛЬ ВЕРИФИЦИРОВАН")
    
    print("\n" + "="*60)
    print("🔧 ПОЛНЫЙ ОТВЕТ API (все доступные поля):")
    print("="*60)
    from pprint import pprint
    pprint(user)
    
    return user