# main.py
import os
import sys
import io
from datetime import datetime

# UTF-8 for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.utils.config import VK_TOKEN, RESULTS_FOLDER
from src.vk_api.vk_api_client import VKApiClient
from src.handlers.photo_handler import PhotoHandler
from src.handlers.friends_handler import FriendsHandler
from src.handlers.file_exporters import FileExporter
from src.output.html_generator import HTMLGenerator
from src.utils.data_preparer import DataPreparer

def main():
    print("="*60)
    print("🚀 VK ПАРСЕР - АВТОМАТИЧЕСКИЙ РЕЖИМ")
    print("="*60)
    
    # Создаем клиент API
    api_client = VKApiClient()
    
    # Вводим только ссылку
    user_input = input("🔗 Введите ссылку на профиль VK: ").strip()
    
    if not user_input:
        print("❌ Ссылка не может быть пустой")
        return
    
    print("\n⏳ Получаем информацию о пользователе...")
    user = api_client.get_user_info(user_input)
    
    if not user:
        print("\n❌ Не удалось получить информацию о пользователе")
        return
    
    # Создаем папку для результатов
    username = user.get('domain', user.get('id', 'user'))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_folder = f"{RESULTS_FOLDER}/{username}_{timestamp}"
    os.makedirs(results_folder, exist_ok=True)
    
    user_id = user.get('id')
    
    print("\n📸 Загружаем фотографии...")
    photo_handler = PhotoHandler(api_client)
    photos = photo_handler.get_all_photos(user_id)
    
    print("\n👥 Загружаем список друзей...")
    friends_handler = FriendsHandler(api_client)
    friends_data = friends_handler.get_all_friends(user_id)
    
    print("\n💾 Скачиваем фотографии...")
    downloaded_photos = []
    if photos:
        downloaded_photos = photo_handler.download_photos(
            photos, 
            results_folder,
            f"{user.get('first_name', '')} {user.get('last_name', '')}"
        )
    
    print("\n📊 Подготавливаем данные...")
    user_data = DataPreparer.prepare_user_data(user)
    
    # Сохраняем все данные
    FileExporter.save_json(user_data, f"{results_folder}/user_info.json")
    if friends_data:
        FileExporter.save_json(friends_data, f"{results_folder}/friends.json")
    if photos:
        FileExporter.save_json({'count': len(photos), 'items': photos}, f"{results_folder}/photos_info.json")
    
    print("\n🌐 Генерируем сайт со всей информацией...")
    HTMLGenerator.generate_full_site(
        user_data=user_data,
        friends_data=friends_data,
        photos=downloaded_photos,
        photos_dir=os.path.join(results_folder, 'photos') if downloaded_photos else None,
        output_dir=results_folder
    )
    
    print("\n" + "="*60)
    print("✅ ГОТОВО!")
    print(f"📁 Папка с результатами: {os.path.abspath(results_folder)}")
    print(f"🌐 Откройте файл: {os.path.abspath(results_folder)}/index.html")
    print("="*60)

if __name__ == "__main__":
    # Точка входа перенесена в run.py
    # Запустите: python run.py
    pass