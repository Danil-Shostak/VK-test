# run.py
# Единая точка входа для системы анализа профилей VK
# Объединяет парсинг, сохранение и сравнение профилей

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Optional

# Импорты из проекта
from src.utils.config import VK_TOKEN, RESULTS_FOLDER
from src.vk_api.vk_api_client import VKApiClient
from src.handlers.photo_handler import PhotoHandler
from src.handlers.friends_handler import FriendsHandler
from src.handlers.file_exporters import FileExporter
from src.output.html_generator import HTMLGenerator
from src.utils.data_preparer import DataPreparer
from src.matchers.profile_comparer import ProfileComparer


class VKProfileAnalyzer:
    """
    Главный класс для анализа профилей VK.
    
    Возможности:
    - Парсинг профиля с сохранением данных и генерацией HTML отчета
    - Сравнение двух профилей
    - Загрузка профилей из папки
    """
    
    def __init__(self, token: str = None):
        """
        Инициализирует анализатор.
        
        Args:
            token: VK API токен (если не передан, используется из config.py)
        """
        if token:
            self.api = VKApiClient(token)
        else:
            try:
                from src.utils.config import VK_TOKEN
                self.api = VKApiClient(VK_TOKEN)
            except Exception as e:
                print(f"⚠️ Ошибка при загрузке токена: {e}")
                self.api = None
    
    # ==================== ПАРСИНГ ПРОФИЛЯ ====================
    
    def parse_profile(self, profile_url: str, download_photos: bool = True) -> Optional[Dict]:
        """
        Парсит профиль VK и сохраняет все данные.
        
        Args:
            profile_url: URL или ID профиля VK
            download_photos: Скачивать ли фотографии на диск
            
        Returns:
            Dict с данными профиля или None при ошибке
        """
        if not self.api:
            print("❌ API клиент не инициализирован")
            return None
        
        print(f"\n{'='*60}")
        print(f"🔍 Парсинг профиля: {profile_url}")
        print(f"{'='*60}")
        
        # Получаем информацию о пользователе
        print("\n⏳ Получаем информацию о пользователе...")
        user = self.api.get_user_info(profile_url)
        
        if not user:
            print("\n❌ Не удалось получить информацию о пользователе")
            return None
        
        # Создаем папку для результатов
        username = user.get('domain', user.get('id', 'user'))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_folder = f"{RESULTS_FOLDER}/{username}_{timestamp}"
        os.makedirs(results_folder, exist_ok=True)
        
        user_id = user.get('id')
        
        # Загружаем друзей
        print("\n👥 Загружаем список друзей...")
        friends_handler = FriendsHandler(self.api)
        friends_data = friends_handler.get_all_friends(user_id)
        
        # Загружаем фотографии
        print("\n📸 Загружаем фотографии...")
        photo_handler = PhotoHandler(self.api)
        photos = photo_handler.get_all_photos(user_id)
        
        # Скачиваем фотографии, если нужно
        downloaded_photos = []
        if download_photos and photos:
            downloaded_photos = photo_handler.download_photos(
                photos, 
                results_folder,
                f"{user.get('first_name', '')} {user.get('last_name', '')}"
            )
        
        # Подготавливаем данные
        print("\n📊 Подготавливаем данные...")
        user_data = DataPreparer.prepare_user_data(user)
        
        # Сохраняем все данные
        print("\n💾 Сохраняем данные...")
        FileExporter.save_json(user_data, f"{results_folder}/user_info.json")
        if friends_data:
            FileExporter.save_json(friends_data, f"{results_folder}/friends.json")
        if photos:
            FileExporter.save_json({'count': len(photos), 'items': photos}, f"{results_folder}/photos_info.json")
        
        # Генерируем HTML отчет
        print("\n🌐 Генерируем HTML отчет...")
        HTMLGenerator.generate_full_site(
            user_data=user_data,
            friends_data=friends_data,
            photos=downloaded_photos,
            photos_dir=os.path.join(results_folder, 'photos') if downloaded_photos else None,
            output_dir=results_folder
        )
        
        print(f"\n{'='*60}")
        print("✅ Парсинг завершен!")
        print(f"📁 Папка с результатами: {os.path.abspath(results_folder)}")
        print(f"🌐 Откройте файл: {os.path.abspath(results_folder)}/index.html")
        print(f"{'='*60}")
        
        return {
            'folder': results_folder,
            'user_data': user_data,
            'friends_data': friends_data,
            'photos_data': photos
        }
    
    # ==================== ЗАГРУЗКА ПРОФИЛЯ ====================
    
    def load_profile(self, profile_url: str) -> Optional[Dict]:
        """
        Загружает данные профиля по URL или ID.
        
        Args:
            profile_url: URL или ID профиля VK
            
        Returns:
            Dict с данными профиля
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
        friends_handler = FriendsHandler(self.api)
        friends_data = friends_handler.get_all_friends(user_id)
        
        # Загружаем фото (лимит 100 последних)
        print(f"   📸 Загрузка фотографий (лимит 100)...")
        photo_handler = PhotoHandler(self.api)
        photos_data = photo_handler.get_all_photos(user_id, limit=100)
        
        return {
            'profile': user_data,
            'friends': friends_data,
            'photos': photos_data
        }
    
    def load_from_folder(self, folder_path: str) -> Optional[Dict]:
        """
        Загружает данные профиля из ранее сохраненной папки.
        
        Args:
            folder_path: Путь к папке с данными профиля
            
        Returns:
            Dict с данными профиля
        """
        if not os.path.exists(folder_path):
            print(f"❌ Папка не найдена: {folder_path}")
            return None
        
        print(f"\n📂 Загрузка из папки: {folder_path}")
        
        data = {
            'profile': None,
            'friends': None,
            'photos': None
        }
        
        # Загружаем JSON файлы
        user_info_path = os.path.join(folder_path, 'user_info.json')
        if os.path.exists(user_info_path):
            with open(user_info_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                data['profile'] = raw_data.get('raw_data', raw_data)
        
        friends_path = os.path.join(folder_path, 'friends.json')
        if os.path.exists(friends_path):
            with open(friends_path, 'r', encoding='utf-8') as f:
                data['friends'] = json.load(f)
        
        photos_path = os.path.join(folder_path, 'photos_info.json')
        if os.path.exists(photos_path):
            with open(photos_path, 'r', encoding='utf-8') as f:
                photos_json = json.load(f)
                data['photos'] = photos_json.get('items', [])
        
        return data
    
    # ==================== СРАВНЕНИЕ ПРОФИЛЕЙ ====================
    
    def compare_profiles(self, profile1_data: Dict, profile2_data: Dict) -> Dict:
        """
        Сравнивает два профиля.
        
        Args:
            profile1_data: Данные первого профиля
            profile2_data: Данные второго профиля
            
        Returns:
            Результат сравнения
        """
        print("\n" + "="*60)
        print("🔬 СРАВНЕНИЕ ПРОФИЛЕЙ")
        print("="*60)
        
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
        
        # Выводим краткую сводку
        print("\n" + "="*60)
        print("📊 РЕЗУЛЬТАТ СРАВНЕНИЯ")
        print("="*60)
        
        final = result.get('final', {})
        print(f"\n🎯 Итоговая оценка: {final.get('percentage', 0):.1f}%")
        print(f"   {final.get('interpretation', '')}")
        print(f"   Уверенность: {final.get('confidence', '')}")
        
        return result
    
    def save_comparison_result(self, result: Dict, output_path: str) -> None:
        """Сохраняет результаты сравнения в файл."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Результаты сохранены в: {output_path}")
    
    # ==================== ИНТЕРАКТИВНЫЙ РЕЖИМ ====================
    
    def run_interactive(self):
        """Запускает интерактивный режим с меню."""
        
        def print_header():
            print("\n" + "="*60)
            print("🔍 СИСТЕМА АНАЛИЗА ПРОФИЛЕЙ VK")
            print("   Парсинг, сохранение и сравнение профилей")
            print("="*60)
        
        def print_menu():
            print("\n📋 МЕНЮ:")
            print("  1. 📥 Спарсировать профиль (сохранить данные и отчет)")
            print("  2. 🔬 Сравнить два профиля по URL")
            print("  3. 📂 Сравнить профиль из папки с профилем по URL")
            print("  4. 🔗 Сравнить два профиля из папок")
            print("  5. ❌ Выход")
        
        def get_profile_input(prompt_num):
            print(f"\nВведите URL или ID профиля {prompt_num}:")
            print("  Примеры: vk.com/id123456789, id123456789, dariapalchik")
            return input("  > ").strip()
        
        def get_folder_input(prompt_num):
            print(f"\nВведите путь к папке с профилем {prompt_num}:")
            print("  Пример: vk_results/dariapalchik_20260302_130051")
            path = input("  > ").strip()
            if os.path.isdir(path):
                return path
            else:
                print(f"  ⚠️ Папка не найдена: {path}")
                return None
        
        print_header()
        
        # Проверяем токен
        if not self.api:
            print("\n❌ Необходим VK API токен для работы.")
            print("   Укажите токен в config.py или в переменной окружения VK_TOKEN")
            return
        
        while True:
            print_menu()
            choice = input("\nВыберите пункт (1-5): ").strip()
            
            if choice == "1":
                # Парсинг профиля
                profile_url = get_profile_input(1)
                if not profile_url:
                    continue
                
                download_photos = input("\nСкачать фотографии? (д/н): ").strip().lower() in ['д', 'y', 'yes']
                self.parse_profile(profile_url, download_photos)
            
            elif choice == "2":
                # Оба профиля по URL
                profile1_url = get_profile_input(1)
                if not profile1_url:
                    continue
                profile2_url = get_profile_input(2)
                if not profile2_url:
                    continue
                
                p1 = self.load_profile(profile1_url)
                if not p1:
                    print("❌ Не удалось загрузить первый профиль")
                    continue
                    
                p2 = self.load_profile(profile2_url)
                if not p2:
                    print("❌ Не удалось загрузить второй профиль")
                    continue
                
                result = self.compare_profiles(p1, p2)
                
                save = input("\nСохранить результаты? (д/н): ").strip().lower()
                if save == 'д' or save == 'y':
                    output_file = input("Введите имя файла (или Enter для auto): ").strip()
                    if not output_file:
                        output_file = f"comparison_{p1['profile'].get('id', 'p1')}_{p2['profile'].get('id', 'p2')}.json"
                    self.save_comparison_result(result, output_file)
            
            elif choice == "3":
                # Профиль из папки + URL
                folder = get_folder_input(1)
                if not folder:
                    continue
                profile_url = get_profile_input(2)
                if not profile_url:
                    continue
                
                p1 = self.load_from_folder(folder)
                if not p1:
                    print("❌ Не удалось загрузить профиль из папки")
                    continue
                    
                p2 = self.load_profile(profile_url)
                if not p2:
                    print("❌ Не удалось загрузить профиль")
                    continue
                
                self.compare_profiles(p1, p2)
            
            elif choice == "4":
                # Оба из папок
                folder1 = get_folder_input(1)
                if not folder1:
                    continue
                folder2 = get_folder_input(2)
                if not folder2:
                    continue
                
                p1 = self.load_from_folder(folder1)
                if not p1:
                    print("❌ Не удалось загрузить первый профиль")
                    continue
                    
                p2 = self.load_from_folder(folder2)
                if not p2:
                    print("❌ Не удалось загрузить второй профиль")
                    continue
                
                result = self.compare_profiles(p1, p2)
                
                save = input("\nСохранить результаты? (д/н): ").strip().lower()
                if save == 'д' or save == 'y':
                    output_file = input("Введите имя файла: ").strip()
                    if output_file:
                        self.save_comparison_result(result, output_file)
            
            elif choice == "5":
                print("\n👋 До свидания!")
                break
            else:
                print("\n⚠️ Неверный выбор. Попробуйте снова.")
            
            input("\nНажмите Enter для продолжения...")


