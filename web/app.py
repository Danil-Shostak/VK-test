# app.py
# Веб-приложение VK Parser
# Запуск: python app.py

import os
import sys
import json
import uuid
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory

# Добавляем родительскую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Прямой импорт модулей, минуя проблемные пакеты
from src.vk_api.vk_api_client import VKApiClient
from src.handlers.photo_handler import PhotoHandler
from src.handlers.friends_handler import FriendsHandler
from src.handlers.file_exporters import FileExporter
from src.utils.data_preparer import DataPreparer
from src.matchers.profile_comparer import ProfileComparer
from src.utils.config import VK_TOKEN, RESULTS_FOLDER

app = Flask(__name__)
app.secret_key = 'vk-parser-secret-key'

# Конфигурация
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'profiles')
RESULTS_FOLDER = os.path.join(os.path.dirname(__file__), 'results')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Создаем папки
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Глобальное хранилище состояния (для демонстрации)
# В production использовать базу данных
profiles_cache = {}
comparisons_cache = {}


def get_api_client(token=None):
    """Создает API клиент VK"""
    if token:
        return VKApiClient(token)
    
    # Пробуем загрузить токен из config
    try:
        from src.utils.config import VK_TOKEN
        if VK_TOKEN:
            return VKApiClient(VK_TOKEN)
    except:
        pass
    
    return None


def parse_profile_async(profile_url, token, download_photos, session_id):
    """Асинхронный парсинг профиля"""
    try:
        api = get_api_client(token)
        if not api:
            profiles_cache[session_id] = {'status': 'error', 'message': 'Необходим VK API токен'}
            return
        
        profiles_cache[session_id] = {'status': 'processing', 'message': 'Получаем информацию о пользователе...'}
        
        # Получаем информацию о пользователе
        user = api.get_user_info(profile_url)
        if not user:
            profiles_cache[session_id] = {'status': 'error', 'message': 'Не удалось получить информацию о пользователе'}
            return
        
        # Создаем папку для результатов
        username = user.get('domain', user.get('id', 'user'))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_folder = f"{RESULTS_FOLDER}/{username}_{timestamp}"
        os.makedirs(results_folder, exist_ok=True)
        
        user_id = user.get('id')
        
        # Загружаем друзей
        profiles_cache[session_id] = {'status': 'processing', 'message': 'Загружаем список друзей...'}
        friends_handler = FriendsHandler(api)
        friends_data = friends_handler.get_all_friends(user_id)
        
        # Загружаем фотографии
        profiles_cache[session_id] = {'status': 'processing', 'message': 'Загружаем фотографии...'}
        photo_handler = PhotoHandler(api)
        photos = photo_handler.get_all_photos(user_id)
        
        # Скачиваем фотографии
        downloaded_photos = []
        if download_photos and photos:
            profiles_cache[session_id] = {'status': 'processing', 'message': 'Скачиваем фотографии...'}
            downloaded_photos = photo_handler.download_photos(
                photos, 
                results_folder,
                f"{user.get('first_name', '')} {user.get('last_name', '')}"
            )
        
        # Подготавливаем данные
        profiles_cache[session_id] = {'status': 'processing', 'message': 'Подготавливаем данные...'}
        user_data = DataPreparer.prepare_user_data(user)
        
        # Сохраняем данные
        FileExporter.save_json(user_data, f"{results_folder}/user_info.json")
        if friends_data:
            FileExporter.save_json(friends_data, f"{results_folder}/friends.json")
        if photos:
            FileExporter.save_json({'count': len(photos), 'items': photos}, f"{results_folder}/photos_info.json")
        
        # Сохраняем в кэш
        profiles_cache[session_id] = {
            'status': 'completed',
            'folder': results_folder,
            'user_data': user_data,
            'friends_data': friends_data,
            'photos_data': photos,
            'downloaded_photos': downloaded_photos,
            'username': username,
            'timestamp': timestamp
        }
        
    except Exception as e:
        profiles_cache[session_id] = {'status': 'error', 'message': str(e)}


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/parse', methods=['GET', 'POST'])
def parse():
    """Страница парсинга профиля"""
    if request.method == 'GET':
        return render_template('parse.html')
    
    # POST - запускаем парсинг
    profile_url = request.form.get('profile_url', '').strip()
    token = request.form.get('token', '').strip()
    download_photos = 'download_photos' in request.form
    
    if not profile_url:
        return render_template('parse.html', error='Введите URL или ID профиля')
    
    # Создаем сессию
    session_id = str(uuid.uuid4())
    
    # Запускаем асинхронный парсинг
    thread = threading.Thread(target=parse_profile_async, args=(profile_url, token, download_photos, session_id))
    thread.start()
    
    return redirect(url_for('parse_progress', session_id=session_id))


