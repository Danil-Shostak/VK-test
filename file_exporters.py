# file_exporters.py
# Экспорт в различные форматы

import json
import csv
from datetime import datetime

class FileExporter:
    @staticmethod
    def save_json(data, filename):
        """Сохраняет данные в JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON сохранен: {filename}")
            return True
        except Exception as e:
            print(f"❌ Ошибка при сохранении JSON: {e}")
            return False
    
    @staticmethod
    def save_txt(data, filename):
        """Сохраняет данные в TXT"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(FileExporter._format_as_text(data))
            print(f"✅ TXT сохранен: {filename}")
            return True
        except Exception as e:
            print(f"❌ Ошибка при сохранении TXT: {e}")
            return False
    
    @staticmethod
    def save_csv(friends_data, filename):
        """Сохраняет список друзей в CSV"""
        if not friends_data or not friends_data.get('items'):
            return False
        
        try:
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                fieldnames = ['id', 'first_name', 'last_name', 'sex', 'bdate', 
                             'city', 'country', 'online', 'last_seen', 'status']
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
                
                writer.writeheader()
                
                for friend in friends_data['items']:
                    row = {
                        'id': friend.get('id', ''),
                        'first_name': friend.get('first_name', ''),
                        'last_name': friend.get('last_name', ''),
                        'sex': {1: 'Женский', 2: 'Мужской', 0: 'Не указан'}.get(friend.get('sex', 0), ''),
                        'bdate': friend.get('bdate', ''),
                        'city': friend.get('city', {}).get('title', '') if friend.get('city') else '',
                        'country': friend.get('country', {}).get('title', '') if friend.get('country') else '',
                        'online': 'Да' if friend.get('online', 0) else 'Нет',
                        'last_seen': datetime.fromtimestamp(friend.get('last_seen', {}).get('time', 0)).strftime('%d.%m.%Y %H:%M') if friend.get('last_seen') else '',
                        'status': friend.get('status', '')
                    }
                    writer.writerow(row)
            
            print(f"✅ CSV сохранен: {filename}")
            return True
        except Exception as e:
            print(f"❌ Ошибка при сохранении CSV: {e}")
            return False
    
    @staticmethod
    def _format_as_text(data):
        """Форматирует данные для текстового файла"""
        lines = []
        lines.append("="*60)
        lines.append("📊 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ VK")
        lines.append(f"📅 Дата экспорта: {data['metadata']['export_date']}")
        lines.append(f"🔗 Профиль: {data['metadata']['profile_url']}")
        lines.append("="*60 + "\n")
        
        # Основная информация
        lines.append("📋 ОСНОВНЫЕ ДАННЫЕ:")
        lines.append("-"*40)
        for key, value in data['basic_info'].items():
            if value:
                key_rus = {
                    'id': 'ID', 'first_name': 'Имя', 'last_name': 'Фамилия',
                    'domain': 'Домен', 'sex': 'Пол', 'birth_date': 'Дата рождения',
                    'city': 'Город', 'country': 'Страна', 'is_closed': 'Профиль закрыт',
                    'verified': 'Верифицирован'
                }.get(key, key)
                lines.append(f"{key_rus}: {value}")
        lines.append("")
        
        # Контакты
        if data['contacts']:
            lines.append("📱 КОНТАКТЫ:")
            lines.append("-"*40)
            for key, value in data['contacts'].items():
                key_rus = {'site': 'Сайт', 'instagram': 'Instagram',
                          'facebook': 'Facebook', 'twitter': 'Twitter',
                          'skype': 'Skype'}.get(key, key)
                lines.append(f"{key_rus}: {value}")
            lines.append("")
        
        # Интересы
        if data['interests']:
            lines.append("🎯 ИНТЕРЕСЫ:")
            lines.append("-"*40)
            for key, value in data['interests'].items():
                key_rus = {'activities': 'Деятельность', 'interests': 'Интересы',
                          'music': 'Музыка', 'movies': 'Фильмы', 'books': 'Книги',
                          'games': 'Игры', 'quotes': 'Цитаты'}.get(key, key)
                lines.append(f"{key_rus}: {value}")
            lines.append("")
        
        # Статистика
        if data['statistics']:
            lines.append("📈 СТАТИСТИКА:")
            lines.append("-"*40)
            if 'followers_count' in data['statistics']:
                lines.append(f"Подписчиков: {data['statistics']['followers_count']}")
            
            if 'counters' in data['statistics']:
                counters = data['statistics']['counters']
                stat_map = {'friends': 'Друзья', 'followers': 'Подписчики',
                           'photos': 'Фото', 'videos': 'Видео', 'audios': 'Аудио',
                           'groups': 'Группы', 'gifts': 'Подарки'}
                for key, value in counters.items():
                    if key in stat_map:
                        lines.append(f"{stat_map[key]}: {value}")
            lines.append("")
        
        lines.append("="*60)
        lines.append("✅ КОНЕЦ ФАЙЛА")
        lines.append("="*60)
        
        return '\n'.join(lines)