# social_geo_analyzer.py
# Модуль анализа геолокационной структуры социальных сетей (центроиды, плотность)

import math
from typing import Dict, List, Tuple, Optional, Set
from collections import Counter

from .geo_matcher import GeoMatcher


class SocialGeoAnalyzer:
    """
    Анализер географической структуры социальных сетей
    
    Функции:
    - Геокодирование городов друзей в координаты
    - Вычисление географического центроида сети друзей
    - Сравнение центроидов двух профилей (Haversine distance)
    - Анализ плотности пересечения социальных кластеров (spatial overlap density)
    - Устойчивость к пропущенным/неполным данным
    """
    
    # Настройки радиуса для анализа пересечения
    BASE_RADIUS_KM = 100  # Базовый радиус
    MAX_RADIUS_KM = 300   # Максимальный радиус
    DISTANCE_FACTOR = 0.5  # Коэффициент: радиус = база + (расстояние_между_центроидами * фактор)
    
    def __init__(self, geo_matcher: Optional[GeoMatcher] = None):
        """
        Инициализирует анализатор
        
        Args:
            geo_matcher: Экземпляр GeoMatcher (если None - создается новый)
        """
        self.geo_matcher = geo_matcher or GeoMatcher()
    
    def geocode_friend_locations(self, friends_data: Dict) -> List[Tuple[float, float]]:
        """
        Преобразует города друзей в координаты (геокодирование)
        
        Args:
            friends_data: Данные друзей из VK API
            
        Returns:
            Список кортежей (широта, долгота) для каждого друга с известным городом
        """
        if not friends_data or 'items' not in friends_data:
            return []
        
        coordinates = []
        
        for friend in friends_data['items']:
            city = friend.get('city', {})
            city_title = city.get('title', '') if isinstance(city, dict) else (city if isinstance(city, str) else '')
            
            if not city_title:
                continue
            
            coords = self.geo_matcher.get_city_coords(city_title)
            if coords:
                coordinates.append(coords)
        
        return coordinates
    
    def calculate_centroid(self, coordinates: List[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
        """
        Вычисляет географический центроид (среднее арифметическое координат)
        
        Args:
            coordinates: Список кортежей (lat, lon)
            
        Returns:
            Кортеж (средняя_широта, средняя_долгота) или None если нет данных
        """
        if not coordinates:
            return None
        
        total_lat = sum(lat for lat, _ in coordinates)
        total_lon = sum(lon for _, lon in coordinates)
        count = len(coordinates)
        
        return (total_lat / count, total_lon / count)
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Вычисляет расстояние между двумя точками по формуле Хаверисайна
        
        Returns:
            Расстояние в километрах
        """
        return self.geo_matcher.haversine_distance(lat1, lon1, lat2, lon2)
    
    def centroid_proximity(self, friends1: List[Tuple[float, float]], 
                          friends2: List[Tuple[float, float]]) -> Dict[str, any]:
        """
        Вычисляет расстояние между центроидами двух дружеских сетей
        
        Args:
            friends1: Координаты друзей первого профиля
            friends2: Координаты друзей второго профиля
            
        Returns:
            Dict с результатами:
            - centroid1: центроид первой сети (или None)
            - centroid2: центроид второй сети (или None)
            - distance_km: расстояние между центроидами (или None)
            - has_data: есть ли данные для сравнения
            - interpretation: текстовое описание
        """
        centroid1 = self.calculate_centroid(friends1)
        centroid2 = self.calculate_centroid(friends2)
        
        if not centroid1 or not centroid2:
            return {
                'centroid1': centroid1,
                'centroid2': centroid2,
                'distance_km': None,
                'has_data': False,
                'interpretation': 'Недостаточно данных для расчета центроидов (нет координат городов друзей)',
                'friends1_count': len(friends1),
                'friends2_count': len(friends2)
            }
        
        distance = self.haversine_distance(
            centroid1[0], centroid1[1],
            centroid2[0], centroid2[1]
        )
        
        # Интерпретация расстояния
        if distance < 50:
            interpretation = "Очень близкие социальные кластеры (менее 50 км)"
        elif distance < 200:
            interpretation = "Умеренное удаление социальных кластеров (50-200 км)"
        elif distance < 500:
            interpretation = "Дальние социальные кластеры (200-500 км)"
        elif distance < 1000:
            interpretation = "Очень дальние кластеры (500-1000 км)"
        else:
            interpretation = "Крайне далекие кластеры (более 1000 км)"
        
        return {
            'centroid1': centroid1,
            'centroid2': centroid2,
            'distance_km': round(distance, 2),
            'has_data': True,
            'interpretation': interpretation,
            'friends1_coordinates': len(friends1),
            'friends2_coordinates': len(friends2)
        }
    
    def _get_adaptive_radius(self, centroid1: Tuple[float, float], 
                            centroid2: Tuple[float, float]) -> float:
        """
        Вычисляет адаптивный радиус в зависимости от расстояния между центроидами.
        
        Более далекие кластеры получают больший радиус для учета их географического размаха.
        """
        distance = self.haversine_distance(centroid1[0], centroid1[1], 
                                            centroid2[0], centroid2[1])
        
        # Радиус = база + (расстояние * фактор)
        radius = self.BASE_RADIUS_KM + (distance * self.DISTANCE_FACTOR)
        
        # Ограничиваем максимумом
        return min(radius, self.MAX_RADIUS_KM)
    
    def spatial_overlap_density(self, source_coords: List[Tuple[float, float]],
                               target_centroid: Tuple[float, float],
                               base_radius_km: float = None) -> float:
        """
        Вычисляет долю друзей source-сети, находящихся в заданном радиусе от target_centroid
        
        Args:
            source_coords: Координаты друзей источника
            target_centroid: Центроид целевой сети
            base_radius_km: Базовый радиус в км (по умолчанию self.BASE_RADIUS_KM)
            
        Returns:
            Процент (0-1) друзей источника в радиусе от target-центроида
        """
        if not source_coords or not target_centroid:
            return 0.0
        
        radius = base_radius_km or self.BASE_RADIUS_KM
        count_in_radius = 0
        
        for coord in source_coords:
            distance = self.haversine_distance(
                coord[0], coord[1],
                target_centroid[0], target_centroid[1]
            )
            if distance <= radius:
                count_in_radius += 1
        
        return count_in_radius / len(source_coords)
    
    def analyze_social_geo_overlap(self, friends1_data: Dict, friends2_data: Dict) -> Dict[str, any]:
        """
        Полный анализ географического пересечения социальных сетей
        
        Args:
            friends1_data: Данные друзей первого профиля
            friends2_data: Данные друзей второго профиля
            
        Returns:
            Комплексный отчет с метриками:
            - centroid_distance_km: расстояние между центроидами
            - overlap_1_in_2: % друзей профиля1 в радиусе от центроида профиля2
            - overlap_2_in_1: % друзей профиля2 в радиусе от центроида профиля1
            - mutual_overlap: симметричное пересечение (min из двух)
            - geo_cluster_similarity: итоговая оценка схожести геолокационных кластеров (0-1)
            - interpretation: текстовое описание
        """
        # Геокодируем города друзей
        coords1 = self.geocode_friend_locations(friends1_data)
        coords2 = self.geocode_friend_locations(friends2_data)
        
        # Вычисляем центроиды
        centroid1 = self.calculate_centroid(coords1)
        centroid2 = self.calculate_centroid(coords2)
        
        # Расстояние между центроидами
        proximity = self.centroid_proximity(coords1, coords2)
        
        # Плотность пересечения (если есть оба центроида)
        overlap_1_in_2 = 0.0
        overlap_2_in_1 = 0.0
        mutual_overlap = 0.0
        used_radius = self.BASE_RADIUS_KM  # значение по умолчанию для отображения
        
        if centroid1 and centroid2:
            # Вычисляем адаптивный радиус на основе расстояния между центроидами
            used_radius = self._get_adaptive_radius(centroid1, centroid2)
            
            # Считаем пересечение с этим радиусом
            overlap_1_in_2 = self.spatial_overlap_density(coords1, centroid2, base_radius_km=used_radius)
            overlap_2_in_1 = self.spatial_overlap_density(coords2, centroid1, base_radius_km=used_radius)
            mutual_overlap = min(overlap_1_in_2, overlap_2_in_1)
        
        # Комбинированная оценка схожести гео-кластеров
        geo_cluster_similarity = 0.0
        
        if proximity['has_data']:
            distance_km = proximity['distance_km']
            
            # Базовая оценка на основе расстояния центроидов (обратная зависимость)
            # Чем ближе — тем выше. Нормализуем: 0 км → 1.0, 500 км → 0.0
            distance_score = max(0.0, 1.0 - (distance_km / 500.0))
            
            # Оценка плотности пересечения
            density_score = mutual_overlap
            
            # КОРРЕКЦИЯ: если расстояние мало (<20 км) но overlap = 0,
            # это contradicts логике — либо данные некорректны, сильно снижаем
            if distance_km < 20 and mutual_overlap < 0.1:
                # Нет пересечения при близости центроидов — погрешность/ошибка
                geo_cluster_similarity = 0.1  # минимальный балл
            elif mutual_overlap >= 0.5:
                # Большое пересечение — высокий балл, расстояние второстепенно
                geo_cluster_similarity = 0.8 + density_score * 0.2
            elif mutual_overlap >= 0.2:
                # Умеренное пересечение
                geo_cluster_similarity = distance_score * 0.4 + density_score * 0.6
            elif mutual_overlap > 0:
                # Маленькое, но ненулевое пересечение
                geo_cluster_similarity = distance_score * 0.6 + density_score * 0.4
            else:
                # Нет пересечения — только расстояние, но с пониженным весом
                geo_cluster_similarity = distance_score * 0.3
        
        # Есть ли данные для анализа?
        has_data = len(coords1) > 0 and len(coords2) > 0 and centroid1 is not None and centroid2 is not None
        
        # Интерпретация
        interpretation = self._interpret_geo_similarity(
            proximity.get('distance_km'),
            mutual_overlap,
            geo_cluster_similarity
        )
        
        return {
            'coords1_count': len(coords1),
            'coords2_count': len(coords2),
            'centroid1': centroid1,
            'centroid2': centroid2,
            'centroid_distance_km': proximity.get('distance_km'),
            'overlap_1_in_2': round(overlap_1_in_2, 4),
            'overlap_2_in_1': round(overlap_2_in_1, 4),
            'mutual_overlap': round(mutual_overlap, 4),
            'geo_cluster_similarity': round(geo_cluster_similarity, 4),
            'has_data': has_data,
            'interpretation': interpretation,
            'details': {
                'centroid_proximity': proximity,
                'spatial_analysis': {
                    'radius_km': round(used_radius, 1),
                    'friends1_in_radius': int(overlap_1_in_2 * len(coords1)) if coords1 else 0,
                    'friends2_in_radius': int(overlap_2_in_1 * len(coords2)) if coords2 else 0
                }
            }
        }
    
    def _interpret_geo_similarity(self, distance: Optional[float], 
                                 mutual_overlap: float, 
                                 similarity: float) -> str:
        """Интерпретирует результаты гео-анализа"""
        
        if distance is None:
            return "Недостаточно данных для географического анализа социальных кластеров"
        
        if similarity >= 0.8:
            return "Очень высокая географическая схожесть социальных кластеров - вероятно один город/регион"
        elif similarity >= 0.6:
            return "Высокая географическая схожесть - близкие социальные окружения"
        elif similarity >= 0.4:
            return "Умеренная географическая схожесть - частично пересекающиеся социальные круги"
        elif similarity >= 0.2:
            return "Низкая географическая схожесть - разные регионы"
        else:
            return "Очень низкая географическая схожесть - социальные кластеры в разных частях страны/мира"


# Пример использования
if __name__ == "__main__":
    analyzer = SocialGeoAnalyzer()
    
    # Тестовые данные друзей
    friends1 = {
        'items': [
            {'city': {'title': 'Москва'}},
            {'city': {'title': 'Москва'}},
            {'city': {'title': 'Санкт-Петербург'}},
            {'city': {'title': 'Москва'}},
            {'city': {'title': 'Подольск'}},
        ]
    }
    
    friends2 = {
        'items': [
            {'city': {'title': 'Москва'}},
            {'city': {'title': 'Москва'}},
            {'city': {'title': 'Химки'}},
            {'city': {'title': 'Москва'}},
            {'city': {'title': 'Мытищи'}},
        ]
    }
    
    print("="*60)
    print("ТЕСТ ГЕОГРАФИЧЕСКОГО АНАЛИЗА СОЦИАЛЬНЫХ СЕТЕЙ")
    print("="*60)
    
    result = analyzer.analyze_social_geo_overlap(friends1, friends2)
    
    print(f"\nКоординатов друзей профиля1: {result['coords1_count']}")
    print(f"Координатов друзей профиля2: {result['coords2_count']}")
    print(f"Центроид 1: {result['centroid1']}")
    print(f"Центроид 2: {result['centroid2']}")
    print(f"Расстояние между центроидами: {result['centroid_distance_km']} км")
    print(f"Пересечение (профиль1 → центроид профиля2): {result['overlap_1_in_2']:.2%}")
    print(f"Пересечение (профиль2 → центроид профиля1): {result['overlap_2_in_1']:.2%}")
    print(f"Взаимное пересечение: {result['mutual_overlap']:.2%}")
    print(f"Оценка гео-схожести: {result['geo_cluster_similarity']:.2%}")
    print(f"Интерпретация: {result['interpretation']}")