@app.route('/parse/progress/<session_id>')
def parse_progress(session_id):
    """Прогресс парсинга"""
    if session_id not in profiles_cache:
        return render_template('error.html', error='Сессия не найдена')
    
    data = profiles_cache[session_id]
    
    if data['status'] == 'completed':
        return redirect(url_for('parse_result', session_id=session_id))
    elif data['status'] == 'error':
        return render_template('error.html', error=data.get('message', 'Произошла ошибка'))
    else:
        return render_template('progress.html', 
                             message=data.get('message', 'Обработка...'),
                             session_id=session_id)


@app.route('/parse/result/<session_id>')
def parse_result(session_id):
    """Результат парсинга"""
    if session_id not in profiles_cache:
        return render_template('error.html', error='Сессия не найдена')
    
    data = profiles_cache[session_id]
    if data['status'] != 'completed':
        return redirect(url_for('parse_progress', session_id=session_id))
    
    return render_template('result.html',
                          user_data=data['user_data'],
                          friends_data=data['friends_data'],
                          photos_data=data['photos_data'],
                          folder=data['folder'],
                          username=data['username'])


@app.route('/compare', methods=['GET', 'POST'])
def compare():
    """Страница сравнения профилей"""
    if request.method == 'GET':
        # Получаем список сохраненных профилей
        saved_profiles = []
        if os.path.exists(RESULTS_FOLDER):
            for item in os.listdir(RESULTS_FOLDER):
                item_path = os.path.join(RESULTS_FOLDER, item)
                if os.path.isdir(item_path):
                    user_info_path = os.path.join(item_path, 'user_info.json')
                    if os.path.exists(user_info_path):
                        try:
                            with open(user_info_path, 'r', encoding='utf-8') as f:
                                user_data = json.load(f)
                                saved_profiles.append({
                                    'name': item,
                                    'path': item_path,
                                    'user': user_data
                                })
                        except:
                            pass
        
        return render_template('compare.html', saved_profiles=saved_profiles)
    
    # POST - запускаем сравнение
    profile1_url = request.form.get('profile1_url', '').strip()
    profile2_url = request.form.get('profile2_url', '').strip()
    profile1_path = request.form.get('profile1_path', '').strip()
    profile2_path = request.form.get('profile2_path', '').strip()
    token = request.form.get('token', '').strip()
    
    if not ((profile1_url or profile1_path) and (profile2_url or profile2_path)):
        return render_template('compare.html', error='Выберите два профиля для сравнения')
    
    # Загружаем профили
    api = get_api_client(token)
    
    try:
        # Профиль 1
        if profile1_path and os.path.exists(profile1_path):
            with open(os.path.join(profile1_path, 'user_info.json'), 'r', encoding='utf-8') as f:
                p1_raw = json.load(f)
                p1_profile = p1_raw.get('raw_data', p1_raw)
            with open(os.path.join(profile1_path, 'friends.json'), 'r', encoding='utf-8') as f:
                p1_friends = json.load(f)
            with open(os.path.join(profile1_path, 'photos_info.json'), 'r', encoding='utf-8') as f:
                p1_photos = json.load(f).get('items', [])
            p1 = {'profile': p1_profile, 'friends': p1_friends, 'photos': p1_photos}
        elif profile1_url:
            if not api:
                return render_template('compare.html', error='Необходим VK API токен')
            p1 = load_profile_from_url(api, profile1_url)
            if not p1:
                return render_template('compare.html', error='Не удалось загрузить первый профиль')
        else:
            return render_template('compare.html', error='Выберите первый профиль')
        
        # Профиль 2
        if profile2_path and os.path.exists(profile2_path):
            with open(os.path.join(profile2_path, 'user_info.json'), 'r', encoding='utf-8') as f:
                p2_raw = json.load(f)
                p2_profile = p2_raw.get('raw_data', p2_raw)
            with open(os.path.join(profile2_path, 'friends.json'), 'r', encoding='utf-8') as f:
                p2_friends = json.load(f)
            with open(os.path.join(profile2_path, 'photos_info.json'), 'r', encoding='utf-8') as f:
                p2_photos = json.load(f).get('items', [])
            p2 = {'profile': p2_profile, 'friends': p2_friends, 'photos': p2_photos}
        elif profile2_url:
            if not api:
                return render_template('compare.html', error='Необходим VK API токен')
            p2 = load_profile_from_url(api, profile2_url)
            if not p2:
                return render_template('compare.html', error='Не удалось загрузить второй профиль')
        else:
            return render_template('compare.html', error='Выберите второй профиль')
        
        # Сравниваем
        comparer = ProfileComparer()
        result = comparer.compare_profiles(
            p1['profile'], p2['profile'],
            friends1_data=p1.get('friends'),
            friends2_data=p2.get('friends'),
            photos1_data=p1.get('photos'),
            photos2_data=p2.get('photos')
        )
        
        # Сохраняем результат
        comparison_id = str(uuid.uuid4())
        comparisons_cache[comparison_id] = {
            'result': result,
            'profile1': p1['profile'],
            'profile2': p2['profile']
        }
        
        return redirect(url_for('comparison_result', comparison_id=comparison_id))
        
    except Exception as e:
        return render_template('compare.html', error=f'Ошибка при сравнении: {str(e)}')


