# demographics_matcher.py
# Модуль сравнения демографических данных

import re
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime

class DemographicsMatcher:
    """
    Класс для сравнения демографических данных профилей
    
    Функции:
    - Сравнение дат рождения
    - Сравнение образования
    - Сравнение работы/карьеры
    - Сравнение семейного положения
    - Сравнение других демографических данных
    """
    
    # Карьерные названия (для нормализации)
    JOB_KEYWORDS = {
        'it': ['программист', 'разработчик', 'developer', 'it', 'инженер', 'frontend', 'backend', 
               'fullstack', 'devops', 'qa', 'тестировщик', 'аналитик', 'сисадмин', 'админ'],
        'manager': ['менеджер', 'manager', 'руководитель', 'директор', 'начальник', 'head', 'lead'],
        'designer': ['дизайнер', 'designer', 'artist', 'художник', 'illustrator'],
        'teacher': ['учитель', 'преподаватель', 'учетель', 'педагог', 'профессор', 'доцент'],
        'doctor': ['врач', 'доктор', 'medic', 'медик', 'хирург', 'терапевт', 'стоматолог'],
        'lawyer': ['юрист', 'адвокат', 'нотариус', 'lawyer', 'legal'],
        'finance': ['бухгалтер', 'финансист', 'экономист', 'accountant', 'finance', 'bank'],
        'marketing': ['маркетолог', 'marketing', 'smm', 'pr', 'специалист по рекламе'],
        'sales': ['продавец', 'консультант', 'sales', 'merchandiser'],
        'student': ['студент', 'учащийся', 'школьник', 'ученик', 'student'],
    }
    
    # Семейное положение
    RELATION_MAP = {
        1: 'не замужем / не женат',
        2: 'есть друг / есть подруга',
        3: 'помолвлен / помолвлена',
        4: 'женат / замужем',
        5: 'всё сложно',
        6: 'в активном поиске',
        7: 'влюблён / влюблена',
        8: 'в гражданском браке',
    }
    
    def __init__(self):
        pass
    
    def parse_birthdate(self, bdate: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """
        Парсит дату рождения
        
        Args:
            bdate: Строка вида "DD.MM.YYYY" или "DD.MM"
            
        Returns:
            Кортеж (день, месяц, год)
        """
        
        if not bdate:
            return None, None, None
        
        parts = bdate.split('.')
        
        day = int(parts[0]) if len(parts) >= 1 and parts[0].isdigit() else None
        month = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else None
        year = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else None
        
        return day, month, year
    
    def calculate_age(self, bdate: str) -> Optional[int]:
        """Вычисляет возраст по дате рождения"""
        
        day, month, year = self.parse_birthdate(bdate)
        
        if not year:
            return None
        
        current_year = datetime.now().year
        
        # Проверяем, что год реалистичный
        if year < 1900 or year > 2015:
            return None
        
        age = current_year - year
        
        # Учитываем месяц и день для точности
        if month:
            current_month = datetime.now().month
            if month > current_month:
                age -= 1
            elif month == current_month and day:
                current_day = datetime.now().day
                if day > current_day:
                    age -= 1
        
        return age if 0 < age < 120 else None
    
    def compare_birthdates(self, bdate1: str, bdate2: str) -> Dict[str, any]:
        """
        Сравнивает даты рождения
        
        Args:
            bdate1: Дата рождения первого профиля
            bdate2: Дата рождения второго профиля
        """
        
        day1, month1, year1 = self.parse_birthdate(bdate1)
        day2, month2, year2 = self.parse_birthdate(bdate2)
        
        # Если обе даты полные
        if year1 and year2:
            exact_match = (day1 == day2 and month1 == month2 and year1 == year2)
            
            # Если только год совпадает
            year_match = (year1 == year2)
            
            # Близкие года (разница до 3 лет)
            close_years = (abs(year1 - year2) <= 3)
            
            return {
                'exact_match': exact_match,
                'year_match': year_match,
                'close_years': close_years,
                'age1': self.calculate_age(bdate1),
                'age2': self.calculate_age(bdate2),
                'year_diff': abs(year1 - year2) if year1 and year2 else None,
                'final_score': 1.0 if exact_match else (0.9 if year_match else (0.6 if close_years else 0.0)),
                'interpretation': self._interpret_birthdate(exact_match, year_match, close_years)
            }
        
        # Если только год известен
        if year1 or year2:
            return {
                'partial_info': True,
                'year1': year1,
                'year2': year2,
                'final_score': 0.3,
                'interpretation': 'Год рождения указан только у одного профиля'
            }
        
        # Нет данных
        return {
            'no_data': True,
            'final_score': 0.0,
            'interpretation': 'Даты рождения не указаны'
        }
    
    def _interpret_birthdate(self, exact: bool, year_match: bool, close_years: bool) -> str:
        """Интерпретирует результат сравнения дат рождения"""
        
        if exact:
            return "Точное совпадение дат рождения"
        elif year_match:
            return "Одинаковый год рождения"
        elif close_years:
            return "Близкие года рождения (разница до 3 лет)"
        else:
            return "Разные даты рождения"
    
    def compare_sex(self, sex1: int, sex2: int) -> Dict[str, any]:
        """
        Сравнивает пол
        
        Args:
            sex1: Пол первого профиля (1 - женский, 2 - мужской, 0 - не указан)
            sex2: Пол второго профиля
        """
        
        # 0 означает неопределенный пол
        if sex1 == 0 or sex2 == 0:
            return {
                'match': sex1 == sex2,
                'score': 0.5,
                'interpretation': 'Пол одного из профилей не указан'
            }
        
        match = (sex1 == sex2)
        
        return {
            'match': match,
            'score': 1.0 if match else 0.0,
            'interpretation': 'Пол совпадает' if match else 'Пол разный'
        }
    
    def normalize_education(self, education: Dict) -> List[str]:
        """Нормализует данные об образовании"""
        
        if not education:
            return []
        
        results = []
        
        # Университет
        if 'university' in education and education['university']:
            results.append(str(education['university']).lower())
        
        if 'university_name' in education and education['university_name']:
            results.append(str(education['university_name']).lower())
        
        # Факультет
        if 'faculty' in education and education['faculty']:
            results.append(str(education['faculty']).lower())
        
        if 'faculty_name' in education and education['faculty_name']:
            results.append(str(education['faculty_name']).lower())
        
        # Год выпуска
        if 'graduation' in education and education['graduation']:
            results.append(str(education['graduation']))
        
        return results
    
    def compare_education(self, edu1: Dict, edu2: Dict) -> Dict[str, any]:
        """
        Сравнивает образование
        
        Args:
            edu1: Данные об образовании первого профиля
            edu2: Данные об образовании второго профиля
        """
        
        norm1 = self.normalize_education(edu1)
        norm2 = self.normalize_education(edu2)
        
        if not norm1 and not norm2:
            return {
                'match': False,
                'score': 0.0,
                'interpretation': 'Образование не указано'
            }
        
        if not norm1 or not norm2:
            return {
                'match': False,
                'score': 0.2,
                'interpretation': 'Образование указано только у одного профиля'
            }
        
        # Проверяем совпадения
        common = set(norm1) & set(norm2)
        
        # Проверяем совпадение выпуска
        grad1 = [n for n in norm1 if n.isdigit()]
        grad2 = [n for n in norm2 if n.isdigit()]
        
        same_graduation = bool(grad1 and grad2 and grad1[0] == grad2[0])
        
        if common:
            return {
                'match': True,
                'common_education': list(common),
                'same_graduation': same_graduation,
                'score': 0.8 if same_graduation else 0.5,
                'interpretation': 'Совпадение в образовании'
            }
        
        return {
            'match': False,
            'score': 0.0,
            'interpretation': 'Образование разное'
        }
    
    def compare_career(self, career1: List[Dict], career2: List[Dict]) -> Dict[str, any]:
        """
        Сравнивает карьеру/работу
        
        Args:
            career1: Список мест работы первого профиля
            career2: Список мест работы второго профиля
        """
        
        if not career1 and not career2:
            return {
                'match': False,
                'score': 0.0,
                'interpretation': 'Информация о работе не указана'
            }
        
        if not career1 or not career2:
            return {
                'match': False,
                'score': 0.2,
                'interpretation': 'Информация о работе указана только у одного профиля'
            }
        
        # Извлекаем названия компаний
        companies1 = set()
        positions1 = set()
        
        for job in career1:
            if job.get('company'):
                companies1.add(str(job['company']).lower())
            if job.get('position'):
                positions1.add(str(job['position']).lower())
        
        companies2 = set()
        positions2 = set()
        
        for job in career2:
            if job.get('company'):
                companies2.add(str(job['company']).lower())
            if job.get('position'):
                positions2.add(str(job['position']).lower())
        
        # Проверяем совпадения
        common_companies = companies1 & companies2
        common_positions = positions1 & positions2
        
        # Проверяем тип работы (категория)
        def categorize_position(positions: Set[str]) -> Set[str]:
            categories = set()
            for pos in positions:
                for category, keywords in self.JOB_KEYWORDS.items():
                    if any(kw in pos for kw in keywords):
                        categories.add(category)
            return categories
        
        cats1 = categorize_position(positions1)
        cats2 = categorize_position(positions2)
        
        same_category = bool(cats1 & cats2)
        
        if common_companies:
            return {
                'match': True,
                'common_companies': list(common_companies),
                'same_category': same_category,
                'score': 0.9,
                'interpretation': 'Одинаковые места работы'
            }
        
        if common_positions:
            return {
                'match': True,
                'common_positions': list(common_positions),
                'same_category': same_category,
                'score': 0.7,
                'interpretation': 'Похожие должности'
            }
        
        if same_category:
            return {
                'match': False,
                'same_category': True,
                'categories': list(cats1 & cats2),
                'score': 0.4,
                'interpretation': 'Одинаковая сфера деятельности'
            }
        
        return {
            'match': False,
            'score': 0.0,
            'interpretation': 'Разная работа'
        }
    
    def compare_relation(self, relation1: int, relation2: int) -> Dict[str, any]:
        """Сравнивает семейное положение"""
        
        # Если оба не указаны
        if relation1 == 0 and relation2 == 0:
            return {
                'match': False,
                'score': 0.0,
                'interpretation': 'Семейное положение не указано'
            }
        
        if relation1 == 0 or relation2 == 0:
            return {
                'match': False,
                'score': 0.3,
                'interpretation': 'Семейное положение указано только у одного'
            }
        
        match = (relation1 == relation2)
        
        # Особые случаи
        # Оба в браке
        both_married = (relation1 == 4 and relation2 == 4)
        
        # Оба свободны
        both_single = (relation1 == 1 and relation2 == 1)
        
        return {
            'match': match,
            'both_married': both_married,
            'both_single': both_single,
            'score': 1.0 if match else 0.3,
            'interpretation': self.RELATION_MAP.get(relation1, 'неизвестно') + ' vs ' + self.RELATION_MAP.get(relation2, 'неизвестно')
        }
    
    def compare_all_demographics(self, user1: Dict, user2: Dict) -> Dict[str, any]:
        """
        Комплексное сравнение всех демографических данных
        
        Args:
            user1: Данные первого пользователя
            user2: Данные второго пользователя
        """
        
        results = {}
        
        # Дата рождения
        bdate1 = user1.get('bdate', '')
        bdate2 = user2.get('bdate', '')
        results['birthdate'] = self.compare_birthdates(bdate1, bdate2)
        
        # Пол
        sex1 = user1.get('sex', 0)
        sex2 = user2.get('sex', 0)
        results['sex'] = self.compare_sex(sex1, sex2)
        
        # Образование
        edu1 = user1.get('education', {})
        edu2 = user2.get('education', {})
        results['education'] = self.compare_education(edu1, edu2)
        
        # Также проверяем universities
        if not edu1 and user1.get('universities'):
            edu1 = user1['universities'][0] if user1['universities'] else {}
        if not edu2 and user2.get('universities'):
            edu2 = user2['universities'][0] if user2['universities'] else {}
        
        if edu1 and edu2:
            results['education'] = self.compare_education(edu1, edu2)
        
        # Карьера
        career1 = user1.get('career', [])
        career2 = user2.get('career', [])
        results['career'] = self.compare_career(career1, career2)
        
        # Семейное положение
        rel1 = user1.get('relation', 0)
        rel2 = user2.get('relation', 0)
        results['relation'] = self.compare_relation(rel1, rel2)
        
        # Родной город
        home_town1 = user1.get('home_town', '')
        home_town2 = user2.get('home_town', '')
        
        # Приводим к строке, если передано число
        if not isinstance(home_town1, str):
            home_town1 = str(home_town1) if home_town1 else ''
        if not isinstance(home_town2, str):
            home_town2 = str(home_town2) if home_town2 else ''
        
        if home_town1 and home_town2:
            results['home_town'] = {
                'match': (home_town1.lower() == home_town2.lower()),
                'score': 1.0 if home_town1.lower() == home_town2.lower() else 0.0,
                'home_town1': home_town1,
                'home_town2': home_town2
            }
        
        # Рассчитываем общую оценку
        scores = []
        for key, result in results.items():
            if 'score' in result:
                scores.append(result['score'])
        
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        results['overall_demographics_score'] = overall_score
        results['interpretation'] = self._interpret_demographics(overall_score)
        
        return results
    
    def _interpret_demographics(self, score: float) -> str:
        """Интерпретирует общую оценку демографии"""
        
        if score >= 0.9:
            return "Практически полное совпадение демографических данных"
        elif score >= 0.7:
            return "Сильное совпадение демографических данных"
        elif score >= 0.5:
            return "Частичное совпадение демографических данных"
        elif score >= 0.3:
            return "Минимальное совпадение демографических данных"
        else:
            return "Разные демографические данные или недостаточно данных"


# Пример использования
if __name__ == "__main__":
    matcher = DemographicsMatcher()
    
    print("="*60)
    print("ТЕСТ ДЕМОГРАФИЧЕСКОГО СРАВНЕНИЯ")
    print("="*60)
    
    # Тест дат рождения
    print("\nСравнение дат рождения:")
    result = matcher.compare_birthdates("15.03.1995", "15.03.1995")
    print(f"15.03.1995 vs 15.03.1995: {result['interpretation']} (score: {result['final_score']})")
    
    result = matcher.compare_birthdates("15.03.1995", "20.08.1995")
    print(f"15.03.1995 vs 20.08.1995: {result['interpretation']} (score: {result['final_score']})")
    
    result = matcher.compare_birthdates("15.03.1995", "15.03.1998")
    print(f"15.03.1995 vs 15.03.1998: {result['interpretation']} (score: {result['final_score']})")
    
    # Тест пола
    print("\nСравнение пола:")
    result = matcher.compare_sex(2, 2)
    print(f"Мужской vs Мужской: {result['interpretation']}")
    
    result = matcher.compare_sex(2, 1)
    print(f"Мужской vs Женский: {result['interpretation']}")
    
    # Тест полного сравнения
    print("\nТест полного сравнения:")
    user1 = {'bdate': '15.03.1995', 'sex': 2, 'relation': 4}
    user2 = {'bdate': '15.03.1995', 'sex': 2, 'relation': 4}
    
    result = matcher.compare_all_demographics(user1, user2)
    print(f"Общая оценка: {result['overall_demographics_score']:.2f}")
    print(f"Интерпретация: {result['interpretation']}")
