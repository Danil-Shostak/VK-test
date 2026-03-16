# face_recognition_module.py
# Модуль распознавания лиц с использованием бесплатных библиотек
# Использует: face_recognition (dlib), OpenCV, NumPy
# Все библиотеки бесплатные и работают локально

import os
import sys
import io
import json
from typing import Dict, List, Tuple, Optional

# Настройка UTF-8 для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Пробуем импортировать библиотеки
FACE_RECOGNITION_AVAILABLE = False
CV2_AVAILABLE = False

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
    print("✓ face_recognition: OK")
except ImportError:
    print("✗ face_recognition: Не установлена")
    print("  Установите: pip install face_recognition")

try:
    import cv2
    CV2_AVAILABLE = True
    print("✓ OpenCV: OK")
except ImportError:
    print("✗ OpenCV: Не установлена")
    print("  Установите: pip install opencv-python")

try:
    import numpy as np
    print("✓ NumPy: OK")
except ImportError:
    print("✗ NumPy: Не установлена")
    print("  Установите: pip install numpy")


class FaceRecognitionEngine:
    """
    Движок для распознавания и сравнения лиц
    
    Использует библиотеку face_recognition (бесплатная, открытый код)
    - Обнаружение лица (face detection)
    - Извлечение 128 ключевых точек лица (face encoding)
    - Сравнение лиц по евклидову расстоянию
    """
    
    def __init__(self):
        self.is_available = FACE_RECOGNITION_AVAILABLE
        self.comparison_threshold = 0.6  # Порог для определения совпадения
        
    def detect_faces(self, image_path: str) -> Dict:
        """
        Обнаруживает лица на изображении
        
        Args:
            image_path: Путь к файлу изображения
            
        Returns:
            Dict с информацией о найденных лицах
        """
        
        if not self.is_available:
            return {
                'success': False,
                'error': 'Библиотека face_recognition не установлена',
                'faces_found': 0
            }
        
        if not os.path.exists(image_path):
            return {
                'success': False,
                'error': f'Файл не найден: {image_path}',
                'faces_found': 0
            }
        
        try:
            # Загружаем изображение
            image = face_recognition.load_image_file(image_path)
            
            # Находим все лица
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            faces_data = []
            for i, (location, encoding) in enumerate(zip(face_locations, face_encodings)):
                top, right, bottom, left = location
                
                face_info = {
                    'index': i,
                    'location': {
                        'top': top,
                        'right': right,
                        'bottom': bottom,
                        'left': left
                    },
                    'width': right - left,
                    'height': bottom - top,
                    'encoding': encoding.tolist(),  # 128 точек
                    'encoding_magnitude': float(np.linalg.norm(encoding))
                }
                faces_data.append(face_info)
            
            return {
                'success': True,
                'image_path': image_path,
                'faces_found': len(faces_data),
                'faces': faces_data,
                'has_multiple_faces': len(faces_data) > 1
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'faces_found': 0
            }
    
    def compare_faces(self, image1_path: str, image2_path: str) -> Dict:
        """
        Сравнивает два лица на изображениях
        
        Args:
            image1_path: Путь к первому изображению
            image2_path: Путь ко второму изображению
            
        Returns:
            Dict с результатами сравнения
        """
        
        if not self.is_available:
            return {
                'success': False,
                'error': 'Библиотека face_recognition не установлена'
            }
        
        # Проверяем существование файлов
        if not os.path.exists(image1_path):
            return {
                'success': False,
                'error': f'Файл не найден: {image1_path}'
            }
        
        if not os.path.exists(image2_path):
            return {
                'success': False,
                'error': f'Файл не найден: {image2_path}'
            }
        
        try:
            # Загружаем изображения
            img1 = face_recognition.load_image_file(image1_path)
            img2 = face_recognition.load_image_file(image2_path)
            
            # Получаем кодировки лиц
            encodings1 = face_recognition.face_encodings(img1)
            encodings2 = face_recognition.face_encodings(img2)
            
            # Проверяем, есть ли лица на изображениях
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
            
            # Берем первое лицо из каждого изображения
            encoding1 = encodings1[0]
            encoding2 = encodings2[0]
            
            # Вычисляем евклидово расстояние
            face_distance = np.linalg.norm(encoding1 - encoding2)
            
            # Определяем результат
            is_match = face_distance < self.comparison_threshold
            
            # Вычисляем процент схожести (0-100%)
            # Исправлено: используем более корректную формулу с учётом макс. расстояния ~1.5
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
            return {
                'success': False,
                'error': str(e)
            }
    
    def compare_multiple_faces(self, image1_path: str, image2_path: str) -> Dict:
        """
        Сравнивает все лица на двух изображениях (если их несколько)
        
        Args:
            image1_path: Путь к первому изображению
            image2_path: Путь ко второму изображению
            
        Returns:
            Dict с результатами сравнения всех лиц
        """
        
        if not self.is_available:
            return {
                'success': False,
                'error': 'Библиотека face_recognition не установлена'
            }
        
        try:
            # Загружаем изображения
            img1 = face_recognition.load_image_file(image1_path)
            img2 = face_recognition.load_image_file(image2_path)
            
            # Получаем все кодировки лиц
            encodings1 = face_recognition.face_encodings(img1)
            encodings2 = face_recognition.face_encodings(img2)
            
            if len(encodings1) == 0 or len(encodings2) == 0:
                return {
                    'success': False,
                    'error': 'На одном из изображений не найдены лица',
                    'faces_in_image1': len(encodings1),
                    'faces_in_image2': len(encodings2)
                }
            
            # Сравниваем каждое лицо с каждым
            comparisons = []
            best_match = None
            best_similarity = 0
            
            for i, enc1 in enumerate(encodings1):
                for j, enc2 in enumerate(encodings2):
                    distance = np.linalg.norm(enc1 - enc2)
                    is_match = distance < self.comparison_threshold
                    similarity = max(0, (1 - distance / 1.5)) * 100
                    
                    comparisons.append({
                        'face1_index': i,
                        'face2_index': j,
                        'distance': float(distance),
                        'similarity': float(similarity),
                        'is_match': is_match
                    })
                    
                    if is_match and similarity > best_similarity:
                        best_similarity = similarity
                        best_match = {
                            'face1_index': i,
                            'face2_index': j,
                            'similarity': float(similarity)
                        }
            
            return {
                'success': True,
                'total_faces_image1': len(encodings1),
                'total_faces_image2': len(encodings2),
                'comparisons': comparisons,
                'best_match': best_match,
                'found_match': best_match is not None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
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
    
    def get_face_encoding(self, image_path: str) -> Optional[List[float]]:
        """
        Получает кодировку лица для дальнейшего использования
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Список из 128 чисел или None
        """
        
        if not self.is_available:
            return None
        
        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            
            if len(encodings) > 0:
                return encodings[0].tolist()
            return None
            
        except Exception:
            return None


def test_face_recognition():
    """Тестирует работу модуля распознавания лиц"""
    
    print("\n" + "="*60)
    print("ТЕСТ СИСТЕМЫ РАСПОЗНАВАНИЯ ЛИЦ")
    print("="*60)
    
    engine = FaceRecognitionEngine()
    
    if not engine.is_available:
        print("\n❌ Модуль недоступен. Установите библиотеки:")
        print("   pip install face_recognition dlib")
        print("   pip install opencv-python")
        print("   pip install numpy")
        return
    
    # Создаем тестовые изображения (заглушки)
    test_dir = "test_faces"
    os.makedirs(test_dir, exist_ok=True)
    
    print("\n✓ Система распознавания лиц готова к работе!")
    print("\nДоступные функции:")
    print("  1. detect_faces(image_path) - найти лица на фото")
    print("  2. compare_faces(img1, img2) - сравнить два лица")
    print("  3. compare_multiple_faces(img1, img2) - сравнить все лица")
    print(f"  4. Порог совпадения: {engine.comparison_threshold}")


if __name__ == "__main__":
    test_face_recognition()
