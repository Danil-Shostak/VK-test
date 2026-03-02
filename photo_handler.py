# photo_handler.py
# Работа с фотографиями

import requests
import time
import os
from config import MAX_PHOTOS_PER_REQUEST

class PhotoHandler:
    def __init__(self, api_client):
        self.api = api_client
    
    def get_all_photos(self, user_id):
        """Получает все фотографии пользователя"""
        all_photos = []
        offset = 0
        
        print(f"\n📸 Загрузка фотографий пользователя {user_id}...")
        
        while True:
            params = {
                'owner_id': user_id,
                'offset': offset,
                'count': MAX_PHOTOS_PER_REQUEST,
                'extended': 1,
                'photo_sizes': 1
            }
            
            response = self.api._request('photos.getAll', params)
            
            if not response:
                break
            
            items = response.get('items', [])
            count_total = response.get('count', 0)
            
            all_photos.extend(items)
            print(f"   Загружено {len(all_photos)} из {count_total} фотографий...")
            
            if len(items) < MAX_PHOTOS_PER_REQUEST or len(all_photos) >= count_total:
                break
                
            offset += len(items)
            time.sleep(0.3)
        
        print(f"✅ Загружено всего {len(all_photos)} фотографий")
        return all_photos
    
    def download_photos(self, photos_list, save_dir, user_name=""):
        """Скачивает фотографии на диск"""
        if not photos_list:
            return []
        
        photos_dir = os.path.join(save_dir, 'photos')
        if not os.path.exists(photos_dir):
            os.makedirs(photos_dir)
        
        downloaded = []
        print(f"\n💾 Скачивание {len(photos_list)} фотографий...")
        
        for i, photo in enumerate(photos_list):
            try:
                max_size_url = self._get_best_photo_url(photo)
                
                if max_size_url:
                    timestamp = photo.get('date', int(time.time()))
                    filename = f"photo_{i+1:04d}_{timestamp}.jpg"
                    filepath = os.path.join(photos_dir, filename)
                    
                    img_response = requests.get(max_size_url, stream=True)
                    if img_response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            for chunk in img_response.iter_content(chunk_size=1024):
                                f.write(chunk)
                        downloaded.append(filepath)
                        
                        if (i+1) % 10 == 0 or i+1 == len(photos_list):
                            print(f"   Скачано {i+1}/{len(photos_list)} фото")
                
                if (i+1) % 20 == 0:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"   ⚠️ Ошибка при скачивании фото {i+1}: {e}")
        
        print(f"✅ Скачано {len(downloaded)} фотографий")
        return downloaded
    
    def _get_best_photo_url(self, photo):
        """Находит URL самого большого размера фото"""
        max_size_url = None
        max_dimensions = 0
        
        if 'sizes' in photo:
            for size in photo['sizes']:
                dimensions = size.get('width', 0) * size.get('height', 0)
                if dimensions > max_dimensions:
                    max_dimensions = dimensions
                    max_size_url = size.get('url')
        elif 'photo_max_orig' in photo:
            max_size_url = photo['photo_max_orig']
        elif 'photo_max' in photo:
            max_size_url = photo['photo_max']
        
        return max_size_url