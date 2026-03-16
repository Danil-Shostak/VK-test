# visual_matcher.py
# Модуль визуального анализа фотографий профилей
# С интеграцией распознавания лиц

import os
import sys
import io
import json
import hashlib
import requests
from typing import Dict, List, Tuple, Optional
from collections import Counter
from datetime import datetime

# Импортируем модули распознавания лиц
FACE_RECOGNITION_AVAILABLE = False
CV2_AVAILABLE = False
MEDIAPIPE_AVAILABLE = False

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    pass

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    pass

try:
    from mediapipe.tasks import python as mp_tasks
    from mediapipe import Image, ImageFormat
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    pass

import numpy as np


class VisualMatcher:
    """
    Класс для визуального анализа фотографий профилей
    
    Функции:
    - Извлечение метаданных из фотографий
    - Анализ визуальных паттернов
    - Сравнение аватарок профилей
    - Распознавание и сравнение лиц (ИНТЕГРИРОВАННО)
    """
    
    # Типичные размеры аватарок VK
    AVATAR_SIZES = ['photo_50', 'photo_100', 'photo_200', 'photo_400', 'photo_max', 'photo_max_orig']
    
    # Единый порог для определения совпадения лиц
    FACE_MATCH_THRESHOLD = 0.6  # евклидово расстояние для face_recognition
    
    def __init__(self):
        self.face_engine = None
        self.opencv_recognizer = None
        self.mediapipe_recognizer = None
        
        # Инициализируем доступные движки распознавания лиц
        self._init_face_recognition()
    
    def _init_face_recognition(self):
        """Инициализирует доступные движки распознавания лиц"""
        
        # 1. Пробуем face_recognition (наиболее точный)
        if FACE_RECOGNITION_AVAILABLE:
            try:
                self.face_engine = FaceRecognitionEngine()
                if self.face_engine.is_available:
                    print("[OK] FaceRecognition engine initialized")
            except Exception as e:
                print("[X] Initialization error: " + str(e))
        
        # 2. Пробуем OpenCV (fallback)
        if CV2_AVAILABLE and not self.face_engine:
            try:
                self.opencv_recognizer = OpenCVFaceRecognizer()
                if self.opencv_recognizer.is_available:
                    print("[OK] OpenCV FaceRecognizer initialized")
            except Exception as e:
                print("[X] OpenCV init error: " + str(e))
        
        # 3. Пробуем MediaPipe (fallback)
        if MEDIAPIPE_AVAILABLE and not self.face_engine:
            try:
                self.mediapipe_recognizer = MediaPipeFaceRecognizer()
                if self.mediapipe_recognizer.is_available:
                    print("[OK] MediaPipe FaceRecognizer initialized")
            except Exception as e:
                print("[X] MediaPipe init error: " + str(e))
    
    def get_avatar_url(self, user_data: Dict) -> Optional[str]:
        """
        Извлекает URL аватарки профиля
        
        Args:
            user_data: Данные пользователя от VK API
        """
        
        # Пробуем получить оригинальное фото
        for size in self.AVATAR_SIZES:
            if size in user_data and user_data[size]:
                return user_data[size]
        
        return None
    
    def download_avatar(self, avatar_url: str, save_path: str) -> bool:
        """
        Скачивает аватарку по URL
        
        Args:
            avatar_url: URL аватарки
            save_path: Путь для сохранения
            
        Returns:
            True если успешно
        """
        try:
            response = requests.get(avatar_url, timeout=10)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            print(f"Ошибка скачивания аватарки: {e}")
        return False
    
    def analyze_photo_collection(self, photos_data: List[Dict]) -> Dict[str, any]:
        """
        Анализирует коллекцию фотографий пользователя
        
        Args:
            photos_data: Список фотографий от VK API
        """
        
        if not photos_data:
            return {
                'total_photos': 0,
                'has_photos': False,
                'photo_analysis': 'Нет фотографий для анализа'
            }
        
        # Подсчет по типам
        sizes_counter = Counter()
        likes_counter = []
        comments_counter = []
        dates = []
        
        for photo in photos_data:
            # Анализируем размеры
            if 'sizes' in photo:
                for size in photo['sizes']:
                    sizes_counter[size.get('type', 'unknown')] += 1
            
            # Лайки
            if 'likes' in photo:
                likes_counter.append(photo['likes'].get('count', 0))
            
            # Комментарии
            if 'comments' in photo:
                comments_counter.append(photo['comments'].get('count', 0))
            
            # Даты
            if 'date' in photo:
                dates.append(photo['date'])
        
        # Статистика лайков
        avg_likes = sum(likes_counter) / len(likes_counter) if likes_counter else 0
        max_likes = max(likes_counter) if likes_counter else 0
        
        # Анализ дат (активность)
        date_range = None
        if dates:
            min_date = min(dates)
            max_date = max(dates)
            date_range = {
                'first_photo': datetime.fromtimestamp(min_date).strftime('%Y-%m-%d'),
                'last_photo': datetime.fromtimestamp(max_date).strftime('%Y-%m-%d'),
                'days_span': max_date - min_date
            }
        
        # Анализ текста на фото
        texts_on_photos = []
        for photo in photos_data:
            if 'text' in photo and photo['text']:
                texts_on_photos.append(photo['text'])
        
        return {
            'total_photos': len(photos_data),
            'has_photos': len(photos_data) > 0,
            'size_distribution': dict(sizes_counter),
            'likes_stats': {
                'avg': avg_likes,
                'max': max_likes,
                'total': sum(likes_counter)
            },
            'comments_stats': {
                'avg': sum(comments_counter) / len(comments_counter) if comments_counter else 0,
                'total': sum(comments_counter)
            },
            'date_range': date_range,
            'texts_on_photos': texts_on_photos[:10],
        }
    
    def compare_photo_collections(self, photos1: List[Dict], photos2: List[Dict]) -> Dict[str, any]:
        """
        Сравнивает две коллекции фотографий
        
        Args:
            photos1: Фотографии первого профиля
            photos2: Фотографии второго профиля
        """
        
        analysis1 = self.analyze_photo_collection(photos1)
        analysis2 = self.analyze_photo_collection(photos2)
        
        # Проверяем идентичные фото (по likes + comments + date)
        def get_photo_signature(photo):
            return f"{photo.get('likes', {}).get('count', 0)}_{photo.get('comments', {}).get('count', 0)}_{photo.get('date', 0)}"
        
        signatures1 = {get_photo_signature(p) for p in photos1 if get_photo_signature(p)}
        signatures2 = {get_photo_signature(p) for p in photos2 if get_photo_signature(p)}
        
        common_signatures = signatures1 & signatures2
        
        # Сравниваем активность
        activity_score = 0.0
        if analysis1['has_photos'] and analysis2['has_photos']:
            likes1 = analysis1['likes_stats']['avg']
            likes2 = analysis2['likes_stats']['avg']
            
            if likes1 > 0 and likes2 > 0:
                likes_ratio = min(likes1, likes2) / max(likes1, likes2)
                activity_score = likes_ratio
        
        return {
            'collection1_analysis': analysis1,
            'collection2_analysis': analysis2,
            'identical_photos_count': len(common_signatures),
            'common_photo_signatures': list(common_signatures),
            'activity_similarity': activity_score,
            'interpretation': self._interpret_photo_comparison(len(common_signatures), activity_score)
        }
    
    def compare_avatars_by_url(self, avatar_url1: str, avatar_url2: str, temp_dir: str = "temp_avatars") -> Dict[str, any]:
        """
        Сравнивает аватарки двух профилей по URL с использованием распознавания лиц
        
        Args:
            avatar_url1: URL первой аватарки
            avatar_url2: URL второй аватарки
            temp_dir: Временная папка для скачанных аватарок
            
        Returns:
            Результат сравнения лиц
        """
        os.makedirs(temp_dir, exist_ok=True)
        
        # Скачиваем аватарки
        path1 = os.path.join(temp_dir, "avatar1.jpg")
        path2 = os.path.join(temp_dir, "avatar2.jpg")
        
        success1 = self.download_avatar(avatar_url1, path1)
        success2 = self.download_avatar(avatar_url2, path2)
        
        if not success1 or not success2:
            return {
                'success': False,
                'error': 'Не удалось скачать аватарки',
                'method': 'none'
            }
        
        # Сравниваем лица
        result = self.compare_faces(path1, path2)
        
        # Удаляем временные файлы
        try:
            if os.path.exists(path1):
                os.remove(path1)
            if os.path.exists(path2):
                os.remove(path2)
        except:
            pass
        
        return result
    
    def compare_faces(self, image1_path: str, image2_path: str) -> Dict[str, any]:
        """
        Сравнивает лица на двух изображениях
        
        Args:
            image1_path: Путь к первому изображению
            image2_path: Путь ко второму изображению
            
        Returns:
            Результат сравнения
        """
        # Пробуем использовать наиболее точный метод
        if self.face_engine:
            result = self.face_engine.compare_faces(image1_path, image2_path)
            if result.get('success'):
                result['method'] = 'face_recognition'
                result['face_match'] = result.get('match', False)
                result['face_similarity'] = result.get('similarity_percentage', 0)
                return result
        
        if self.opencv_recognizer:
            result = self.opencv_recognizer.compare_faces(image1_path, image2_path)
            if result.get('success'):
                result['method'] = 'opencv'
                result['face_match'] = result.get('match', False)
                result['face_similarity'] = result.get('similarity_percentage', 0)
                return result
        
        if self.mediapipe_recognizer:
            result = self.mediapipe_recognizer.compare_faces(image1_path, image2_path)
            if result.get('success'):
                result['method'] = 'mediapipe'
                result['face_match'] = result.get('match', False)
                result['face_similarity'] = result.get('similarity_percentage', 0)
                return result
        
        return {
            'success': False,
            'error': 'Ни один модуль распознавания лиц недоступен',
            'method': 'none',
            'face_match': False,
            'face_similarity': 0
        }
    
    def detect_faces_in_image(self, image_path: str) -> Dict[str, any]:
        """
        Обнаруживает лица на изображении
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Информация о найденных лицах
        """
        if self.face_engine:
            result = self.face_engine.detect_faces(image_path)
            result['method'] = 'face_recognition'
            return result
        
        if self.opencv_recognizer:
            result = self.opencv_recognizer.detect_faces(image_path)
            result['method'] = 'opencv'
            return result
        
        if self.mediapipe_recognizer:
            result = self.mediapipe_recognizer.detect_faces(image_path)
            result['method'] = 'mediapipe'
            return result
        
        return {
            'success': False,
            'error': 'Ни один модуль распознавания лиц недоступен',
            'faces_found': 0
        }
    
    def _interpret_photo_comparison(self, identical_count: int, activity_score: float) -> str:
        """Интерпретирует результат сравнения фотографий"""
        
        if identical_count >= 3:
            return "Найдены идентичные фотографии - высокая вероятность совпадения"
        elif identical_count >= 1:
            return "Найдены общие фотографии"
        elif activity_score > 0.7:
            return "Похожая активность на фотографиях"
        elif activity_score > 0.4:
            return "Частично похожая активность"
        else:
            return "Разные паттерны фотографий"
    
    def analyze_avatar(self, user_data: Dict) -> Dict[str, any]:
        """
        Анализирует аватарку профиля
        
        Args:
            user_data: Данные пользователя
        """
        
        avatar_url = self.get_avatar_url(user_data)
        
        if not avatar_url:
            return {
                'has_avatar': False,
                'avatar_url': None,
                'is_default': True
            }
        
        # Проверяем, является ли аватар стандартным
        is_default = (
            'camera_200' in avatar_url or
            'deactivated' in avatar_url
        )
        
        return {
            'has_avatar': True,
            'avatar_url': avatar_url,
            'is_default': is_default,
            'likely_active': not is_default
        }
    
    def compare_avatars(self, user1_data: Dict, user2_data: Dict) -> Dict[str, any]:
        """
        Сравнивает аватарки двух профилей
        
        Args:
            user1_data: Данные первого пользователя
            user2_data: Данные второго пользователя
        """
        
        avatar1 = self.get_avatar_url(user1_data)
        avatar2 = self.get_avatar_url(user2_data)
        
        # Если нет аватарок
        if not avatar1 and not avatar2:
            return {
                'both_no_avatar': True,
                'match_score': 0.0,
                'interpretation': 'У обоих профилей нет аватарок'
            }
        
        if not avatar1 or not avatar2:
            return {
                'one_has_avatar': True,
                'match_score': 0.1,
                'interpretation': 'Только один профиль имеет аватарку'
            }
        
        # Сравниваем URL аватарок
        exact_match = (avatar1 == avatar2)
        
        # Если URL совпадают - это точное совпадение
        if exact_match:
            return {
                'exact_match': True,
                'both_have_avatars': True,
                'match_score': 1.0,
                'interpretation': 'Аватарки полностью совпадают (одинаковое фото)'
            }
        
        # Если URL разные - пробуем распознавание лиц
        print("\n🔍 Сравнение аватарок методом распознавания лиц...")
        face_result = self.compare_avatars_by_url(avatar1, avatar2)
        
        if face_result.get('success'):
            return {
                'exact_match': False,
                'both_have_avatars': True,
                'face_comparison': {
                    'method': face_result.get('method', 'unknown'),
                    'face_match': face_result.get('face_match', False),
                    'face_similarity': face_result.get('face_similarity', 0),
                    'face_distance': face_result.get('face_distance'),
                    'interpretation': face_result.get('interpretation', '')
                },
                'match_score': face_result.get('face_similarity', 0) / 100,
                'interpretation': f"Сравнение лиц: {face_result.get('interpretation', 'результат неизвестен')}"
            }
        
        # Если распознавание не удалось
        return {
            'exact_match': False,
            'both_have_avatars': True,
            'face_comparison': {
                'error': face_result.get('error', 'Неизвестная ошибка')
            },
            'match_score': 0.0,
            'interpretation': 'Не удалось сравнить лица (разные URL аватарок)'
        }
    
    def extract_visual_metadata(self, photo_data: Dict) -> Dict[str, any]:
        """
        Извлекает визуальные метаданные из фото
        
        Args:
            photo_data: Данные одного фото
        """
        
        return {
            'photo_id': photo_data.get('id'),
            'owner_id': photo_data.get('owner_id'),
            'date': photo_data.get('date'),
            'likes': photo_data.get('likes', {}).get('count', 0),
            'comments': photo_data.get('comments', {}).get('count', 0),
            'reposts': photo_data.get('reposts', {}).get('count', 0),
            'has_text': bool(photo_data.get('text')),
            'text_length': len(photo_data.get('text', '')),
            'width': photo_data.get('width'),
            'height': photo_data.get('height'),
            'access_key': photo_data.get('access_key'),
        }
    
    def analyze_visual_patterns(self, photos_data: List[Dict]) -> Dict[str, any]:
        """
        Анализирует визуальные паттерны в фотографиях
        
        Args:
            photos_data: Список фотографий
        """
        
        if not photos_data:
            return {
                'pattern_analysis': 'Нет данных'
            }
        
        # Анализ соотношения сторон
        aspect_ratios = []
        for photo in photos_data:
            width = photo.get('width', 0)
            height = photo.get('height', 0)
            if width > 0 and height > 0:
                aspect_ratios.append(width / height)
        
        # Категоризация по соотношению сторон
        landscape = sum(1 for r in aspect_ratios if r > 1.2)
        portrait = sum(1 for r in aspect_ratios if r < 0.8)
        square = sum(1 for r in aspect_ratios if 0.8 <= r <= 1.2)
        
        # Анализ размеров
        sizes = Counter()
        for photo in photos_data:
            if 'sizes' in photo:
                max_size = max(photo['sizes'], key=lambda s: s.get('width', 0) * s.get('height', 0))
                sizes[max_size.get('type', 'unknown')] += 1
        
        return {
            'total_photos': len(photos_data),
            'aspect_ratio': {
                'landscape': landscape,
                'portrait': portrait,
                'square': square,
            },
            'size_preferences': dict(sizes.most_common(5)),
            'avg_likes_per_photo': sum(p.get('likes', {}).get('count', 0) for p in photos_data) / len(photos_data),
            'photos_with_text': sum(1 for p in photos_data if p.get('text')),
        }
    
    def get_face_detection_status(self) -> Dict[str, any]:
        """
        Проверяет доступность библиотек для распознавания лиц
        
        Returns:
            Информация о доступности функций распознавания лиц
        """
        
        return {
            'face_recognition_available': FACE_RECOGNITION_AVAILABLE,
            'cv2_available': CV2_AVAILABLE,
            'mediapipe_available': MEDIAPIPE_AVAILABLE,
            'active_engine': 'face_recognition' if self.face_engine else ('opencv' if self.opencv_recognizer else ('mediapipe' if self.mediapipe_recognizer else 'none')),
            'message': self._get_status_message()
        }
    
    def _get_status_message(self) -> str:
        """Возвращает сообщение о статусе"""
        
        if self.face_engine:
            return "Available advanced face recognition (face_recognition/dlib)"
        elif self.opencv_recognizer:
            return "Available basic face recognition (OpenCV Haar Cascade)"
        elif self.mediapipe_recognizer:
            return "Available face recognition (MediaPipe)"
        else:
            return "Face recognition unavailable. Install: pip install face-recognition opencv-python"


