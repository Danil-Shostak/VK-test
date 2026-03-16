# friends_matcher.py
# Модуль анализа друзей и социальных связей

import re
from typing import Dict, List, Tuple, Optional, Set
from collections import Counter
from difflib import SequenceMatcher

class FriendsMatcher:
    """
    Класс для анализа и сравнения социальных связей двух профилей
    
    Функции:
    - Анализ общих друзей
    - Анализ общих групп
    - Структурный анализ дружеских связей
    - Выявление паттернов социальных связей
    """
    
    def __init__(self):
        pass
    
    def extract_friend_ids(self, friends_data: Dict) -> Set[int]:
        """Извлекает ID друзей из данных"""
        if not friends_data or 'items' not in friends_data:
            return set()
        
        return {friend.get('id') for friend in friends_data['items'] if friend.get('id')}
    
    def extract_friend_info(self, friends_data: Dict) -> List[Dict]:
        """Извлекает подробную информацию о друзьях"""
        if not friends_data or 'items' not in friends_data:
            return []
        
        friends = []
        for friend in friends_data['items']:
            friend_info = {
                'id': friend.get('id'),
                'first_name': friend.get('first_name', ''),
                'last_name': friend.get('last_name', ''),
                'sex': friend.get('sex', 0),
                'bdate': friend.get('bdate', ''),
                'city': friend.get('city', {}).get('title', '') if friend.get('city') else '',
                'online': friend.get('online', 0),
                'common_count': friend.get('common_count', 0),
                'relation': friend.get('relation', 0),
            }
            friends.append(friend_info)
        
        return friends
    
    def compare_friends(self, friends1: Dict, friends2: Dict) -> Dict[str, any]:
        """
        Сравнивает списки друзей двух профилей
        
        Returns:
            Dict с ключами:
            - common_friends: список общих друзей
            - common_count: количество общих друзей
            - jaccard_index: коэффициент Жаккара
            - friend_overlap_score: оценка пересечения друзей (0-1)
        """
        
        ids1 = self.extract_friend_ids(friends1)
        ids2 = self.extract_friend_ids(friends2)
        
        # Общие друзья
        common_ids = ids1 & ids2
        common_count = len(common_ids)
        
        # Уникальные друзья
        unique_to_1 = ids1 - ids2
        unique_to_2 = ids2 - ids1
        
        # Коэффициент Жаккара
        union = ids1 | ids2
        jaccard_index = len(common_ids) / len(union) if union else 0
        
        # Общая информация о друзьях
        friends_info1 = self.extract_friend_info(friends1)
        friends_info2 = self.extract_friend_info(friends2)
        
        # Находим общих друзей с полной информацией
        common_friends = [f for f in friends_info1 if f['id'] in common_ids]
        
        # Дополнительная информация
        total_friends_1 = len(ids1)
        total_friends_2 = len(ids2)
        
        # Процент от каждого списка
        percent_of_1 = common_count / total_friends_1 if total_friends_1 > 0 else 0
        percent_of_2 = common_count / total_friends_2 if total_friends_2 > 0 else 0
        
        # Оценка пересечения друзей
        # Чем больше общих друзей, тем выше вероятность того, что это один человек
        # Но также важно учитывать размер списков друзей
        
        # Базовая оценка на основе коэффициента Жаккара
        base_score = jaccard_index
        
        # Бонус за большое количество общих друзей
        if common_count >= 10:
            base_score = min(1.0, base_score + 0.2)
        elif common_count >= 5:
            base_score = min(1.0, base_score + 0.1)
        
        # Штраф за очень разные размеры списков друзей
        if total_friends_1 > 0 and total_friends_2 > 0:
            size_ratio = min(total_friends_1, total_friends_2) / max(total_friends_1, total_friends_2)
            base_score *= size_ratio
        
        return {
            'common_friends': common_friends,
            'common_friend_ids': list(common_ids),
            'common_count': common_count,
            'total_friends_1': total_friends_1,
            'total_friends_2': total_friends_2,
            'unique_to_1': list(unique_to_1),
            'unique_to_2': list(unique_to_2),
            'jaccard_index': jaccard_index,
            'percent_of_1': percent_of_1,
            'percent_of_2': percent_of_2,
            'friend_overlap_score': min(1.0, base_score),
            'interpretation': self._interpret_friend_score(common_count, jaccard_index)
        }
    
    def _interpret_friend_score(self, common_count: int, jaccard: float) -> str:
        """Интерпретирует оценку пересечения друзей"""
        if common_count >= 20:
            return "Очень сильное пересечение друзей"
        elif common_count >= 10:
            return "Сильное пересечение друзей"
        elif common_count >= 5:
            return "Значительное пересечение друзей"
        elif common_count >= 1:
            return "Есть общие друзья"
        else:
            return "Нет общих друзей"
    
    def analyze_mutual_friends(self, friend1_id: int, friends1_data: Dict, friends2_data: Dict) -> Dict[str, any]:
        """
        Анализирует взаимных друзей между двумя профилями
        
        Args:
            friend1_id: ID первого профиля
            friends1_data: Список друзей первого профиля
            friends2_data: Список друзей второго профиля
        """
        
        friends2_ids = self.extract_friend_ids(friends2_data)
        
        # Ищем friend1_id в списке друзей второго профиля
        mutual_info = None
        
        if 'items' in friends2_data:
            for friend in friends2_data['items']:
                if friend.get('id') == friend1_id:
                    mutual_info = {
                        'common_count': friend.get('common_count', 0),
                        'is_friend': True
                    }
                    break
        
        return {
            'friend_of_each_other': mutual_info is not None,
            'mutual_info': mutual_info
        }
    
    def analyze_friend_demographics(self, friends_data: Dict) -> Dict[str, any]:
        """
        Анализирует демографические данные друзей
        
        Returns:
            Dict с половой, возрастной, географической статистикой
        """
        
        friends = self.extract_friend_info(friends_data)
        
        if not friends:
            return {
                'sex_distribution': {},
                'avg_age': None,
                'top_cities': [],
                'total_count': 0
            }
        
        # Пол
        sex_counts = Counter(f.get('sex', 0) for f in friends)
        sex_dist = {
            'female': sex_counts.get(1, 0),
            'male': sex_counts.get(2, 0),
            'unknown': sex_counts.get(0, 0)
        }
        
        # Возраст
        ages = []
        for friend in friends:
            bdate = friend.get('bdate', '')
            if bdate and len(bdate.split('.')) >= 3:
                try:
                    year = int(bdate.split('.')[-1])
                    if 1900 < year < 2015:
                        age = 2026 - year
                        if 14 <= age <= 100:
                            ages.append(age)
                except:
                    pass
        
        avg_age = sum(ages) / len(ages) if ages else None
        
        # Города
        city_counts = Counter(f.get('city', '') for f in friends if f.get('city'))
        top_cities = city_counts.most_common(10)
        
        return {
            'sex_distribution': sex_dist,
            'avg_age': avg_age,
            'top_cities': top_cities,
            'total_count': len(friends),
            'age_distribution': {
                'teenagers': len([a for a in ages if 13 <= a <= 19]),
                'young': len([a for a in ages if 20 <= a <= 29]),
                'adults': len([a for a in ages if 30 <= a <= 45]),
                'middle_aged': len([a for a in ages if 45 <= a <= 60]),
                'seniors': len([a for a in ages if a > 60])
            } if ages else {}
        }
    
    def compare_friend_demographics(self, friends1: Dict, friends2: Dict) -> Dict[str, any]:
        """Сравнивает демографические данные друзей двух профилей"""
        
        demo1 = self.analyze_friend_demographics(friends1)
        demo2 = self.analyze_friend_demographics(friends2)
        
        # Сравнение возраста
        age_score = 0.0
        if demo1['avg_age'] and demo2['avg_age']:
            age_diff = abs(demo1['avg_age'] - demo2['avg_age'])
            if age_diff < 5:
                age_score = 1.0
            elif age_diff < 10:
                age_score = 0.7
            elif age_diff < 15:
                age_score = 0.4
            else:
                age_score = 0.1
        
        # Сравнение пола
        sex_score = 0.0
        total1 = demo1['sex_distribution']['female'] + demo1['sex_distribution']['male']
        total2 = demo2['sex_distribution']['female'] + demo2['sex_distribution']['male']
        
        if total1 > 0 and total2 > 0:
            ratio1 = demo1['sex_distribution']['female'] / total1
            ratio2 = demo2['sex_distribution']['female'] / total2
            sex_diff = abs(ratio1 - ratio2)
            
            if sex_diff < 0.1:
                sex_score = 1.0
            elif sex_diff < 0.2:
                sex_score = 0.7
            elif sex_diff < 0.3:
                sex_score = 0.4
            else:
                sex_score = 0.2
        
        # Сравнение городов
        cities1 = set(c[0] for c in demo1['top_cities'][:5])
        cities2 = set(c[0] for c in demo2['top_cities'][:5])
        common_cities = cities1 & cities2
        
        city_score = len(common_cities) / max(len(cities1), len(cities2), 1) if cities1 and cities2 else 0
        
        return {
            'demo1': demo1,
            'demo2': demo2,
            'age_comparison': {
                'age1': demo1['avg_age'],
                'age2': demo2['avg_age'],
                'score': age_score
            },
            'sex_comparison': {
                'score': sex_score
            },
            'city_comparison': {
                'common_cities': list(common_cities),
                'score': city_score
            },
            'overall_demographic_score': (age_score + sex_score + city_score) / 3
        }
    
    def analyze_social_network_structure(self, friends1: Dict, friends2: Dict) -> Dict[str, any]:
        """
        Анализирует структуру социальных сетей
        
        Идея: Если два профиля имеют много общих друзей, 
        это может указывать на то, что они один человек
        """
        
        comparison = self.compare_friends(friends1, friends2)
        
        # Анализируем "общих друзей друзей"
        # Если у общих друзей много общих друзей между собой, это усиливает вероятность
        
        return {
            'friend_comparison': comparison,
            'is_same_social_circle': comparison['friend_overlap_score'] > 0.3,
            'strength_indicators': {
                'high_common_friends': comparison['common_count'] >= 10,
                'similar_friend_count': 0.5 < (comparison['total_friends_1'] / max(comparison['total_friends_2'], 1)) < 2.0,
                'high_jaccard': comparison['jaccard_index'] > 0.1
            }
        }


