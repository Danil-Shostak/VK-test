# html_generator.py
import os
from datetime import datetime
from friends_handler import FriendsHandler  # Добавляем импорт

class HTMLGenerator:
    @staticmethod
    def generate_full_site(user_data, friends_data, photos, photos_dir, output_dir):
        """Генерирует один большой сайт со всей информацией"""
        
        # Получаем статистику по друзьям, если они есть
        friend_stats = {}
        if friends_data and friends_data.get('items'):
            fh = FriendsHandler(None)
            friend_stats = fh.analyze_friends_stats(friends_data['items'])
        
        # Количество друзей для отображения в табе
        friends_count = friends_data.get('total', 0) if friends_data else 0
        
        # Количество фотографий
        photos_count = len(photos) if photos else 0
        
        html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VK Профиль: {user_data['basic_info'].get('first_name', '')} {user_data['basic_info'].get('last_name', '')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #f0f2f5;
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, #4a76a8 0%, #2a4a6a 100%);
            color: white;
            padding: 30px 0;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        .header .date {{
            opacity: 0.9;
            font-size: 14px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        /* Профиль */
        .profile-card {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            gap: 30px;
            align-items: center;
        }}
        
        .profile-avatar {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            overflow: hidden;
            border: 4px solid #4a76a8;
        }}
        
        .profile-avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .profile-info {{
            flex: 1;
        }}
        
        .profile-name {{
            font-size: 28px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}
        
        .profile-status {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            margin-bottom: 15px;
        }}
        
        .status-online {{
            background: #4caf50;
            color: white;
        }}
        
        .status-offline {{
            background: #9e9e9e;
            color: white;
        }}
        
        .profile-details {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .detail-item {{
            background: #f5f5f5;
            padding: 10px 15px;
            border-radius: 10px;
        }}
        
        .detail-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        
        .detail-value {{
            font-size: 16px;
            font-weight: 600;
            color: #333;
        }}
        
        /* Табы */
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .tab-button {{
            padding: 12px 24px;
            background: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            color: #666;
            transition: all 0.3s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .tab-button:hover {{
            background: #4a76a8;
            color: white;
            transform: translateY(-2px);
        }}
        
        .tab-button.active {{
            background: #4a76a8;
            color: white;
        }}
        
        .tab-content {{
            display: none;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        /* Секции */
        .section-title {{
            font-size: 24px;
            color: #4a76a8;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #4a76a8;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        /* Друзья */
        .friends-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .friend-card {{
            background: #f8f9fa;
            border-radius: 15px;
            padding: 15px;
            display: flex;
            align-items: center;
            gap: 15px;
            transition: all 0.3s;
        }}
        
        .friend-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        
        .friend-avatar {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            overflow: hidden;
        }}
        
        .friend-avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .friend-info {{
            flex: 1;
        }}
        
        .friend-name {{
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .friend-details {{
            font-size: 12px;
            color: #666;
        }}
        
        .friend-online {{
            color: #4caf50;
            font-weight: 600;
        }}
        
        .friend-offline {{
            color: #999;
        }}
        
        /* Фотографии */
        .photos-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .photo-card {{
            position: relative;
            border-radius: 10px;
            overflow: hidden;
            cursor: pointer;
            aspect-ratio: 1;
        }}
        
        .photo-card img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s;
        }}
        
        .photo-card:hover img {{
            transform: scale(1.1);
        }}
        
        .photo-overlay {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.7));
            color: white;
            padding: 10px;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.3s;
            display: flex;
            gap: 10px;
        }}
        
        .photo-card:hover .photo-overlay {{
            opacity: 1;
        }}
        
        /* Статистика друзей */
        .stats-section {{
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .city-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
        }}
        
        .city-item {{
            background: white;
            padding: 10px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
        }}
        
        /* Модальное окно */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
        }}
        
        .modal-content {{
            margin: auto;
            display: block;
            max-width: 90%;
            max-height: 90%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }}
        
        .close {{
            position: absolute;
            right: 35px;
            top: 15px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }}
        
        .nav-button {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(255,255,255,0.1);
            color: white;
            padding: 16px;
            font-size: 24px;
            border: none;
            cursor: pointer;
            transition: background 0.3s;
        }}
        
        .nav-button:hover {{
            background: rgba(255,255,255,0.3);
        }}
        
        .prev {{
            left: 20px;
        }}
        
        .next {{
            right: 20px;
        }}
        
        .photo-counter {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: white;
            font-size: 16px;
            background: rgba(0,0,0,0.5);
            padding: 5px 15px;
            border-radius: 20px;
        }}
        
        .search-box {{
            width: 100%;
            padding: 10px;
            margin: 20px 0;
            border: 2px solid #4a76a8;
            border-radius: 10px;
            font-size: 16px;
        }}
        
        @media (max-width: 768px) {{
            .profile-card {{
                flex-direction: column;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 VK Профиль: {user_data['basic_info'].get('first_name', '')} {user_data['basic_info'].get('last_name', '')}</h1>
        <div class="date">Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
    </div>
    
    <div class="container">
        <!-- Карточка профиля -->
        <div class="profile-card">
            <div class="profile-avatar">
                <img src="{user_data['basic_info'].get('photo', 'https://vk.com/images/camera_200.png')}" alt="Avatar">
            </div>
            <div class="profile-info">
                <div class="profile-name">
                    {user_data['basic_info'].get('first_name', '')} {user_data['basic_info'].get('last_name', '')}
                </div>
                <span class="profile-status {'status-online' if user_data['online_status']['online'] else 'status-offline'}">
                    {'🟢 Онлайн' if user_data['online_status']['online'] else '⚫ Офлайн'}
                </span>
                <div class="profile-details">
                    <div class="detail-item">
                        <div class="detail-label">ID</div>
                        <div class="detail-value">{user_data['basic_info'].get('id', '')}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Пол</div>
                        <div class="detail-value">{user_data['basic_info'].get('sex', 'Не указан')}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Дата рождения</div>
                        <div class="detail-value">{user_data['basic_info'].get('birth_date', 'Не указана')}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Город</div>
                        <div class="detail-value">{user_data['basic_info'].get('city', 'Не указан')}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Страна</div>
                        <div class="detail-value">{user_data['basic_info'].get('country', 'Не указана')}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Табы -->
        <div class="tabs">
            <button class="tab-button active" onclick="showTab('info')">📋 Информация</button>
            <button class="tab-button" onclick="showTab('friends')">👥 Друзья ({friends_count})</button>
            <button class="tab-button" onclick="showTab('photos')">📸 Фотографии ({photos_count})</button>
        </div>
        
        <!-- Вкладка с информацией -->
        <div id="tab-info" class="tab-content active">
"""
        
        # Статистика
        if user_data['statistics']:
            html_content += """
            <div class="section-title">📊 Статистика</div>
            <div class="stats-grid">
"""
            if 'followers_count' in user_data['statistics']:
                html_content += f"""
                <div class="stat-card">
                    <div class="stat-number">{user_data['statistics']['followers_count']}</div>
                    <div class="stat-label">Подписчиков</div>
                </div>
"""
            
            if 'counters' in user_data['statistics']:
                counters = user_data['statistics']['counters']
                stat_map = {'friends': 'Друзья', 'photos': 'Фотографии',
                           'videos': 'Видео', 'audios': 'Аудиозаписи',
                           'groups': 'Группы', 'gifts': 'Подарки'}
                for key, value in counters.items():
                    if key in stat_map and value:
                        html_content += f"""
                <div class="stat-card">
                    <div class="stat-number">{value}</div>
                    <div class="stat-label">{stat_map[key]}</div>
                </div>
"""
            html_content += """
            </div>
"""
        
        # Контакты
        if user_data['contacts']:
            html_content += """
            <div class="section-title">📱 Контакты</div>
            <div class="stats-grid">
"""
            for key, value in user_data['contacts'].items():
                icon = {'site': '🌐', 'instagram': '📷', 'facebook': '👤',
                       'twitter': '🐦', 'skype': '💬'}.get(key, '🔗')
                html_content += f"""
                <div class="stat-card" style="background: linear-gradient(135deg, #4a76a8 0%, #2a4a6a 100%)">
                    <div class="stat-number">{icon}</div>
                    <div class="stat-label">{key.capitalize()}</div>
                    <div style="font-size: 12px; margin-top: 5px;"><a href="{value}" target="_blank" style="color: white;">{value}</a></div>
                </div>
"""
            html_content += """
            </div>
"""
        
        # Интересы
        if user_data['interests']:
            html_content += """
            <div class="section-title">🎯 Интересы</div>
            <div class="stats-grid">
"""
            for key, value in user_data['interests'].items():
                key_rus = {'activities': 'Деятельность', 'interests': 'Интересы',
                          'music': 'Музыка', 'movies': 'Фильмы', 'books': 'Книги',
                          'games': 'Игры', 'quotes': 'Цитаты'}.get(key, key)
                html_content += f"""
                <div class="stat-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
                    <div class="stat-label">{key_rus}</div>
                    <div style="font-size: 14px; margin-top: 10px;">{value}</div>
                </div>
"""
            html_content += """
            </div>
"""
        
        # Образование
        if user_data['education_career']:
            html_content += """
            <div class="section-title">🎓 Образование и карьера</div>
            <div class="stats-grid">
"""
            if 'education' in user_data['education_career']:
                edu = user_data['education_career']['education']
                if 'university' in edu:
                    html_content += f"""
                <div class="stat-card" style="background: linear-gradient(135deg, #e67e22 0%, #d35400 100%)">
                    <div class="stat-label">ВУЗ</div>
                    <div style="font-size: 14px; margin-top: 10px;">{edu['university']}</div>
                </div>
"""
                if 'faculty' in edu:
                    html_content += f"""
                <div class="stat-card" style="background: linear-gradient(135deg, #e67e22 0%, #d35400 100%)">
                    <div class="stat-label">Факультет</div>
                    <div style="font-size: 14px; margin-top: 10px;">{edu['faculty']}</div>
                </div>
"""
                if 'graduation' in edu:
                    html_content += f"""
                <div class="stat-card" style="background: linear-gradient(135deg, #e67e22 0%, #d35400 100%)">
                    <div class="stat-label">Год выпуска</div>
                    <div style="font-size: 14px; margin-top: 10px;">{edu['graduation']}</div>
                </div>
"""
            
            if 'career' in user_data['education_career']:
                for job in user_data['education_career']['career'][:3]:
                    company = job.get('company', '')
                    position = job.get('position', '')
                    if company and position:
                        html_content += f"""
                <div class="stat-card" style="background: linear-gradient(135deg, #27ae60 0%, #229954 100%)">
                    <div class="stat-label">Работа</div>
                    <div style="font-size: 14px; margin-top: 10px;">{position}<br>{company}</div>
                </div>
"""
            html_content += """
            </div>
"""
        
        html_content += """
        </div>
        
        <!-- Вкладка с друзьями -->
        <div id="tab-friends" class="tab-content">
"""
        
        if friends_data and friends_data.get('items') and friend_stats:
            html_content += f"""
            <div class="section-title">📊 Статистика друзей</div>
            <div class="stats-grid">
                <div class="stat-card" style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)">
                    <div class="stat-number">{friend_stats.get('sex', {}).get('female', 0)}</div>
                    <div class="stat-label">Женщины</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #3498db 0%, #2980b9 100%)">
                    <div class="stat-number">{friend_stats.get('sex', {}).get('male', 0)}</div>
                    <div class="stat-label">Мужчины</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%)">
                    <div class="stat-number">{friend_stats.get('online', 0)}</div>
                    <div class="stat-label">Сейчас онлайн</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #f1c40f 0%, #f39c12 100%)">
                    <div class="stat-number">{friend_stats.get('avg_age', 0):.1f}</div>
                    <div class="stat-label">Средний возраст</div>
                </div>
            </div>
            
            <div class="section-title">🏙️ Топ городов</div>
            <div class="city-stats">
"""
            for city, count in list(friend_stats.get('cities', {}).items())[:10]:
                if city != 'Не указан':
                    html_content += f"""
                <div class="city-item">
                    <span>{city}</span>
                    <span><strong>{count}</strong></span>
                </div>
"""
            
            html_content += """
            </div>
            
            <div class="section-title">👥 Все друзья</div>
            <input type="text" class="search-box" id="friend-search" placeholder="🔍 Поиск по имени..." onkeyup="searchFriends()">
            <div class="friends-grid" id="friends-grid">
"""
            
            for friend in friends_data['items']:
                online_class = "friend-online" if friend.get('online') else "friend-offline"
                online_text = "🟢 Онлайн" if friend.get('online') else "⚫ Офлайн"
                city = friend.get('city', {}).get('title', '') if friend.get('city') else ''
                age = ''
                if friend.get('bdate') and len(friend['bdate'].split('.')) == 3:
                    try:
                        year = int(friend['bdate'].split('.')[2])
                        age = f", {datetime.now().year - year} лет"
                    except:
                        pass
                
                html_content += f"""
                <div class="friend-card" data-name="{friend.get('first_name', '')} {friend.get('last_name', '')}">
                    <div class="friend-avatar">
                        <img src="{friend.get('photo_100', 'https://vk.com/images/camera_50.png')}" alt="">
                    </div>
                    <div class="friend-info">
                        <div class="friend-name">{friend.get('first_name', '')} {friend.get('last_name', '')}</div>
                        <div class="friend-details">
                            <span class="{online_class}">{online_text}</span><br>
                            {city}{age}
                        </div>
                    </div>
                </div>
"""
            
            html_content += """
            </div>
"""
        else:
            html_content += "<p>❌ Список друзей недоступен</p>"
        
        html_content += """
        </div>
        
        <!-- Вкладка с фотографиями -->
        <div id="tab-photos" class="tab-content">
"""
        
        if photos and len(photos) > 0:
            html_content += f"""
            <div class="section-title">📸 Все фотографии ({len(photos)})</div>
            <div class="photos-grid" id="photos-grid">
"""
            for i, photo_path in enumerate(photos):
                rel_path = os.path.basename(photo_path)
                html_content += f"""
                <div class="photo-card" onclick="openModal({i})">
                    <img src="photos/{rel_path}" alt="Photo {i+1}">
                </div>
"""
            
            html_content += """
            </div>
"""
        else:
            html_content += "<p>❌ Фотографии недоступны</p>"
        
        # Модальное окно для фото
        html_content += f"""
        </div>
    </div>
    
    <!-- Модальное окно для фотографий -->
    <div id="modal" class="modal">
        <span class="close" onclick="closeModal()">&times;</span>
        <button class="nav-button prev" onclick="changeImage(-1)">❮</button>
        <button class="nav-button next" onclick="changeImage(1)">❯</button>
        <img class="modal-content" id="modal-img">
        <div class="photo-counter" id="modal-counter">1 / {photos_count}</div>
    </div>
    
    <script>
        // Массив фотографий
        const photos = [
"""
        
        if photos:
            for i, photo_path in enumerate(photos):
                rel_path = os.path.basename(photo_path)
                html_content += f"            'photos/{rel_path}',\n"
        
        html_content += """
        ];
        
        let currentImageIndex = 0;
        
        // Переключение табов
        function showTab(tabName) {
            // Скрываем все табы
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Убираем активный класс у всех кнопок
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Показываем выбранный таб
            document.getElementById('tab-' + tabName).classList.add('active');
            
            // Активируем кнопку (находим кнопку по тексту или data-атрибуту)
            const buttons = document.querySelectorAll('.tab-button');
            for (let btn of buttons) {
                if (btn.textContent.includes(tabName === 'info' ? 'Информация' : 
                                              tabName === 'friends' ? 'Друзья' : 'Фотографии')) {
                    btn.classList.add('active');
                    break;
                }
            }
        }
        
        // Поиск по друзьям
        function searchFriends() {
            const searchText = document.getElementById('friend-search').value.toLowerCase();
            const friends = document.querySelectorAll('.friend-card');
            
            friends.forEach(friend => {
                const name = friend.getAttribute('data-name').toLowerCase();
                if (name.includes(searchText)) {
                    friend.style.display = 'flex';
                } else {
                    friend.style.display = 'none';
                }
            });
        }
        
        // Модальное окно для фото
        function openModal(index) {
            if (photos.length === 0) return;
            currentImageIndex = index;
            document.getElementById('modal').style.display = 'block';
            document.getElementById('modal-img').src = photos[currentImageIndex];
            updateCounter();
        }
        
        function closeModal() {
            document.getElementById('modal').style.display = 'none';
        }
        
        function changeImage(direction) {
            if (photos.length === 0) return;
            currentImageIndex += direction;
            if (currentImageIndex >= photos.length) {
                currentImageIndex = 0;
            } else if (currentImageIndex < 0) {
                currentImageIndex = photos.length - 1;
            }
            document.getElementById('modal-img').src = photos[currentImageIndex];
            updateCounter();
        }
        
        function updateCounter() {
            document.getElementById('modal-counter').innerText = 
                (currentImageIndex + 1) + ' / ' + photos.length;
        }
        
        // Клавиши навигации
        document.addEventListener('keydown', function(e) {
            if (document.getElementById('modal').style.display === 'block') {
                if (e.key === 'Escape') {
                    closeModal();
                } else if (e.key === 'ArrowLeft') {
                    changeImage(-1);
                } else if (e.key === 'ArrowRight') {
                    changeImage(1);
                }
            }
        });
        
        // Закрытие по клику вне изображения
        document.getElementById('modal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });
    </script>
</body>
</html>
"""
        
        index_path = os.path.join(output_dir, 'index.html')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Сайт создан: {index_path}")