# ============================================================================
# ВНУТРЕННИЕ КЛАССЫ ДЛЯ РАСПОЗНАВАНИЯ ЛИЦ
# ============================================================================

class FaceRecognitionEngine:
    """
    Движок для распознавания и сравнения лиц (использует face_recognition/dlib)
    """
    
    def __init__(self):
        self.is_available = FACE_RECOGNITION_AVAILABLE
        self.comparison_threshold = 0.6  # Порог для определения совпадения
    
    def detect_faces(self, image_path: str) -> Dict:
        """Обнаруживает лица на изображении"""
        
        if not self.is_available:
            return {'success': False, 'error': 'face_recognition не установлен', 'faces_found': 0}
        
        if not os.path.exists(image_path):
            return {'success': False, 'error': f'Файл не найден: {image_path}', 'faces_found': 0}
        
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            faces_data = []
            for i, (location, encoding) in enumerate(zip(face_locations, face_encodings)):
                top, right, bottom, left = location
                faces_data.append({
                    'index': i,
                    'location': {'top': top, 'right': right, 'bottom': bottom, 'left': left},
                    'width': right - left,
                    'height': bottom - top,
                    'encoding': encoding.tolist(),
                    'encoding_magnitude': float(np.linalg.norm(encoding))
                })
            
            return {
                'success': True,
                'image_path': image_path,
                'faces_found': len(faces_data),
                'faces': faces_data,
                'has_multiple_faces': len(faces_data) > 1
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'faces_found': 0}
    
    def compare_faces(self, image1_path: str, image2_path: str) -> Dict:
        """Сравнивает два лица на изображениях"""
        
        if not self.is_available:
            return {'success': False, 'error': 'face_recognition не установлен'}
        
        if not os.path.exists(image1_path):
            return {'success': False, 'error': f'Файл не найден: {image1_path}'}
        
        if not os.path.exists(image2_path):
            return {'success': False, 'error': f'Файл не найден: {image2_path}'}
        
        try:
            img1 = face_recognition.load_image_file(image1_path)
            img2 = face_recognition.load_image_file(image2_path)
            
            encodings1 = face_recognition.face_encodings(img1)
            encodings2 = face_recognition.face_encodings(img2)
            
            if len(encodings1) == 0:
                return {
                    'success': False,
                    'error': 'На первом изображении не найдено лицо',
                    'faces_in_image1': 0,
                    'faces_in_image2': len(encodings2)
                }
            
            if len(encodings2) == 0:
                return {
                    'success': False,
                    'error': 'На втором изображении не найдено лицо',
                    'faces_in_image1': len(encodings1),
                    'faces_in_image2': 0
                }
            
            encoding1 = encodings1[0]
            encoding2 = encodings2[0]
            
            # Вычисляем евклидово расстояние
            face_distance = np.linalg.norm(encoding1 - encoding2)
            
            # Определяем результат
            is_match = face_distance < self.comparison_threshold
            
            # Вычисляем процент схожести (0-100%)
            # Исправлено: используем более корректную формулу
            similarity_percentage = max(0, (1 - face_distance / 1.5)) * 100
            
            return {
                'success': True,
                'match': is_match,
                'face_distance': float(face_distance),
                'similarity_percentage': float(similarity_percentage),
                'threshold': self.comparison_threshold,
                'faces_in_image1': len(encodings1),
                'faces_in_image2': len(encodings2),
                'interpretation': self._interpret_result(is_match, similarity_percentage)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _interpret_result(self, is_match: bool, similarity: float) -> str:
        """Интерпретирует результат сравнения"""
        
        if similarity >= 80:
            return "Очень высокая схожесть - вероятно одно лицо"
        elif similarity >= 60:
            return "Высокая схожесть - возможно одно лицо"
        elif similarity >= 40:
            return "Средняя схожесть - возможно разные люди"
        else:
            return "Низкая схожесть - разные люди"


class OpenCVFaceRecognizer:
    """
    Система распознавания лиц на основе OpenCV (Haar Cascade)
    """
    
    def __init__(self):
        self.is_available = CV2_AVAILABLE
        self.face_cascade = None
        
        if self.is_available:
            try:
                self.face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                
                if self.face_cascade is None or self.face_cascade.empty():
                    self.is_available = False
                else:
                    print("[OK] OpenCV Haar Cascade loaded")
            except:
                self.is_available = False
    
    def detect_faces(self, image_path: str) -> Dict:
        """Обнаруживает лица на изображении"""
        
        if not self.is_available:
            return {'success': False, 'error': 'OpenCV не доступен', 'faces_found': 0}
        
        if not os.path.exists(image_path):
            return {'success': False, 'error': 'Файл не найден', 'faces_found': 0}
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {'success': False, 'error': 'Не загрузить изображение', 'faces_found': 0}
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            faces_data = []
            for i, (x, y, w, h) in enumerate(faces):
                faces_data.append({
                    'index': i,
                    'bbox': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                    'confidence': 1.0,
                    'size': int(w * h)
                })
            
            return {
                'success': True,
                'image_path': image_path,
                'image_size': {'width': image.shape[1], 'height': image.shape[0]},
                'faces_found': len(faces_data),
                'faces': faces_data,
                'has_multiple_faces': len(faces_data) > 1
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'faces_found': 0}
    
    def compare_faces(self, image1_path: str, image2_path: str) -> Dict:
        """Сравнивает два лица (упрощённый метод)"""
        
        if not self.is_available:
            return {'success': False, 'error': 'OpenCV не доступен'}
        
        r1 = self.detect_faces(image1_path)
        r2 = self.detect_faces(image2_path)
        
        if not r1.get('success') or r1['faces_found'] == 0:
            return {'success': False, 'error': f'На первом фото не найдено лицо: {r1.get("error")}'}
        
        if not r2.get('success') or r2['faces_found'] == 0:
            return {'success': False, 'error': f'На втором фото не найдено лицо: {r2.get("error")}'}
        
        # OpenCV Haar Cascade не даёт хороших embedding-ов для сравнения
        # Это упрощённая версия - она может только определить наличие лиц
        # Для реального сравнения рекомендуется использовать face_recognition
        
        return {
            'success': True,
            'match': False,  # OpenCV не может надёжно сравнить лица
            'similarity_percentage': 50.0,  # Неопределённый результат
            'warning': 'OpenCV Haar Cascade не поддерживает точное сравнение лиц. Используйте face_recognition для лучших результатов.',
            'interpretation': 'Лица найдены, но сравнение недоступно (используйте face_recognition)'
        }


class MediaPipeFaceRecognizer:
    """
    Система распознавания лиц на основе MediaPipe
    """
    
    def __init__(self):
        self.is_available = False  # Отключаем MediaPipe по умолчанию
        self.face_detector = None
        
        # Примечание: Для использования MediaPipe требуется:
        # 1. Скачать модель face_detector с https://developers.google.com/mediapipe/solutions/vision/face_detector
        # 2. Указать локальный путь к файлу модели (.blob)
        # Пока используем OpenCV как основной метод распознавания лиц
        print("[X] MediaPipe: Требуется загрузка моделей вручную. Используется OpenCV.")
    
    def _load_image(self, image_path: str):
        """Загружает изображение для MediaPipe"""
        image = cv2.imread(image_path)
        if image is None:
            return None
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return mp_tasks.vision.Image(image_format=mp_tasks.vision.ImageFormat.SRGB, data=rgb_image)
    
    def detect_faces(self, image_path: str) -> Dict:
        """Обнаруживает лица на изображении"""
        
        if not self.is_available or self.face_detector is None:
            return {'success': False, 'error': 'MediaPipe недоступен', 'faces_found': 0}
        
        if not os.path.exists(image_path):
            return {'success': False, 'error': 'Файл не найден', 'faces_found': 0}
        
        try:
            image = self._load_image(image_path)
            if image is None:
                return {'success': False, 'error': 'Не загрузить изображение', 'faces_found': 0}
            
            result = self.face_detector.detect(image)
            faces_data = []
            
            if result.detections:
                for i, detection in enumerate(result.detections):
                    bbox = detection.bounding_box
                    confidence = detection.categories[0].score if detection.categories else 0
                    faces_data.append({
                        'index': i,
                        'bbox': {'x': bbox.origin_x, 'y': bbox.origin_y, 'width': bbox.width, 'height': bbox.height},
                        'confidence': float(confidence)
                    })
            
            return {
                'success': True,
                'image_path': image_path,
                'faces_found': len(faces_data),
                'faces': faces_data
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'faces_found': 0}
    
    def compare_faces(self, image1_path: str, image2_path: str) -> Dict:
        """Сравнивает два лица (упрощённый метод)"""
        
        if not self.is_available:
            return {'success': False, 'error': 'MediaPipe недоступен'}
        
        r1 = self.detect_faces(image1_path)
        r2 = self.detect_faces(image2_path)
        
        if not r1.get('success') or r1['faces_found'] == 0:
            return {'success': False, 'error': f'На первом фото не найдено лицо: {r1.get("error")}'}
        
        if not r2.get('success') or r2['faces_found'] == 0:
            return {'success': False, 'error': f'На втором фото не найдено лицо: {r2.get("error")}'}
        
        # MediaPipe FaceDetector не даёт embedding для сравнения
        # Для сравнения нужен FaceLandmarker (более тяжёлый)
        
        return {
            'success': True,
            'match': False,
            'similarity_percentage': 50.0,
            'warning': 'MediaPipe FaceDetector не поддерживает сравнение лиц. Используйте face_recognition.',
            'interpretation': 'Лица найдены, но точное сравнение недоступно'
        }


# Пример использования
if __name__ == "__main__":
    matcher = VisualMatcher()
    
    # Проверка статуса
    print("\n" + "="*60)
    print("СТАТУС ВИЗУАЛЬНОГО АНАЛИЗА")
    print("="*60)
    status = matcher.get_face_detection_status()
    print(f"face_recognition: {status['face_recognition_available']}")
    print(f"OpenCV: {status['cv2_available']}")
    print(f"MediaPipe: {status['mediapipe_available']}")
    print(f"Активный движок: {status['active_engine']}")
    print(f"Сообщение: {status['message']}")