# Пример использования
if __name__ == "__main__":
    matcher = FriendsMatcher()
    
    # Тестовые данные
    friends1 = {
        'items': [
            {'id': 1, 'first_name': 'Иван', 'last_name': 'Петров', 'sex': 2},
            {'id': 2, 'first_name': 'Мария', 'last_name': 'Сидорова', 'sex': 1},
            {'id': 3, 'first_name': 'Алексей', 'last_name': 'Иванов', 'sex': 2},
            {'id': 4, 'first_name': 'Елена', 'last_name': 'Козлова', 'sex': 1},
            {'id': 5, 'first_name': 'Дмитрий', 'last_name': 'Смирнов', 'sex': 2},
        ]
    }
    
    friends2 = {
        'items': [
            {'id': 1, 'first_name': 'Иван', 'last_name': 'Петров', 'sex': 2},
            {'id': 2, 'first_name': 'Мария', 'last_name': 'Сидорова', 'sex': 1},
            {'id': 6, 'first_name': 'Сергей', 'last_name': 'Кузнецов', 'sex': 2},
            {'id': 7, 'first_name': 'Анна', 'last_name': 'Васильева', 'sex': 1},
        ]
    }
    
    print("="*60)
    print("ТЕСТ АНАЛИЗА ДРУЗЕЙ")
    print("="*60)
    
    result = matcher.compare_friends(friends1, friends2)
    print(f"\nОбщие друзья: {result['common_count']}")
    print(f"Коэффициент Жаккара: {result['jaccard_index']:.3f}")
    print(f"Оценка пересечения: {result['friend_overlap_score']:.3f}")
    print(f"Интерпретация: {result['interpretation']}")
