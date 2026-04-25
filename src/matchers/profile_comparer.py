# profile_comparer.py
# Главный модуль сравнения профилей VK

import json
import sys
import io
from typing import Dict, List, Optional, Any
from datetime import datetime

# Настройка UTF-8 для Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.matchers.name_matcher import NameMatcher
from src.matchers.geo_matcher import GeoMatcher
from src.matchers.friends_matcher import FriendsMatcher
from src.matchers.content_matcher import ContentMatcher
from src.matchers.visual_matcher import VisualMatcher
from src.matchers.demographics_matcher import DemographicsMatcher


class ProfileComparer:
    """
    Главный класс для комплексного сравнения профилей VK
    
    Объединяет все модули анализа и вычисляет общую вероятность
    того, что два профиля принадлежат одному человеку.
    
    Весовая система факторов:
    - Имя: 15% (высокая уникальность)
    - Фото: 25% (визуальное сходство)
    - Друзья: 25% (социальные связи)
    - Геолокация: 10% (местоположение)
    - Контент: 15% (стиль и интересы)
    - Демография: 10% (базовые данные)
    """
    
    # Стандартные веса для разных факторов
    DEFAULT_WEIGHTS = {
        'name': 0.15,
        'visual': 0.25,
        'friends': 0.25,
        'geolocation': 0.10,
        'content': 0.15,
        'demographics': 0.10,
    }
    
    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        """
        Инициализирует компаратор профилей
        
        Args:
            custom_weights: Пользовательские весы (если нужно переопределить)
        """
        
        # Инициализируем все модули
        self.name_matcher = NameMatcher()
        self.geo_matcher = GeoMatcher()
        self.friends_matcher = FriendsMatcher()
        self.content_matcher = ContentMatcher()
        self.visual_matcher = VisualMatcher()
        self.demographics_matcher = DemographicsMatcher()
        
        # Устанавливаем веса
        self.weights = custom_weights or self.DEFAULT_WEIGHTS.copy()
        
        # Проверяем сумму весов
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.001:
            # Нормализуем веса
            self.weights = {k: v / total_weight for k, v in self.weights.items()}
    
    def compare_profiles(self, profile1_data: Dict, profile2_data: Dict,
                        friends1_data: Optional[Dict] = None,
                        friends2_data: Optional[Dict] = None,
                        photos1_data: Optional[List[Dict]] = None,
                        photos2_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Комплексное сравнение двух профилей
        
        Args:
            profile1_data: Основные данные первого профиля
            profile2_data: Основные данные второго профиля
            friends1_data: Данные о друзьях первого профиля
            friends2_data: Данные о друзьях второго профиля
            photos1_data: Данные о фото первого профиля
            photos2_data: Данные о фото второго профиля
            
        Returns:
            Dict с полным результатом сравнения
        """
        
        results = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'profile1_id': profile1_data.get('id'),
                'profile2_id': profile2_data.get('id'),
            },
            'analysis': {},
            'scores': {},
            'final': {}
        }
        
        # 1. Анализ имени
        print("\n📛 Анализ имени...")
        name_result = self._analyze_name(profile1_data, profile2_data)
        results['analysis']['name'] = name_result
        
        # 2. Анализ геолокации
        print("🌍 Анализ геолокации...")
        geo_result = self._analyze_geolocation(profile1_data, profile2_data)
        results['analysis']['geolocation'] = geo_result
        
        # 3. Анализ друзей
        print("👥 Анализ друзей...")
        friends_result = self._analyze_friends(friends1_data, friends2_data)
        results['analysis']['friends'] = friends_result
        
        # 4. Анализ контента
        print("📝 Анализ контента...")
        content_result = self._analyze_content(profile1_data, profile2_data)
        results['analysis']['content'] = content_result
        
        # 5. Анализ демографии
        print("📊 Анализ демографии...")
        demo_result = self._analyze_demographics(profile1_data, profile2_data)
        results['analysis']['demographics'] = demo_result
        
        # 6. Визуальный анализ (с сравнением лиц)
        print("📸 Визуальный анализ...")
        visual_result = self._analyze_visual(profile1_data, profile2_data, photos1_data, photos2_data)
        results['analysis']['visual'] = visual_result
        
        # Рассчитываем взвешенные оценки
        print("\n⚖️ Расчет итоговой оценки...")
        weighted_scores = self._calculate_weighted_scores(results['analysis'])
        
        # Добавляем бонусы за сильные совпадения
        bonus_scores = self._calculate_bonus_scores(results['analysis'])
        
        # Финальная оценка
        final_score = sum(weighted_scores.values()) + bonus_scores['total_bonus']
        
        # Нормализуем оценку (не более 100%)
        final_percentage = min(100.0, max(0.0, final_score * 100))
        
        # Интерпретация
        interpretation = self._interpret_final_score(final_percentage)
        
        results['scores'] = {
            'weighted_scores': weighted_scores,
            'bonuses': bonus_scores,
            'total_raw': final_score
        }
        
        results['final'] = {
            'percentage': final_percentage,
            'interpretation': interpretation,
            'confidence': self._calculate_confidence(results['analysis']),
            'data_quality': self._assess_data_quality(profile1_data, profile2_data, 
                                                       friends1_data, friends2_data,
                                                       photos1_data, photos2_data)
        }
        
        # Добавляем детальную информацию о совпадениях
        results['detailed_breakdown'] = self._generate_detailed_breakdown(results['analysis'])
        
        return results
    
    def _analyze_name(self, p1: Dict, p2: Dict) -> Dict[str, Any]:
        """Анализирует совпадение имен"""
        
        first_name1 = p1.get('first_name', '')
        last_name1 = p1.get('last_name', '')
        first_name2 = p2.get('first_name', '')
        last_name2 = p2.get('last_name', '')
        
        result = self.name_matcher.compare_full_names(
            first_name1, last_name1, first_name2, last_name2
        )
        
        return {
            'score': result['combined_score'],
            'first_name': {
                'value1': first_name1,
                'value2': first_name2,
                'comparison': result['first_name_comparison']
            },
            'last_name': {
                'value1': last_name1,
                'value2': last_name2,
                'comparison': result['last_name_comparison']
            },
            'has_data': bool(first_name1 and first_name2),
            'interpretation': result['interpretation']
        }
    
    def _analyze_geolocation(self, p1: Dict, p2: Dict) -> Dict[str, Any]:
        """Анализирует совпадение геолокации"""
        
        # Извлекаем город и страну
        city1 = p1.get('city', {})
        city1_title = city1.get('title', '') if isinstance(city1, dict) else city1
        
        city2 = p2.get('city', {})
        city2_title = city2.get('title', '') if isinstance(city2, dict) else city2
        
        country1 = p1.get('country', {})
        country1_title = country1.get('title', '') if isinstance(country1, dict) else country1
        
        country2 = p2.get('country', {})
        country2_title = country2.get('title', '') if isinstance(country2, dict) else country2
        
        # Также проверяем home_town
        home1 = p1.get('home_town', '')
        home2 = p2.get('home_town', '')
        
        # Сравниваем
        city_result = self.geo_matcher.compare_locations(
            city1_title or home1,
            city2_title or home2,
            country1_title,
            country2_title
        )
        
        return {
            'score': city_result['final_score'],
            'city1': city1_title or home1,
            'city2': city2_title or home2,
            'country1': country1_title,
            'country2': country2_title,
            'comparison': city_result,
            'has_data': bool(city1_title or home1 or city2_title or home2),
            'interpretation': self.geo_matcher.interpret_score(city_result['final_score'])
        }
    
    def _analyze_friends(self, f1: Optional[Dict], f2: Optional[Dict]) -> Dict[str, Any]:
        """Анализирует совпадение друзей"""
        
        if not f1 or not f2:
            return {
                'score': 0.0,
                'has_data': False,
                'interpretation': 'Нет данных о друзьях'
            }
        
        result = self.friends_matcher.compare_friends(f1, f2)
        
        return {
            'score': result['friend_overlap_score'],
            'common_count': result['common_count'],
            'total_1': result['total_friends_1'],
            'total_2': result['total_friends_2'],
            'jaccard': result['jaccard_index'],
            'has_data': True,
            'interpretation': result['interpretation']
        }
    
    def _analyze_content(self, p1: Dict, p2: Dict) -> Dict[str, Any]:
        """Анализирует контент профилей"""
        
        # Извлекаем контент
        content1 = {
            'posts': p1.get('posts', []),
            'status': p1.get('status', ''),
            'about': p1.get('about', ''),
            'activities': p1.get('activities', ''),
            'interests': p1.get('interests', ''),
            'music': p1.get('music', ''),
            'movies': p1.get('movies', ''),
            'books': p1.get('books', ''),
            'games': p1.get('games', ''),
            'quotes': p1.get('quotes', ''),
        }
        
        content2 = {
            'posts': p2.get('posts', []),
            'status': p2.get('status', ''),
            'about': p2.get('about', ''),
            'activities': p2.get('activities', ''),
            'interests': p2.get('interests', ''),
            'music': p2.get('music', ''),
            'movies': p2.get('movies', ''),
            'books': p2.get('books', ''),
            'games': p2.get('games', ''),
            'quotes': p2.get('quotes', ''),
        }
        
        # Сравниваем интересы
        interests_result = self.content_matcher.compare_interests(p1, p2)
        
        # Проверяем наличие контента
        has_content1 = any(v for k, v in content1.items() if k != 'posts')
        has_content2 = any(v for k, v in content2.items() if k != 'posts')
        
        if not has_content1 and not has_content2:
            return {
                'score': 0.0,
                'has_data': False,
                'interpretation': 'Нет контента для анализа'
            }
        
        return {
            'score': interests_result['score'],
            'interests_result': interests_result,
            'has_data': has_content1 or has_content2,
            'interpretation': f"Совпадение интересов: {len(interests_result.get('common_interests', []))}"
        }
    
    def _analyze_demographics(self, p1: Dict, p2: Dict) -> Dict[str, Any]:
        """Анализирует демографические данные"""
        
        result = self.demographics_matcher.compare_all_demographics(p1, p2)
        
        return {
            'score': result.get('overall_demographics_score', 0.0),
            'details': result,
            'has_data': bool(p1.get('bdate') or p2.get('bdate')),
            'interpretation': result.get('interpretation', '')
        }
    
    def _analyze_visual(self, p1: Optional[Dict], p2: Optional[Dict], ph1: Optional[List], ph2: Optional[List]) -> Dict[str, Any]:
        """
        Анализирует визуальные данные (включая сравнение лиц по всем фотографиям)
        """
        
        if not p1 or not p2:
            return {
                'score': 0.0,
                'has_data': False,
                'interpretation': 'Нет данных профилей для анализа'
            }
        
        # 1. Сначала сравниваем аватарки (быстро)
        print("   Сравнение аватарок профилей...")
        avatar_result = self.visual_matcher.compare_avatars(p1, p2)
        
        face_similarity = 0.0
        face_match = False
        face_method = 'none'
        all_photos_result = {}
        
        if avatar_result.get('face_comparison'):
            fc = avatar_result['face_comparison']
            if fc.get('face_similarity'):
                face_similarity = fc['face_similarity']
                face_match = fc.get('face_match', False)
                face_method = fc.get('method', 'unknown')
                print(f"      Лица (аватары): {face_similarity:.1f}% схожесть ({face_method})")
        
        # 2. Если на аватарах не найдено лиц И есть другие фотографии — сравниваем все фотки
        all_photos_similarity = 0.0
        if ph1 and ph2 and (face_similarity == 0 or face_similarity < 60):
            print("   Сравнение всех фотографий (face matching)...")
            all_photos_result = self.visual_matcher.compare_all_photos(ph1, ph2, max_comparisons=200)
            all_photos_similarity = all_photos_result.get('max_similarity', 0.0)
            print(f"      Лица (все фото): {all_photos_similarity:.1f}% схожесть")
        
        # 3. Анализ коллекций фото (метаданные)
        activity_similarity = 0.0
        identical_photos = 0
        if ph1 and ph2:
            photo_collection_result = self.visual_matcher.compare_photo_collections(ph1, ph2)
            identical_photos = photo_collection_result.get('identical_photos_count', 0)
            activity_similarity = photo_collection_result.get('activity_similarity', 0.0)
            print(f"      Идентичных фото: {identical_photos}")
            print(f"      Сходство активности: {activity_similarity:.1%}")
        
        # 4. Определяем итоговый score (берем максимальное сходство из всех источников)
        best_face_similarity = max(face_similarity, all_photos_similarity)
        visual_score = best_face_similarity / 100.0
        
        # Если вообще нет совпадений по лицам — используем activity_similarity (с понижающим коэффициентом)
        if visual_score == 0.0 and activity_similarity > 0:
            visual_score = activity_similarity * 0.5
        
        # 5. Интерпретация
        if best_face_similarity >= 80:
            interpretation = "Очень высокая схожесть - вероятно одно и то же лицо"
        elif best_face_similarity >= 60:
            interpretation = "Высокая схожесть лиц"
        elif identical_photos > 0:
            interpretation = f"Найдено {identical_photos} идентичных фотографий"
        elif activity_similarity > 0.7:
            interpretation = "Похожая активность на фотографиях"
        else:
            interpretation = "Низкое визуальное сходство"
        
        return {
            'score': visual_score,
            'has_data': True,
            'face_similarity': best_face_similarity,
            'face_match': best_face_similarity >= 60,
            'face_method': face_method if face_similarity > 0 else 'face_recognition_all_photos',
            'identical_photos': identical_photos,
            'activity_similarity': activity_similarity,
            'all_photos_comparisons': all_photos_result.get('total_comparisons', 0) if all_photos_result else 0,
            'interpretation': interpretation
        }
        
        # 1. Сначала сравниваем аватарки (быстро)
        print("   Сравнение аватарок профилей...")
        avatar_result = self.visual_matcher.compare_avatars(p1, p2)
        
        face_similarity = 0.0
        face_match = False
        face_method = 'none'
        
        if avatar_result.get('face_comparison'):
            fc = avatar_result['face_comparison']
            if fc.get('face_similarity'):
                face_similarity = fc['face_similarity']
                face_match = fc.get('face_match', False)
                face_method = fc.get('method', 'unknown')
                print(f"      Лица (аватары): {face_similarity:.1f}% схожесть ({face_method})")
        
        # 2. Если на аватарах не найдено лиц И есть другие фотографии — сравниваем все фотки
        all_photos_similarity = 0.0
        if ph1 and ph2 and (face_similarity == 0 or not face_match):
            print("   Сравнение всех фотографий (face matching)...")
            all_photos_result = self.visual_matcher.compare_all_photos(ph1, ph2, max_comparisons=300)
            all_photos_similarity = all_photos_result.get('max_similarity', 0.0)
            print(f"      Лица (все фото): {all_photos_similarity:.1f}% схожесть")
        
        # 3. Анализ коллекций фото (метаданные)
        activity_similarity = 0.0
        identical_photos = 0
        if ph1 and ph2:
            photo_collection_result = self.visual_matcher.compare_photo_collections(ph1, ph2)
            identical_photos = photo_collection_result.get('identical_photos_count', 0)
            activity_similarity = photo_collection_result.get('activity_similarity', 0.0)
            print(f"      Идентичных фото: {identical_photos}")
            print(f"      Сходство активности: {activity_similarity:.1%}")
        
        # 4. Определяем итоговый score
        # Берем максимальное сходство из: аватаров, всех фото, активности
        visual_score = max(face_similarity, all_photos_similarity) / 100.0
        
        # Если вообще нет совпадений по лицам — используем activity_similarity
        if visual_score == 0.0 and activity_similarity > 0:
            visual_score = activity_similarity * 0.5  #Downweight activity-only match
        
        # Интерпретация
        if face_similarity >= 80 or all_photos_similarity >= 80:
            interpretation = "Очень высокая схожесть лиц - вероятно одно и то же лицо"
        elif face_similarity >= 60 or all_photos_similarity >= 60:
            interpretation = "Высокая схожесть лиц"
        elif identical_photos > 0:
            interpretation = f"Найдено {identical_photos} идентичных фотографий"
        elif activity_similarity > 0.7:
            interpretation = "Похожая активность в фотографиях"
        else:
            interpretation = "Низкое визуальное сходство"
        
        return {
            'score': visual_score,
            'has_data': True,
            'face_similarity': max(face_similarity, all_photos_similarity),
            'face_match': face_match or all_photos_similarity >= 60,
            'face_method': face_method if face_similarity > 0 else 'face_recognition_all_photos',
            'identical_photos': identical_photos,
            'activity_similarity': activity_similarity,
            'identical_photos_count': identical_photos,
            'all_photos_comparisons': all_photos_result.get('total_comparisons', 0) if ph1 and ph2 else 0,
            'interpretation': interpretation
        }
    
    def _calculate_weighted_scores(self, analysis: Dict) -> Dict[str, float]:
        """Рассчитывает взвешенные оценки для каждого фактора"""
        
        scores = {}
        
        # Оценки из анализа
        raw_scores = {
            'name': analysis.get('name', {}).get('score', 0.0),
            'visual': analysis.get('visual', {}).get('score', 0.0),
            'friends': analysis.get('friends', {}).get('score', 0.0),
            'geolocation': analysis.get('geolocation', {}).get('score', 0.0),
            'content': analysis.get('content', {}).get('score', 0.0),
            'demographics': analysis.get('demographics', {}).get('score', 0.0),
        }
        
        # Применяем веса
        for factor, weight in self.weights.items():
            raw_score = raw_scores.get(factor, 0.0)
            scores[factor] = raw_score * weight
        
        return scores
    
    def _calculate_bonus_scores(self, analysis: Dict) -> Dict[str, Any]:
        """Рассчитывает бонусы за сильные совпадения"""
        
        bonuses = {
            'strong_name_match': 0.0,
            'high_friend_overlap': 0.0,
            'exact_location': 0.0,
            'identical_photos': 0.0,
            'total_bonus': 0.0
        }
        
        # Бонус за точное совпадение имени
        name_analysis = analysis.get('name', {})
        if name_analysis.get('score', 0) >= 0.9:
            bonuses['strong_name_match'] = 0.15
        
        # Бонус за высокое пересечение друзей
        friends_analysis = analysis.get('friends', {})
        common_count = friends_analysis.get('common_count', 0)
        if common_count >= 20:
            bonuses['high_friend_overlap'] = 0.15
        elif common_count >= 10:
            bonuses['high_friend_overlap'] = 0.1
        elif common_count >= 5:
            bonuses['high_friend_overlap'] = 0.05
        
        # Бонус за точную геолокацию
        geo_analysis = analysis.get('geolocation', {})
        if geo_analysis.get('score', 0) >= 0.95:
            bonuses['exact_location'] = 0.1
        
        # Бонус за идентичные фото
        visual_analysis = analysis.get('visual', {})
        identical = visual_analysis.get('identical_photos', 0)
        if identical >= 3:
            bonuses['identical_photos'] = 0.2
        elif identical >= 1:
            bonuses['identical_photos'] = 0.1
        
        bonuses['total_bonus'] = sum([
            bonuses['strong_name_match'],
            bonuses['high_friend_overlap'],
            bonuses['exact_location'],
            bonuses['identical_photos']
        ])
        
        return bonuses
    
    def _interpret_final_score(self, percentage: float) -> str:
        """Интерпретирует финальную оценку"""
        
        if percentage >= 90:
            return "🟢 ПРАКТИЧЕСКИ ТОЧНО - профили почти наверняка принадлежат одному человеку"
        elif percentage >= 75:
            return "🟢 ВЫСОКАЯ ВЕРОЯТНОСТЬ - очень вероятно это один и тот же человек"
        elif percentage >= 60:
            return "🟡 СРЕДНЯЯ ВЕРОЯТНОСТЬ - вероятно профили принадлежат одному человеку"
        elif percentage >= 40:
            return "🟠 НИЗКАЯ ВЕРОЯТНОСТЬ - маловероятно, но возможно"
        elif percentage >= 20:
            return "🔴 ОЧЕНЬ НИЗКАЯ ВЕРОЯТНОСТЬ - скорее всего разные люди"
        else:
            return "🔴 ПРАКТИЧЕСКИ НЕВОЗМОЖНО - профили почти наверняка разные"
    
    def _calculate_confidence(self, analysis: Dict) -> str:
        """Оценивает уверенность в результате на основе качества данных"""
        
        data_factors = []
        
        # Проверяем наличие данных для каждого фактора
        if analysis.get('name', {}).get('has_data'):
            data_factors.append('name')
        if analysis.get('geolocation', {}).get('has_data'):
            data_factors.append('geolocation')
        if analysis.get('friends', {}).get('has_data'):
            data_factors.append('friends')
        if analysis.get('content', {}).get('has_data'):
            data_factors.append('content')
        if analysis.get('demographics', {}).get('has_data'):
            data_factors.append('demographics')
        if analysis.get('visual', {}).get('has_data'):
            data_factors.append('visual')
        
        factor_count = len(data_factors)
        
        if factor_count >= 5:
            return "Высокая уверенность (достаточно данных)"
        elif factor_count >= 3:
            return "Средняя уверенность (частичные данные)"
        elif factor_count >= 1:
            return "Низкая уверенность (минимум данных)"
        else:
            return "Очень низкая уверенность (недостаточно данных)"
    
    def _assess_data_quality(self, p1: Dict, p2: Dict, f1: Optional[Dict], 
                            f2: Optional[Dict], ph1: Optional[List], 
                            ph2: Optional[List]) -> Dict[str, Any]:
        """Оценивает качество данных для сравнения"""
        
        quality = {
            'profile1_complete': False,
            'profile2_complete': False,
            'has_friends': bool(f1 and f2),
            'has_photos': bool(ph1 and ph2),
            'missing_factors': []
        }
        
        # Проверяем полноту профилей
        required_fields = ['first_name', 'last_name', 'bdate', 'city']
        
        p1_complete = all(p1.get(f) for f in required_fields)
        p2_complete = all(p2.get(f) for f in required_fields)
        
        quality['profile1_complete'] = p1_complete
        quality['profile2_complete'] = p2_complete
        
        if not p1_complete:
            quality['missing_factors'].append('profile1_incomplete')
        if not p2_complete:
            quality['missing_factors'].append('profile2_incomplete')
        if not f1 or not f2:
            quality['missing_factors'].append('no_friends')
        if not ph1 or not ph2:
            quality['missing_factors'].append('no_photos')
        
        return quality
    
    def _generate_detailed_breakdown(self, analysis: Dict) -> List[Dict]:
        """Генерирует детальную разбивку по каждому фактору"""
        
        breakdown = []
        
        factors = [
            ('name', 'Имя', 'name_analysis'),
            ('geolocation', 'Геолокация', 'geo_analysis'),
            ('friends', 'Друзья', 'friends_analysis'),
            ('content', 'Контент', 'content_analysis'),
            ('demographics', 'Демография', 'demo_analysis'),
            ('visual', 'Фотографии', 'visual_analysis'),
        ]
        
        for factor_key, factor_name, analysis_key in factors:
            factor_data = analysis.get(factor_key, {})
            weight = self.weights.get(factor_key, 0)
            score = factor_data.get('score', 0.0)
            has_data = factor_data.get('has_data', False)
            
            breakdown.append({
                'factor': factor_key,
                'name': factor_name,
                'weight': weight,
                'score': score,
                'weighted_score': score * weight,
                'has_data': has_data,
                'interpretation': factor_data.get('interpretation', '')
            })
        
        return breakdown
    
    def export_results(self, results: Dict, output_file: str = None) -> str:
        """
        Экспортирует результаты в JSON
        
        Args:
            results: Результаты сравнения
            output_file: Имя файла для сохранения
            
        Returns:
            JSON строка
        """
        
        json_str = json.dumps(results, ensure_ascii=False, indent=2)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str
    
    def print_summary(self, results: Dict) -> None:
        """Выводит краткую сводку результатов в консоль"""
        
        print("\n" + "="*60)
        print("📊 РЕЗУЛЬТАТ СРАВНЕНИЯ ПРОФИЛЕЙ")
        print("="*60)
        
        final = results.get('final', {})
        scores = results.get('scores', {})
        
        print(f"\n🎯 ИТОГОВАЯ ВЕРОЯТНОСТЬ: {final.get('percentage', 0):.1f}%")
        print(f"   {final.get('interpretation', '')}")
        
        print(f"\n📈 ДЕТАЛИ:")
        breakdown = results.get('detailed_breakdown', [])
        
        for item in breakdown:
            factor = item['name']
            weight = item['weight'] * 100
            score = item['score'] * 100
            has_data = "✓" if item['has_data'] else "✗"
            
            print(f"   {has_data} {factor:15s}: {score:5.1f}% (вес: {weight:4.0f}%)")
        
        print(f"\n⚡ БОНУСЫ:")
        bonuses = scores.get('bonuses', {})
        for bonus_name, bonus_value in bonuses.items():
            if bonus_name != 'total_bonus' and bonus_value > 0:
                print(f"   + {bonus_name:25s}: +{bonus_value*100:.0f}%")
        
        print(f"\n🔍 УВЕРЕННОСТЬ: {final.get('confidence', '')}")
        print(f"   Качество данных: {final.get('data_quality', {})}")
        
        print("\n" + "="*60)


# Пример использования
if __name__ == "__main__":
    # Тестовый запуск
    comparer = ProfileComparer()
    
    # Тестовые данные профилей
    profile1 = {
        'id': 123456,
        'first_name': 'Даниил',
        'last_name': 'Петров',
        'bdate': '15.03.1995',
        'sex': 2,
        'city': {'title': 'Москва'},
        'country': {'title': 'Россия'},
        'home_town': 'Москва',
        'relation': 4,
    }
    
    profile2 = {
        'id': 789012,
        'first_name': 'Данил',
        'last_name': 'Петров',
        'bdate': '15.03.1995',
        'sex': 2,
        'city': {'title': 'Москва'},
        'country': {'title': 'Россия'},
        'home_town': 'Москва',
        'relation': 4,
    }
    
    # Тестовые друзья
    friends1 = {
        'items': [
            {'id': 1, 'first_name': 'Иван', 'last_name': 'Петров'},
            {'id': 2, 'first_name': 'Мария', 'last_name': 'Сидорова'},
            {'id': 3, 'first_name': 'Алексей', 'last_name': 'Иванов'},
        ]
    }
    
    friends2 = {
        'items': [
            {'id': 1, 'first_name': 'Иван', 'last_name': 'Петров'},
            {'id': 2, 'first_name': 'Мария', 'last_name': 'Сидорова'},
            {'id': 4, 'first_name': 'Сергей', 'last_name': 'Кузнецов'},
        ]
    }
    
    print("="*60)
    print("ТЕСТ СРАВНЕНИЯ ПРОФИЛЕЙ")
    print("="*60)
    
    result = comparer.compare_profiles(
        profile1, profile2,
        friends1_data=friends1,
        friends2_data=friends2
    )
    
    comparer.print_summary(result)
