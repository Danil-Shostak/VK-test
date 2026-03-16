# opencv_face_recognition.py
# Модуль распознавания лиц с использованием OpenCV (Haar Cascade)
# Полностью бесплатно, работает локально, без внешних моделей

import os
import sys
import io
import json
import math
from typing import Dict, List, Tuple, Optional
import numpy as np

# Настройка UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

CV2_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
    print("OpenCV: OK")
except ImportError:
    print("OpenCV: Не установлена")

print("NumPy: OK")


class OpenCVFaceRecognizer:
    """
    Система распознавания лиц на основе OpenCV (Haar Cascade)
    
    Особенности:
    - Бесплатная и открытая
    - Работает локально
    - Не требует дополнительных моделей
    - Встроена в OpenCV
    """
    
    def __init__(self):
        self.is_available = CV2_AVAILABLE
        self.face_cascade = None
        self.eye_cascade = None
        
        if self.is_available:
            # Загружаем классификатор Haar Cascade для лиц
            # OpenCV поставляется с встроенными каскадами
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            self.face_alt = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml'
            )
            
            self.face_alt2 = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'
            )
            
            self.eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_eye.xml'
            )
            
            # Проверяем загрузку
            if self.face_cascade is None or self.face_cascade.empty():
                print("Не удалось загрузить каскад лиц")
                self.is_available = False
            else:
                print("Haar Cascade: OK")
    
    def detect_faces(self, image_path: str) -> Dict:
        """Обнаруживает лица на изображении"""
        
        if not self.is_available:
            return {'success': False, 'error': 'OpenCV не доступен', 'faces_found': 0}
        
        if not os.path.exists(image_path):
            return {'success': False, 'error': 'Файл не найден', 'faces_found': 0}
        
        try:
            # Загружаем изображение
            image = cv2.imread(image_path)
            if image is None:
                return {'success': False, 'error': 'Не загрузить изображение', 'faces_found': 0}
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Обнаруживаем лица (несколько каскадов для лучшего результата)
            faces = []
            
            # Основной каскад
            faces1 = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(30, 30)
            )
            
            # Альтернативный каскад
            faces2 = self.face_alt.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=4, 
                minSize=(30, 30)
            )
            
            # Объединяем результаты
            all_faces = list(faces1) + list(faces2)
            
            # Фильтруем перекрывающиеся прямоугольники
            faces = self._filter_overlapping_rectangles(all_faces)
            
            faces_data = []
            for i, (x, y, w, h) in enumerate(faces):
                faces_data.append({
                    'index': i,
                    'bbox': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                    'confidence': 1.0,  # Haar каскад не дает уверенность
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
    
    def _filter_overlapping_rectangles(self, rectangles: List, iou_threshold: float = 0.5) -> List:
        """Фильтрует перекрывающиеся прямоугольники"""
        
        if len(rectangles) <= 1:
            return rectangles
        
        # Сортируем по площади (большие first)
        rectangles = sorted(rectangles, key=lambda r: r[2] * r[3], reverse=True)
        
        filtered = []
        
        for rect in rectangles:
            x1, y1, w1, h1 = rect
            is_overlapping = False
            
            for f in filtered:
                x2, y2, w2, h2 = f
                
                # Вычисляем IoU
                x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                overlap_area = x_overlap * y_overlap
                
                iou = overlap_area / (w1 * h1 + w2 * h2 - overlap_area) if (w1 * h1 + w2 * h2) > 0 else 0
                
                if iou > iou_threshold:
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                filtered.append(rect)
        
        return filtered
    
    def extract_face_features(self, image_path: str) -> Dict:
        """Извлекает характеристики лица"""
        
        if not self.is_available:
            return {'success': False, 'error': 'OpenCV не доступен'}
        
        if not os.path.exists(image_path):
            return {'success': False, 'error': 'Файл не найден'}
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {'success': False, 'error': 'Не загрузить'}
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Обнаруживаем лица
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                return {'success': False, 'error': 'Лица не найдены', 'faces_found': 0}
            
            faces_data = []
            
            for i, (x, y, w, h) in enumerate(faces):
                # Вырезаем лицо
                face_roi = gray[y:y+h, x:x+w]
                
                # Изменяем размер
                face_resized = cv2.resize(face_roi, (100, 100))
                
                # Вычисляем гистограмму
                hist = cv2.calcHist([face_resized], [0], None, [256], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                
                # Вычисляем моменты
                moments = cv2.moments(face_resized)
                
                # LBP-подобные характеристики (упрощенные)
                features = self._extract_simple_features(face_resized)
                
                faces_data.append({
                    'face_index': i,
                    'bbox': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                    'histogram': hist.tolist()[:50],  # первые 50 значений
                    'features': features,
                    'moments': {
                        'm00': moments['m00'],
                        'm10': moments['m10'],
                        'm01': moments['m01'],
                    }
                })
            
            return {
                'success': True,
                'image_path': image_path,
                'faces_found': len(faces_data),
                'faces': faces_data
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_simple_features(self, face_image) -> List[float]:
        """Извлекает простые характеристики из изображения лица"""
        
        features = []
        
        # Разбиваем на части
        h, w = face_image.shape
        
        # Верхняя/нижняя половина
        top_half = face_image[:h//2, :]
        bottom_half = face_image[h//2:, :]
        
        features.append(np.mean(top_half) / 255)
        features.append(np.mean(bottom_half) / 255)
        features.append(np.std(top_half) / 255)
        features.append(np.std(bottom_half) / 255)
        
        # Левая/правая половина
        left_half = face_image[:, :w//2]
        right_half = face_image[:, w//2:]
        
        features.append(np.mean(left_half) / 255)
        features.append(np.mean(right_half) / 255)
        
        # Квадранты
        q1 = face_image[:h//2, :w//2]
        q2 = face_image[:h//2, w//2:]
        q3 = face_image[h//2:, :w//2]
        q4 = face_image[h//2:, w//2:]
        
        features.append(np.mean(q1) / 255)
        features.append(np.mean(q2) / 255)
        features.append(np.mean(q3) / 255)
        features.append(np.mean(q4) / 255)
        
        # Центр
        center = face_image[h//4:3*h//4, w//4:3*w//4]
        features.append(np.mean(center) / 255)
        
        return features
    
    def compare_faces(self, image1_path: str, image2_path: str) -> Dict:
        """Сравнивает два лица"""
        
        if not self.is_available:
            return {'success': False, 'error': 'OpenCV не доступен'}
        
        r1 = self.extract_face_features(image1_path)
        r2 = self.extract_face_features(image2_path)
        
        if not r1.get('success'):
            return {'success': False, 'error': f"Лицо 1: {r1.get('error')}"}
        
        if not r2.get('success'):
            return {'success': False, 'error': f"Лицо 2: {r2.get('error')}"}
        
        if r1['faces_found'] == 0:
            return {'success': False, 'error': 'На первом фото нет лиц'}
        
        if r2['faces_found'] == 0:
            return {'success': False, 'error': 'На втором фото нет лиц'}
        
        # Берем первое лицо из каждого изображения
        f1 = r1['faces'][0]
        f2 = r2['faces'][0]
        
        # Сравниваем гистограммы
        hist1 = np.array(f1['histogram'])
        hist2 = np.array(f2['histogram'])
        
        # Корреляция гистограмм
        correlation = cv2.compareHist(
            hist1.reshape(-1, 1), 
            hist2.reshape(-1, 1), 
            cv2.HISTCMP_CORREL
        )
        
        # Сравниваем простые характеристики
        feat1 = np.array(f1['features'])
        feat2 = np.array(f2['features'])
        
        # Косинусное сходство
        dot = np.dot(feat1, feat2)
        norm1 = np.linalg.norm(feat1)
        norm2 = np.linalg.norm(feat2)
        
        if norm1 > 0 and norm2 > 0:
            cos_sim = dot / (norm1 * norm2)
        else:
            cos_sim = 0
        
        # Комбинированная оценка
        combined_score = (correlation + cos_sim) / 2
        
        # В процентах
        similarity = max(0, combined_score * 100)
        
        # Порог
        threshold = 0.5
        is_match = combined_score >= threshold
        
        return {
            'success': True,
            'match': is_match,
            'histogram_correlation': float(correlation),
            'features_similarity': float(cos_sim),
            'combined_score': float(combined_score),
            'similarity_percentage': float(similarity),
            'threshold': threshold,
            'faces_in_image1': r1['faces_found'],
            'faces_in_image2': r2['faces_found'],
            'interpretation': self._interpret_result(is_match, similarity)
        }
    
    def _interpret_result(self, is_match: bool, similarity: float) -> str:
        if similarity >= 70:
            return "Высокая схожесть - возможно одно лицо"
        elif similarity >= 50:
            return "Средняя схожесть"
        else:
            return "Низкая схожесть - разные лица"
    
    def draw_faces(self, image_path: str, output_path: str = None) -> str:
        """Рисует рамки вокруг лиц"""
        
        if not self.is_available:
            return None
        
        if not os.path.exists(image_path):
            return None
        
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        if output_path is None:
            name, ext = os.path.splitext(image_path)
            output_path = f"{name}_faces{ext}"
        
        cv2.imwrite(output_path, image)
        return output_path


def main():
    print("\n" + "="*60)
    print("СИСТЕМА РАСПОЗНАВАНИЯ ЛИЦ (OpenCV)")
    print("="*60)
    
    recognizer = OpenCVFaceRecognizer()
    
    if not recognizer.is_available:
        print("\nОшибка: OpenCV не установлен")
        print("pip install opencv-python")
        return
    
    print("\nГотово! Используйте:")
    print("  1. detect_faces(path) - найти лица")
    print("  2. extract_face_features(path) - характеристики")
    print("  3. compare_faces(p1, p2) - сравнить")
    print("  4. draw_faces(path) - нарисовать рамки")


if __name__ == "__main__":
    main()
