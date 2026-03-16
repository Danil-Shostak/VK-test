# Face Recognition Package
# Модули для распознавания и сравнения лиц

from .face_recognition_module import FaceRecognitionModule
from .opencv_face_recognition import OpenCVFaceRecognition
from .mediapipe_face_recognition import MediaPipeFaceRecognition

__all__ = [
    'FaceRecognitionModule',
    'OpenCVFaceRecognition',
    'MediaPipeFaceRecognition'
]