def load_profile_from_url(api, profile_url):
    """Загружает профиль по URL"""
    user = api.get_user_info(profile_url)
    if not user:
        return None
    
    user_id = user.get('id')
    
    # Загружаем друзей
    friends_handler = FriendsHandler(api)
    friends_data = friends_handler.get_all_friends(user_id)
    
    # Загружаем фото
    photo_handler = PhotoHandler(api)
    photos_data = photo_handler.get_all_photos(user_id)
    
    return {
        'profile': user,
        'friends': friends_data,
        'photos': photos_data
    }


@app.route('/comparison/<comparison_id>')
def comparison_result(comparison_id):
    """Результат сравнения"""
    if comparison_id not in comparisons_cache:
        return render_template('error.html', error='Сравнение не найдено')
    
    data = comparisons_cache[comparison_id]
    result = data['result']
    p1 = data['profile1']
    p2 = data['profile2']
    
    return render_template('comparison.html',
                          result=result,
                          profile1=p1,
                          profile2=p2)


@app.route('/profiles')
def profiles():
    """Список сохраненных профилей"""
    saved_profiles = []
    if os.path.exists(RESULTS_FOLDER):
        for item in os.listdir(RESULTS_FOLDER):
            item_path = os.path.join(RESULTS_FOLDER, item)
            if os.path.isdir(item_path):
                user_info_path = os.path.join(item_path, 'user_info.json')
                if os.path.exists(user_info_path):
                    try:
                        with open(user_info_path, 'r', encoding='utf-8') as f:
                            user_data = json.load(f)
                            saved_profiles.append({
                                'name': item,
                                'path': item_path,
                                'user': user_data.get('raw_data', user_data)
                            })
                    except:
                        pass
    
    return render_template('profiles.html', profiles=saved_profiles)


@app.route('/profile/<path:profile_path>')
def view_profile(profile_path):
    """Просмотр профиля"""
    full_path = os.path.join(RESULTS_FOLDER, profile_path)
    
    if not os.path.exists(full_path):
        return render_template('error.html', error='Профиль не найден')
    
    try:
        with open(os.path.join(full_path, 'user_info.json'), 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        friends_data = None
        friends_path = os.path.join(full_path, 'friends.json')
        if os.path.exists(friends_path):
            with open(friends_path, 'r', encoding='utf-8') as f:
                friends_data = json.load(f)
        
        photos_data = None
        photos_path = os.path.join(full_path, 'photos_info.json')
        if os.path.exists(photos_path):
            with open(photos_path, 'r', encoding='utf-8') as f:
                photos_data = json.load(f)
        
        return render_template('view_profile.html',
                              user_data=user_data,
                              friends_data=friends_data,
                              photos_data=photos_data,
                              profile_path=profile_path)
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/photos/<path:filename>')
def serve_photos(filename):
    """Служит фотографии из папки результатов"""
    return send_from_directory(RESULTS_FOLDER, filename)


@app.route('/static/photos/<path:profile>/<path:filename>')
def serve_profile_photos(profile, filename):
    """Служит фотографии профиля"""
    path = os.path.join(RESULTS_FOLDER, profile, 'photos', filename)
    if os.path.exists(path):
        return send_from_directory(os.path.join(RESULTS_FOLDER, profile, 'photos'), filename)
    return "Not found", 404


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', error='Страница не найдена'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error='Внутренняя ошибка сервера'), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌐 VK Parser Web - Запуск сервера")
    print("="*60)
    print("Откройте в браузере: http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)
