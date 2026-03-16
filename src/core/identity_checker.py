# identity_checker.py
# CLI интерфейс для запуска системы идентификации профилей VK

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Optional

# Импортируем модули проекта
from src.vk_api.vk_api_client import VKApiClient
from src.matchers.profile_comparer import ProfileComparer
from src.utils.utils import extract_user_id_from_url


class IdentityChecker:
    """
    CLI интерфейс для системы идентификации профилей VK
    
    Позволяет:
    - Загрузить данные двух профилей
    - Сравнить их
    - Вывести результаты
    """
    
    def __init__(self, token: str = None):
        """
        Инициализирует чекер
        
        Args:
            token: VK API токен (если не передан, будет прочитан из config.py)
        """
        
        if token:
            self.api = VKApiClient(token)
        else:
            # Пробуем импортировать из config
            try:
                from src.utils.config import VK_TOKEN
                self.api = VKApiClient(VK_TOKEN)
            except:
                print("⚠️ Внимание: Токен VK API не найден.")
                print("   Для работы укажите токен через параметр --token")
                self.api = None
    
    def load_profile(self, profile_url: str) -> Optional[Dict]:
        """
        Загружает данные профиля по URL или ID
        
        Args:
            profile_url: URL или ID профиля VK
            
        Returns:
            Dict с данными профиля или None при ошибке
        """
        
        if not self.api:
            print("❌ API клиент не инициализирован")
            return None
        
        print(f"\n🔍 Загрузка профиля: {profile_url}")
        
        user_data = self.api.get_user_info(profile_url)
        
        if not user_data:
            print(f"❌ Не удалось загрузить профиль: {profile_url}")
            return None
        
        user_id = user_data.get('id')
        
        # Загружаем друзей
        print(f"   👥 Загрузка друзей...")
        from friends_handler import FriendsHandler
        friends_handler = FriendsHandler(self.api)
        friends_data = friends_handler.get_all_friends(user_id)
        
        # Загружаем фото
        print(f"   📸 Загрузка фотографий...")
        from photo_handler import PhotoHandler
        photo_handler = PhotoHandler(self.api)
        photos_data = photo_handler.get_all_photos(user_id)
        
        return {
            'profile': user_data,
            'friends': friends_data,
            'photos': photos_data
        }
    
    def load_from_file(self, folder_path: str) -> Optional[Dict]:
        """
        Загружает данные профиля из ранее сохраненной папки
        
        Args:
            folder_path: Путь к папке с данными профиля
            
        Returns:
            Dict с данными профиля
        """
        
        if not os.path.exists(folder_path):
            print(f"❌ Папка не найдена: {folder_path}")
            return None
        
        print(f"\n📂 Загрузка из папки: {folder_path}")
        
        # Загружаем JSON файлы
        data = {
            'profile': None,
            'friends': None,
            'photos': None
        }
        
        # Ищем файл с информацией о пользователе
        user_info_path = os.path.join(folder_path, 'user_info.json')
        if os.path.exists(user_info_path):
            with open(user_info_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                data['profile'] = raw_data.get('raw_data', raw_data)
        
        # Ищем файл с друзьями
        friends_path = os.path.join(folder_path, 'friends.json')
        if os.path.exists(friends_path):
            with open(friends_path, 'r', encoding='utf-8') as f:
                data['friends'] = json.load(f)
        
        # Ищем файл с фото
        photos_path = os.path.join(folder_path, 'photos_info.json')
        if os.path.exists(photos_path):
            with open(photos_path, 'r', encoding='utf-8') as f:
                photos_json = json.load(f)
                data['photos'] = photos_json.get('items', [])
        
        return data
    
    def compare_profiles(self, profile1_data: Dict, profile2_data: Dict) -> Dict:
        """
        Сравнивает два профиля
        
        Args:
            profile1_data: Данные первого профиля
            profile2_data: Данные второго профиля
            
        Returns:
            Результат сравнения
        """
        
        print("\n" + "="*60)
        print("🔬 СРАВНЕНИЕ ПРОФИЛЕЙ")
        print("="*60)
        
        # Извлекаем основные данные
        p1 = profile1_data.get('profile', {})
        p2 = profile2_data.get('profile', {})
        
        print(f"\n📋 Профиль 1: {p1.get('first_name')} {p1.get('last_name')}")
        print(f"   ID: {p1.get('id')}")
        print(f"   Ссылка: vk.com/{p1.get('domain', p1.get('id'))}")
        
        print(f"\n📋 Профиль 2: {p2.get('first_name')} {p2.get('last_name')}")
        print(f"   ID: {p2.get('id')}")
        print(f"   Ссылка: vk.com/{p2.get('domain', p2.get('id'))}")
        
        # Создаем компаратор и запускаем сравнение
        comparer = ProfileComparer()
        
        result = comparer.compare_profiles(
            p1, p2,
            friends1_data=profile1_data.get('friends'),
            friends2_data=profile2_data.get('friends'),
            photos1_data=profile1_data.get('photos'),
            photos2_data=profile2_data.get('photos')
        )
        
        # Выводим результаты
        comparer.print_summary(result)
        
        return result
    
    def save_results(self, result: Dict, output_path: str) -> None:
        """Сохраняет результаты в файл"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Результаты сохранены в: {output_path}")


def main():
    """Главная функция CLI"""
    
    parser = argparse.ArgumentParser(
        description='Система идентификации профилей VK',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

1. Сравнить два профиля по URL:
   python identity_checker.py -p1 "vk.com/id123456" -p2 "vk.com/id789012"

2. Сравнить профиль из папки с URL:
   python identity_checker.py -p1 "vk_results/user1_20240301" -p2 "vk.com/id789012"

3. Сравнить два профиля из папок:
   python identity_checker.py -p1 "vk_results/user1" -p2 "vk_results/user2"

4. С указанием токена:
   python identity_checker.py -p1 "vk.com/id123" -p2 "vk.com/id456" -t "YOUR_TOKEN"

5. Сохранить результаты:
   python identity_checker.py -p1 "vk.com/id123" -p2 "vk.com/id456" -o result.json
        """
    )
    
    parser.add_argument('-p1', '--profile1', required=True,
                       help='Первый профиль (URL, ID или путь к папке)')
    parser.add_argument('-p2', '--profile2', required=True,
                       help='Второй профиль (URL, ID или путь к папке)')
    parser.add_argument('-t', '--token', default=None,
                       help='VK API токен')
    parser.add_argument('-o', '--output', default=None,
                       help='Путь для сохранения результатов (JSON)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Подробный вывод')
    
    args = parser.parse_args()
    
    # Инициализируем чекер
    checker = IdentityChecker(args.token)
    
    if not checker.api:
        print("\n❌ Для работы необходим VK API токен.")
        print("   Получить токен можно здесь: https://vk.com/apps?act=manage")
        print("   Или укажите его в config.py")
        return 1
    
    # Определяем тип входных данных (URL или папка)
    def load_data(path):
        # Проверяем, это URL или ID
        if path.startswith('vk.com') or path.isdigit() or 'id' in path:
            return checker.load_profile(path)
        # Иначе пробуем как папку
        elif os.path.isdir(path):
            return checker.load_from_file(path)
        else:
            print(f"❌ Не удалось определить тип входных данных: {path}")
            return None
    
    # Загружаем профили
    profile1_data = load_data(args.profile1)
    if not profile1_data:
        print("❌ Не удалось загрузить первый профиль")
        return 1
    
    profile2_data = load_data(args.profile2)
    if not profile2_data:
        print("❌ Не удалось загрузить второй профиль")
        return 1
    
    # Сравниваем профили
    result = checker.compare_profiles(profile1_data, profile2_data)
    
    # Сохраняем результаты
    if args.output:
        checker.save_results(result, args.output)
    
    return 0


if __name__ == "__main__":
    # Точка входа перенесена в run.py
    # Запустите: python run.py
    pass
