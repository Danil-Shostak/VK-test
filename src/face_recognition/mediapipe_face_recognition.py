# mediapipe_face_recognition.py
# Модуль распознавания лиц с использованием MediaPipe
# Бесплатная библиотека от Google с открытым исходным кодом

import os
import sys
import io
import json
import math
from typing import Dict, List, Tuple, Optional
import numpy as np

# Настройка UTF-8 для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Пробуем импортировать библиотеки
MEDIAPIPE_AVAILABLE = False
CV2_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
    print("OpenCV: OK")
except ImportError:
    print("OpenCV: Не установлена")

try:
    from mediapipe.tasks import python as mp_tasks
    from mediapipe import Image, ImageFormat
    MEDIAPIPE_AVAILABLE = True
    print("MediaPipe: OK")
except ImportError as e:
    print(f"MediaPipe: {e}")

print("NumPy: OK")


class MediaPipeFaceRecognizer:
    """
    Система распознавания лиц на основе MediaPipe
    """
    
    def __init__(self):
        self.is_available = MEDIAPIPE_AVAILABLE
        self.face_landmarker = None
        self.face_detector = None
        
        if self.is_available:
            # Примечание: для работы MediaPipe требуется загрузка моделей
            # Модели можно скачать с https://developers.google.com/mediapipe/solutions/vision/face_landmarker
            # Пока используем только базовое обнаружение через OpenCV fallback
            print("MediaPipe доступен, но требует загрузки моделей")
            print("Для полноценной работы установите модели вручную")
    
    def _load_image(self, image_path: str):
        import cv2
        image = cv2.imread(image_path)
        if image is None:
            return None
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return Image(image_format=ImageFormat.SRGB, data=rgb_image)
    
    def detect_faces(self, image_path: str) -> Dict:
        if not self.is_available:
            return {'success': False, 'error': 'MediaPipe не установлена', 'faces_found': 0}
        
        if not os.path.exists(image_path):
            return {'success': False, 'error': 'Файл не найден', 'faces_found': 0}
        
        if self.face_detector is None:
            return {'success': False, 'error': 'FaceDetector не инициализирован', 'faces_found': 0}
        
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
    
    def extract_face_landmarks(self, image_path: str) -> Dict:
        if not self.is_available or self.face_landmarker is None:
            return {'success': False, 'error': 'MediaPipe не доступен'}
        
        if not os.path.exists(image_path):
            return {'success': False, 'error': 'Файл не найден'}
        
        try:
            image = self._load_image(image_path)
            if image is None:
                return {'success': False, 'error': 'Не загрузить изображение'}
            
            result = self.face_landmarker.detect(image)
            
            if not result.face_landmarks:
                return {'success': False, 'error': 'Лица не найдены', 'faces_found': 0}
            
            landmarks_data = []
            img_h, img_w = image.height, image.width
            
            for face_idx, face_landmarks in enumerate(result.face_landmarks):
                landmarks = [{'x': p.x * img_w, 'y': p.y * img_h, 'z': p.z * img_w} for p in face_landmarks]
                features = self._calculate_face_features(landmarks, img_w, img_h)
                landmarks_data.append({'face_index': face_idx, 'landmarks': landmarks[:50], 'features': features})
            
            return {'success': True, 'image_path': image_path, 'faces_found': len(landmarks_data), 'faces': landmarks_data}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _calculate_face_features(self, landmarks: List[Dict], img_w: int, img_h: int) -> Dict:
        if len(landmarks) < 10:
            return {'error': 'Мало точек'}
        
        # Ключевые точки
        nose_tip, nose_bridge = landmarks[4], landmarks[6]
        left_eye_left, left_eye_right = landmarks[33], landmarks[133]
        mouth_left, mouth_right = landmarks[61], landmarks[291]
        chin, chin_left, chin_right = landmarks[152], landmarks[377], landmarks[148]
        
        def dist(p1, p2):
            return math.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2)
        
        face_w = chin_right['x'] - chin_left['x']
        face_h = chin['y'] - nose_bridge['y']
        
        embedding = [
            face_w / img_w, face_h / img_h, 
            (face_h / face_w) if face_w > 0 else 0,
            dist(left_eye_left, left_eye_right) / face_w if face_w > 0 else 0,
            dist(nose_bridge, nose_tip) / face_h if face_h > 0 else 0,
            dist(mouth_left, mouth_right) / face_w if face_w > 0 else 0
        ]
        
        return {'embedding': embedding, 'embedding_norm': float(np.linalg.norm(embedding))}
    
    def compare_faces(self, image1_path: str, image2_path: str) -> Dict:
        if not self.is_available:
            return {'success': False, 'error': 'MediaPipe не доступен'}
        
        r1 = self.extract_face_landmarks(image1_path)
        r2 = self.extract_face_landmarks(image2_path)
        
        if not r1.get('success') or not r2.get('success'):
            return {'success': False, 'error': f"Лицо не найдено: {r1.get('error') or r2.get('error')}"}
        
        emb1 = np.array(r1['faces'][0]['features']['embedding'])
        emb2 = np.array(r2['faces'][0]['features']['embedding'])
        
        n1 = np.linalg.norm(emb1)
        n2 = np.linalg.norm(emb2)
        if n1 > 0 and n2 > 0:
            cos_sim = np.dot(emb1, emb2) / (n1 * n2)
        else:
            cos_sim = 0
        similarity = max(0, cos_sim * 100)
        
        return {
            'success': True,
            'match': cos_sim >= 0.85,
            'cosine_similarity': float(cos_sim),
            'similarity_percentage': float(similarity),
            'interpretation': "Высокая схожесть" if cos_sim >= 0.85 else "Низкая схожесть"
        }


def main():
    print("\n" + "="*60)
    print("СИСТЕМА РАСПОЗНАВАНИЯ ЛИЦ (MediaPipe)")
    print("="*60)
    
    recognizer = MediaPipeFaceRecognizer()
    
    if not recognizer.is_available:
        print("\nОшибка: MediaPipe не установлена")
        return
    
    print("\nДля использования:")
    print("  1. detect_faces(path) - найти лица")
    print("  2. extract_face_landmarks(path) - точки")
    print("  3. compare_faces(path1, path2) - сравнить")


if __name__ == "__main__":
    main()