def main():
    """Главная функция CLI."""
    
    parser = argparse.ArgumentParser(
        description='Система анализа профилей VK',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Режимы работы:

1. ИНТЕРАКТИВНЫЙ РЕЖИМ (без аргументов):
   python run.py

2. ПАРСИНГ ПРОФИЛЯ:
   python run.py parse "vk.com/id123456789"
   python run.py parse "vk.com/id123456789" --no-photos
   
3. СРАВНЕНИЕ ПРОФИЛЕЙ:
   python run.py compare "vk.com/id123456789" "vk.com/id789012345"
   python run.py compare "vk_results/user1" "vk.com/id789012345"
   python run.py compare "vk_results/user1" "vk_results/user2" -o result.json

Примеры:
   python run.py parse "dariapalchik"
   python run.py parse "id1102624689" --no-photos
   python run.py compare "vk.com/id123" "vk.com/id456" -o compare.json
   python run.py compare "vk_results/profile1" "vk_results/profile2"
        """
    )
    
    parser.add_argument(
        'mode', 
        nargs='?', 
        choices=['parse', 'compare', 'interactive'],
        default='interactive',
        help='Режим работы: parse (парсинг), compare (сравнение), interactive (меню)'
    )
    
    parser.add_argument(
        'profile1', 
        nargs='?', 
        help='Первый профиль (URL, ID или путь к папке)'
    )
    
    parser.add_argument(
        'profile2', 
        nargs='?', 
        help='Второй профиль (URL, ID или путь к папке) для режима compare'
    )
    
    parser.add_argument(
        '-t', '--token', 
        default=None,
        help='VK API токен'
    )
    
    parser.add_argument(
        '-o', '--output', 
        default=None,
        help='Путь для сохранения результатов (JSON)'
    )
    
    parser.add_argument(
        '--no-photos', 
        action='store_true',
        help='Не скачивать фотографии при парсинге'
    )
    
    parser.add_argument(
        '-v', '--verbose', 
        action='store_true',
        help='Подробный вывод'
    )
    
    args = parser.parse_args()
    
    # Создаем анализатор
    analyzer = VKProfileAnalyzer(args.token)
    
    # Проверяем наличие API
    if not analyzer.api:
        print("\n❌ Необходим VK API токен для работы.")
        print("   Укажите токен:")
        print("   - В файле config.py")
        print("   - В переменной окружения VK_TOKEN")
        print("   - Через параметр --token")
        print("\n   Получить токен: https://vk.com/apps?act=manage")
        return 1
    
    # Выполняем запрошенный режим
    if args.mode == 'interactive' or (not args.profile1 and not args.profile2):
        # Интерактивный режим
        analyzer.run_interactive()
    
    elif args.mode == 'parse':
        # Парсинг профиля
        if not args.profile1:
            print("❌ Укажите профиль для парсинга")
            print("   Пример: python run.py parse vk.com/id123456789")
            return 1
        
        download_photos = not args.no_photos
        analyzer.parse_profile(args.profile1, download_photos)
    
    elif args.mode == 'compare':
        # Сравнение профилей
        if not args.profile1 or not args.profile2:
            print("❌ Укажите два профиля для сравнения")
            print("   Пример: python run.py compare vk.com/id123 vk.com/id456")
            return 1
        
        # Определяем тип входных данных
        def load_data(path):
            if path.startswith('vk.com') or path.isdigit() or 'id' in path:
                return analyzer.load_profile(path)
            elif os.path.isdir(path):
                return analyzer.load_from_folder(path)
            else:
                # Пробуем как URL
                return analyzer.load_profile(path)
        
        p1 = load_data(args.profile1)
        if not p1:
            print(f"❌ Не удалось загрузить первый профиль: {args.profile1}")
            return 1
        
        p2 = load_data(args.profile2)
        if not p2:
            print(f"❌ Не удалось загрузить второй профиль: {args.profile2}")
            return 1
        
        result = analyzer.compare_profiles(p1, p2)
        
        if args.output:
            analyzer.save_comparison_result(result, args.output)
    
    return 0


if __name__ == "__main__":
    # UTF-8 for Windows - после импортов, но до argparse
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
