# geo_matcher.py
# Модуль геолокационного анализа и сравнения местоположений

import re
from typing import Dict, List, Tuple, Optional, Set
from difflib import SequenceMatcher

class GeoMatcher:
    """
    Класс для анализа и сравнения геолокационных данных профилей ВК
    
    Функции:
    - Нормализация названий городов
    - Распознавание сокращений (Москва=Мск, СПб=СПБ)
    - Учет часовых поясов
    - Сравнение местоположений с учетом близости
    """
    
    # Словарь известных городов и их вариаций
    CITY_ALIASES = {
        # Москва и область
        'москва': ['москва', 'мск', 'мoscow', 'moscow', 'moskva', 'г. москва', 'москва, россия'],
        'московская область': ['московская область', 'мо', 'подмосковье', 'мoskovskaya oblast'],
        
        # Санкт-Петербург
        'санкт-петербург': ['санкт-петербург', 'спб', 'питер', 'санкт-петербург', 'петербург', 
                           'st. petersburg', 'saint petersburg', 'saint-petersburg', 'петроград', 'ленинград'],
        'ленинградская область': ['ленинградская область', 'ло'],
        
        # Новосибирск
        'новосибирск': ['новосибирск', 'нск', 'новосибирск, россия'],
        
        # Екатеринбург
        'екатеринбург': ['екатеринбург', 'екб', 'свердловск', 'свердловская область'],
        
        # Казань
        'казань': ['казань', 'казане', 'казань, россия'],
        
        # Нижний Новгород
        'нижний новгород': ['нижний новгород', 'нн', 'горький', 'нижний-новгород'],
        
        # Челябинск
        'челябинск': ['челябинск', 'челяба', 'чел'],
        
        # Самара
        'самара': ['самара', 'самарская обл'],
        
        # Омск
        'омск': ['омск', 'омская обл'],
        
        # Ростов-на-Дону
        'ростов-на-дону': ['ростов-на-дону', 'ростов', 'ростовская обл', 'ростов на дону'],
        
        # Уфа
        'уфа': ['уфа', 'уфим'],
        
        # Красноярск
        'красноярск': ['красноярск', 'крск'],
        
        # Пермь
        'пермь': ['пермь', 'пермская обл'],
        
        # Воронеж
        'воронеж': ['воронеж', 'воронежская обл'],
        
        # Волгоград
        'волгоград': ['волгоград', 'сталинград', 'волгоградская обл'],
        
        # Саратов
        'саратов': ['саратов', 'саратовская обл'],
        
        # Тюмень
        'тюмень': ['тюмень', 'тюменская обл'],
        
        # Тольятти
        'тольятти': ['тольятти', 'тольятти, самарская обл'],
        
        # Ижевск
        'ижевск': ['ижевск', 'иж'],
        
        # Барнаул
        'барнаул': ['барнаул', 'барнаульск'],
        
        # Ульяновск
        'ульяновск': ['ульяновск', 'ульяновская обл'],
        
        # Иркутск
        'иркутск': ['иркутск', 'иркутская обл'],
        
        # Хабаровск
        'хабаровск': ['хабаровск', 'хабаровский кр'],
        
        # Ярославль
        'ярославль': ['ярославль', 'ярославская обл'],
        
        # Владимир
        'владимир': ['владимир', 'владимирская обл'],
        
        # Сочи
        'сочи': ['сочи', 'сочи, краснодарский кр'],
        
        # Краснодар
        'краснодар': ['краснодар', 'краснодарский кр', 'кубань'],
        
        # Минск (Беларусь)
        'минск': ['минск', 'minsk', 'минск, беларусь'],
        
        # Киев (Украина)
        'киев': ['киев', 'kyiv', 'kiev', 'київ'],
        
        # Алматы
        'алматы': ['алматы', 'алма-ата', 'almaty'],
        
        # Другие крупные города
        'владивосток': ['владивосток', 'владивосток, приморский кр'],
        'калининград': ['калининград', 'калининградская обл', 'кенигсберг'],
        'тула': ['тула', 'тульская обл'],
        'калуга': ['калуга', 'калужская обл'],
        'рязань': ['рязань', 'рязанская обл'],
        'брянск': ['брянск', 'брянская обл'],
        'курск': ['курск', 'курская обл'],
        'белгород': ['белгород', 'белгородская обл'],
        'липецк': ['липецк', 'липецкая обл'],
    }
    
    # Страны
    COUNTRY_ALIASES = {
        'россия': ['россия', 'рф', 'russia', 'russian federation', 'российская федерация'],
        'украина': ['украина', 'ukraine', 'україна'],
        'беларусь': ['беларусь', 'белоруссия', 'belarus', 'беларусь'],
        'казахстан': ['казахстан', 'kazakhstan', 'казахстан'],
        'германия': ['германия', 'germany', 'deutschland'],
        'сша': ['сша', 'сша', 'usa', 'united states', 'америка', 'america'],
        'великобритания': ['великобритания', 'uk', 'united kingdom', 'британия', 'англия'],
        'израиль': ['израиль', 'israel', 'израиль'],
        'польша': ['польша', 'poland', 'польща'],
        'франция': ['франция', 'france', 'франція'],
        'италия': ['италия', 'italy', 'італія'],
        'испания': ['испания', 'spain', 'испанія'],
        'грузия': ['грузия', 'georgia', 'грузія'],
        'azerbaijan': ['азербайджан', 'azerbaijan', 'азербайджан'],
    }
    
    # Координаты крупных городов (широта, долгота)
    CITY_COORDS = {
        'москва': (55.7558, 37.6173),
        'санкт-петербург': (59.9343, 30.3351),
        'новосибирск': (55.0084, 82.9357),
        'екатеринбург': (56.8389, 60.6057),
        'казань': (55.8304, 49.0661),
        'нижний новгород': (56.2965, 43.9361),
        'челябинск': (55.1644, 61.4368),
        'самара': (53.1955, 50.1002),
        'омск': (54.9924, 73.2316),
        'ростов-на-дону': (47.2278, 39.7150),
        'уфа': (54.7355, 55.9920),
        'красноярск': (56.0086, 92.8700),
        'пермь': (58.0104, 56.2294),
        'воронеж': (51.6606, 39.2003),
        'волгоград': (48.7071, 44.5169),
        'краснодар': (45.0448, 38.9763),
        'владивосток': (43.1332, 131.9113),
        'хабаровск': (48.4802, 135.0719),
        'сочи': (43.6028, 39.7368),
        'минск': (53.9045, 27.5615),
        'киев': (50.4501, 30.5234),
        'алматы': (43.2220, 76.8512),
    }
    
    # Расстояния между близкими городами (км) - для понимания "того же региона"
    CITY_GROUPS = {
        'московский регион': ['москва', 'московская область', 'подольск', 'химки', 'балашиха', 
                            'мытищи', 'королёв', 'люберцы', 'электросталь', 'коломна'],
        'петербургский регион': ['санкт-петербург', 'ленинградская область', 'гатчина', 'выборг'],
        'уральский регион': ['екатеринбург', 'челябинск', 'тюмень', 'пермь'],
        'сибирский регион': ['новосибирск', 'омск', 'красноярск', 'кемерово', 'томск', 'иркутск'],
        'приволжский регион': ['казань', 'нижний новгород', 'самара', 'уфа', 'пермь', 'ижевск', 'оренбург'],
        'южный регион': ['ростов-на-дону', 'волгоград', 'краснодар', 'сочи', 'астрахань'],
        'дальневосточный регион': ['владивосток', 'хабаровск', 'петропавловск-камчатский', 'южно-сахалинск'],
    }
    
    def __init__(self):
        self._build_reverse_aliases()
    
    def _build_reverse_aliases(self):
        """Создает обратный словарь для нормализации"""
        self.city_normalized = {}
        for canonical, aliases in self.CITY_ALIASES.items():
            for alias in aliases:
                self.city_normalized[alias] = canonical
        
        self.country_normalized = {}
        for canonical, aliases in self.COUNTRY_ALIASES.items():
            for alias in aliases:
                self.country_normalized[alias] = canonical
        
        # Создаем группы городов
        self.city_to_group = {}
        for group_name, cities in self.CITY_GROUPS.items():
            for city in cities:
                self.city_to_group[city] = group_name
    
    def normalize_city(self, city) -> str:
        """Нормализует название города"""
        if city is None:
            return ""
        if not isinstance(city, str):
            city = str(city)
        city = city.strip().lower()
        # Проверяем по словарю псевдонимов
        if city in self.city_normalized:
            return self.city_normalized[city]
        # Удаляем "г.", "город" и т.д.
        city_clean = re.sub(r'^(г\.?|город)\s+', '', city)
        if city_clean in self.city_normalized:
            return self.city_normalized[city_clean]
        return city_clean
    
    def normalize_country(self, country) -> str:
        """Нормализует название страны"""
        if country is None:
            return ""
        if not isinstance(country, str):
            country = str(country)
        country = country.strip().lower()
        if country in self.country_normalized:
            return self.country_normalized[country]
        return country
    
    def get_city_coords(self, city: str) -> Optional[Tuple[float, float]]:
        """Возвращает координаты города"""
        normalized = self.normalize_city(city)
        return self.CITY_COORDS.get(normalized)
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Вычисляет расстояние между двумя точками по формуле Хаверсина (в км)"""
        import math
        
        R = 6371  # Радиус Земли в км
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_region(self, city: str) -> Optional[str]:
        """Возвращает регион для города"""
        normalized = self.normalize_city(city)
        return self.city_to_group.get(normalized)
    
    def fuzzy_match(self, city1: str, city2: str) -> float:
        """Нечеткое сравнение названий городов"""
        if not city1 or not city2:
            return 0.0
        
        norm1 = self.normalize_city(city1)
        norm2 = self.normalize_city(city2)
        
        if norm1 == norm2:
            return 1.0
        
        # Проверяем Soundex-подобное сходство
        ratio = SequenceMatcher(None, norm1[:5], norm2[:5]).ratio()
        
        return ratio
    
    def compare_locations(self, location1: Optional[str], location2: Optional[str],
                         country1: Optional[str] = None, country2: Optional[str] = None) -> Dict[str, any]:
        """
        Сравнивает два местоположения
        
        Returns:
            Dict с ключами:
            - exact_match: точное совпадение
            - normalized_match: совпадение после нормализации
            - same_region: в том же регионе
            - distance_km: расстояние в км (если известно)
            - final_score: итоговая оценка (0-1)
        """
        
        if not location1 and not location2:
            return {
                'exact_match': False,
                'normalized_match': False,
                'same_country': False,
                'same_region': False,
                'distance_km': None,
                'final_score': 0.0,
                'details': 'Оба местоположения не указаны'
            }
        
        if not location1 or not location2:
            return {
                'exact_match': False,
                'normalized_match': False,
                'same_country': False,
                'same_region': False,
                'distance_km': None,
                'final_score': 0.1,  # Низкая оценка, но не нулевая - данные отсутствуют
                'details': 'Одно из местоположений не указано'
            }
        
        details = {}
        
        # Точное совпадение (без нормализации, но с безопасным приведением к строке)
        exact_match = (str(location1).strip().lower() == str(location2).strip().lower())
        details['exact_match'] = exact_match
        
        # Нормализованное совпадение
        norm1 = self.normalize_city(location1)
        norm2 = self.normalize_city(location2)
        normalized_match = (norm1 == norm2)
        details['normalized_match'] = normalized_match
        
        # Страна
        same_country = False
        if country1 and country2:
            norm_country1 = self.normalize_country(country1)
            norm_country2 = self.normalize_country(country2)
            same_country = (norm_country1 == norm_country2)
        details['same_country'] = same_country
        
        # Регион
        region1 = self.get_region(norm1)
        region2 = self.get_region(norm2)
        same_region = (region1 is not None and region1 == region2)
        details['same_region'] = same_region
        details['region1'] = region1
        details['region2'] = region2
        
        # Расстояние
        coords1 = self.get_city_coords(norm1)
        coords2 = self.get_city_coords(norm2)
        
        distance_km = None
        if coords1 and coords2:
            distance_km = self.haversine_distance(
                coords1[0], coords1[1], coords2[0], coords2[1]
            )
        details['distance_km'] = distance_km
        
        # Итоговая оценка
        final_score = 0.0
        
        if exact_match:
            final_score = 1.0
        elif normalized_match:
            final_score = 0.95
        elif same_country and same_region:
            final_score = 0.8
        elif same_country:
            # Проверяем расстояние
            if distance_km is not None:
                if distance_km < 50:
                    final_score = 0.7
                elif distance_km < 200:
                    final_score = 0.5
                elif distance_km < 500:
                    final_score = 0.3
                else:
                    final_score = 0.2
            else:
                final_score = 0.4  # Страна совпадает, но расстояние неизвестно
        elif same_region:
            final_score = 0.6
        else:
            # Проверяем нечеткое сходство названий
            fuzzy = self.fuzzy_match(location1, location2)
            final_score = fuzzy * 0.5
        
        return {
            'exact_match': exact_match,
            'normalized_match': normalized_match,
            'same_country': same_country,
            'same_region': same_region,
            'distance_km': distance_km,
            'final_score': final_score,
            'details': details
        }
    
    def analyze_checkins(self, checkins1: List[Dict], checkins2: List[Dict]) -> Dict[str, any]:
        """
        Анализирует совпадение чекинов/геотегов
        
        Args:
            checkins1: Список чекинов первого профиля [{'place': 'место', 'date': 'дата'}, ...]
            checkins2: Список чекинов второго профиля
        """
        
        if not checkins1 or not checkins2:
            return {
                'common_checkins': [],
                'checkin_match_score': 0.0,
                'details': 'Нет данных о чекинах'
            }
        
        places1 = set(self.normalize_city(c.get('place', '')) for c in checkins1 if c.get('place'))
        places2 = set(self.normalize_city(c.get('place', '')) for c in checkins2 if c.get('place'))
        
        common_places = places1 & places2
        
        if not places1 or not places2:
            common_ratio = 0.0
        else:
            common_ratio = len(common_places) / min(len(places1), len(places2))
        
        # Также учитываем даты (если есть)
        dates1 = set(c.get('date', '') for c in checkins1 if c.get('date'))
        dates2 = set(c.get('date', '') for c in checkins2 if c.get('date'))
        common_dates = dates1 & dates2
        
        return {
            'common_checkins': list(common_places),
            'common_dates': list(common_dates),
            'checkin_match_score': common_ratio,
            'total_checkins_1': len(places1),
            'total_checkins_2': len(places2),
            'details': {
                'places1': list(places1),
                'places2': list(places2)
            }
        }
    
    def interpret_score(self, score: float) -> str:
        """Интерпретирует оценку геолокационного совпадения"""
        if score >= 0.95:
            return "Точное местоположение совпадает"
        elif score >= 0.8:
            return "Тот же город/регион"
        elif score >= 0.6:
            return "Возможно один регион"
        elif score >= 0.4:
            return "Одна страна"
        elif score >= 0.2:
            return "Разные местоположения"
        else:
            return "Нет данных для сравнения"


# Пример использования
if __name__ == "__main__":
    geo = GeoMatcher()
    
    # Тесты
    test_cases = [
        ("Москва", "Мск"),
        ("Санкт-Петербург", "СПб"),
        ("Екатеринбург", "Челябинск"),
        ("Москва", "Подольск"),
        ("Минск", "Минск"),
        ("Москва", "Сочи"),
    ]
    
    print("="*60)
    print("ТЕСТ ГЕОЛОКАЦИОННОГО СРАВНЕНИЯ")
    print("="*60)
    
    for loc1, loc2 in test_cases:
        result = geo.compare_locations(loc1, loc2)
        print(f"\n{loc1} vs {loc2}:")
        print(f"  Точное совпадение: {result['exact_match']}")
        print(f"  Нормализованное: {result['normalized_match']}")
        print(f"  Тот же регион: {result['same_region']}")
        print(f"  Расстояние: {result['distance_km']} км")
        print(f"  ИТОГ: {result['final_score']:.2f}")
        print(f"  => {geo.interpret_score(result['final_score'])}")
