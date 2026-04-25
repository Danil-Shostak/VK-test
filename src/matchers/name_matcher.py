# name_matcher.py
# Модуль сравнения имен с использованием NLP, нечеткого сопоставления и фонетического анализа

import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional

class NameMatcher:
    """
    Класс для сравнения имен с использованием множества методов:
    - Точное совпадение
    - Нечеткое сопоставление (fuzzy matching)
    - Фонетический анализ (Soundex, Metaphone)
    - Анализ вариаций и сокращений имен
    """
    
    # Словарь вариаций русских имен
    NAME_VARIATIONS = {
        # Даниил и его вариации
        'даниил': ['даниил', 'данил', 'данила', 'данилка', 'даня', 'данек', 'даник', 'данилко'],
        'данил': ['даниил', 'данил', 'данила', 'данилка', 'даня', 'данек', 'даник', 'данилко'],
        'данила': ['даниил', 'данил', 'данила', 'данилка', 'даня', 'данек', 'даник', 'данилко'],
        'даня': ['даниил', 'данил', 'данила', 'данилка', 'даня', 'данек', 'даник', 'данилко'],
        
        # Дмитрий
        'дмитрий': ['дмитрий', 'дима', 'димка', 'димон', 'дimitрий', 'димас'],
        
        # Александр
        'александр': ['александр', 'алексей', 'алекс', 'саша', 'саня', 'шурка', 'алексан'],
        
        # Алексей
        'алексей': ['алексей', 'алекс', 'лёша', 'лёшка', 'алешка'],
        
        # Андрей
        'андрей': ['андрей', 'андрюха', 'андрюша', 'дрюха', 'андрейчик'],
        
        # Антон
        'антон': ['антон', 'толя', 'тоха', 'антошка'],
        
        # Артем
        'артем': ['артем', 'артём', 'артур', 'артик', 'арт'],
        
        # Валентин
        'валентин': ['валентин', 'валя', 'валенок', 'влад'],
        
        # Виктор
        'виктор': ['виктор', 'вика', 'витёк', 'викторья'],
        
        # Владимир
        'владимир': ['владимир', 'владик', 'влад', 'вова', 'вован'],
        
        # Максим
        'максим': ['максим', 'макс', 'максимка'],
        
        # Мария
        'мария': ['мария', 'маша', 'машенька', 'мари', 'марья', 'мотя'],
        
        # Екатерина
        'екатерина': ['екатерина', 'катя', 'катюша', 'катерина', 'катёнок'],
        
        # Наталья
        'наталья': ['наталья', 'наташа', 'натка', 'натали'],
        
        # Елена
        'елена': ['елена', 'лена', 'лёна', 'алёна', 'элена'],
        
        # Ольга
        'ольга': ['ольга', 'оля', 'олечка', 'олёга'],
        
        # Полина
        'полина': ['полина', 'поля', 'палина'],
        
        # Кристина
        'кристина': ['кристина', 'кристина', 'кристинка', 'ксюша'],
        
        # Дарья
        'дарья': ['дарья', 'даша', 'дашка', 'дашуля', 'darya', 'dasha'],
        
        # Анастасия
        'анастасия': ['анастасия', 'настя', 'настенька', 'настяня', 'ася'],
        
        # Иван
        'иван': ['иван', 'ваня', 'ванюша', 'иванко', 'вован'],
        
        # Николай
        'николай': ['николай', 'коля', 'коленька', 'николай', 'кока'],
        
        # Константин
        'константин': ['константин', 'костя', 'константин', 'костян'],
        
        # Павел
        'павел': ['павел', 'паша', 'пашка', 'павлик'],
        
        # Сергей
        'сергей': ['сергей', 'серёжа', 'серёжка', 'серега'],
        
        # Юрий
        'юрий': ['юрий', 'юра', 'юрка'],
        
        # Ярослав
        'ярослав': ['ярослав', 'ярик', 'ярославчик'],
    }
    
    # Транслитерация (русский -> английский)
    CYRILLIC_TO_LATIN = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
        'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    
    # LATIN TO CYRILLIC (common transliterations)
    LATIN_TO_CYRILLIC = {
        'a': 'а', 'b': 'б', 'c': 'к', 'd': 'д', 'e': 'е', 'f': 'ф', 'g': 'г',
        'h': 'х', 'i': 'и', 'j': 'дж', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н',
        'o': 'о', 'p': 'п', 'q': 'к', 'r': 'р', 's': 'с', 't': 'т', 'u': 'у',
        'v': 'в', 'w': 'в', 'x': 'х', 'y': 'й', 'z': 'з'
    }
    
    def __init__(self):
        # Создаем обратный словарь вариаций
        self._build_reverse_variations()
    
    def _build_reverse_variations(self):
        """Создает обратный словарь для быстрого поиска канонической формы"""
        self.canonical_forms = {}
        for canonical, variations in self.NAME_VARIATIONS.items():
            for var in variations:
                self.canonical_forms[var] = canonical
            self.canonical_forms[canonical] = canonical
    
    def normalize_name(self, name) -> str:
        """
        Нормализует имя: приводит к строке, удаляет пробелы, регистр, пунктуацию.
        Поддерживает str и int (id → строка).
        """
        if name is None:
            return ""
        # Приводим к строке, если передан не str (например, int ID)
        if not isinstance(name, str):
            name = str(name)
        cleaned = name.strip().lower()
        # Удаляем пунктуацию и спецсимволы, сохраняем буквы (любые алфавиты) и цифры
        cleaned = re.sub(r'[^\w]', '', cleaned, flags=re.UNICODE)
        return cleaned.replace('_', '')
    
    def transliterate(self, text: str, to_cyrillic: bool = False) -> str:
        """Транслитерирует текст между кириллицей и латиницей"""
        if not text:
            return ""
        
        text = text.lower().strip()
        dictionary = self.LATIN_TO_CYRILLIC if to_cyrillic else self.CYRILLIC_TO_LATIN
        
        result = []
        i = 0
        while i < len(text):
            # Проверяем двухсимвольные комбинации
            if i < len(text) - 1:
                two_char = text[i:i+2]
                if two_char in dictionary:
                    result.append(dictionary[two_char])
                    i += 2
                    continue
            
            # Односимвольная замена
            if text[i] in dictionary:
                result.append(dictionary[text[i]])
            else:
                result.append(text[i])
            i += 1
        
        return ''.join(result)
    
    def soundex(self, name: str) -> str:
        """Алгоритм Soundex для фонетического сравнения"""
        if not name:
            return ""
        
        name = self.normalize_name(name)
        
        # Коды Soundex для русских букв
        soundex_codes = {
            'б': '1', 'в': '2', 'г': '3', 'д': '4',
            'ж': '5', 'з': '6', 'й': '7', 'к': '8', 'л': '9',
            'м': 'b', 'н': 'c', 'п': 'd', 'р': 'f', 'с': 'g', 'т': 'h',
            'ф': 'j', 'х': 'k', 'ц': 'l', 'ч': 'm', 'ш': 'n', 'щ': 'p',
            'а': 'a', 'е': 'a', 'ё': 'a', 'и': 'a', 'о': 'a', 'у': 'a',
            'ы': 'a', 'э': 'a', 'ю': 'a', 'я': 'a', 'ь': '', 'ъ': ''
        }
        
        if name[0] in 'аеёиоуыэюя':
            first_char = 'a'
        else:
            first_char = name[0]
        
        coded = first_char
        prev_code = ''
        
        for char in name[1:]:
            code = soundex_codes.get(char, '')
            if code and code != prev_code:
                coded += code
                if len(coded) == 4:
                    break
                prev_code = code
        
        return (coded + '000')[:4]
    
    def metaphone(self, name: str) -> str:
        """Упрощенный алгоритм Metaphone для русских имен"""
        if not name:
            return ""
        
        name = self.normalize_name(name)
        
        # Основные замены для русских звуков
        replacements = {
            'ё': 'е', 'й': 'и', 'ь': '', 'ъ': '',
            'ж': 'ж', 'ш': 'ш', 'ч': 'ч', 'щ': 'щ',
            'ц': 'ц', 'ю': 'ю', 'я': 'я',
            'а': 'а', 'е': 'е', 'и': 'и', 'о': 'о', 'у': 'у', 'ы': 'ы', 'э': 'э'
        }
        
        result = []
        for char in name:
            if char in replacements:
                result.append(replacements[char])
            elif char in 'бвгдзклмнпрстфх':
                result.append(char)
        
        # Удаляем повторяющиеся согласные
        filtered = []
        prev = ''
        for char in result:
            if char != prev or char in 'аеиоуэы':
                filtered.append(char)
            prev = char
        
        return ''.join(filtered)[:6] if filtered else ''
    
    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """Вычисляет расстояние Левенштейна между строками"""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def jaccard_similarity(self, s1: str, s2: str, tokenize: bool = True) -> float:
        """
        Вычисляет коэффициент Жаккара (Jaccard index) между двумя строками
        
        Args:
            s1: Первая строка
            s2: Вторая строка
            tokenize: Если True - разбивает на токены (символы), иначе использует множества символов
            
        Returns:
            Коэффициент Жаккара (0-1), где 1 = полное совпадение, 0 = нет общих элементов
        """
        if not s1 or not s2:
            return 0.0
        
        if tokenize:
            # Разбиваем на токены - используем слова (после нормализации)
            # Для имен подходит разбиение по символам или по n-граммам
            # Здесь используем set от символов ( character-level Jaccard)
            set1 = set(s1)
            set2 = set(s2)
        else:
            # Используем целые строки как множества
            set1 = {s1}
            set2 = {s2}
        
        union = set1 | set2
        if not union:
            return 0.0
        
        intersection = set1 & set2
        return len(intersection) / len(union)
    
    def fuzzy_ratio(self, s1: str, s2: str) -> float:
        """Вычисляет коэффициент нечеткого сходства (0-1)"""
        if not s1 or not s2:
            return 0.0
        return SequenceMatcher(None, s1, s2).ratio()
    
    def get_nickname_variants(self, name: str) -> List[str]:
        """Генерирует список возможных никнеймов/сокращений имени"""
        if not name:
            return []
        
        name = self.normalize_name(name)
        variants = [name]
        
        # Проверяем, является ли имя вариацией
        if name in self.canonical_forms:
            canonical = self.canonical_forms[name]
            variants.extend([v for v in self.NAME_VARIATIONS.get(canonical, []) if v != name])
        
        # Добавляем транслитерации
        translit = self.transliterate(name)
        if translit != name:
            variants.append(translit)
            # Проверяем транслитерацию вариаций
            if name in self.canonical_forms:
                for v in self.NAME_VARIATIONS.get(self.canonical_forms[name], []):
                    variants.append(self.transliterate(v))
        
        # Добавляем популярные сокращения
        if len(name) > 3:
            variants.append(name[:4])  # Первые 4 буквы
            variants.append(name[:3] + 'к')  # Данил -> Даник
            variants.append(name[:3])  # Первые 3 буквы
        
        # Обработка числовых замен (Dan4ik, D4n, etc.)
        digit_variants = name
        digit_map = {'а': '4', 'е': '3', 'о': '0', 'у': 'y', 'и': '1', 'с': 'c'}
        for cyr, lat in digit_map.items():
            if cyr in digit_variants:
                digit_variants = digit_variants.replace(cyr, lat)
        if digit_variants != name:
            variants.append(digit_variants)
        
        return list(set(variants))
    
    def compare_names(self, name1: str, name2: str) -> Dict[str, any]:
        """
        Комплексное сравнение двух имен
        
        Returns:
            Dict с ключами:
            - exact_match: точное совпадение после нормализации
            - fuzzy_score: оценка нечеткого сходства (0-1)
            - phonetic_score: оценка фонетического сходства (0-1)
            - variation_match: совпадение через вариации имен
            - transliteration_match: совпадение через транслитерацию
            - final_score: итоговая оценка (0-1)
            - details: детальная информация
        """
        if not name1 or not name2:
            return {
                'exact_match': False,
                'fuzzy_score': 0.0,
                'phonetic_score': 0.0,
                'variation_match': False,
                'transliteration_match': False,
                'final_score': 0.0,
                'details': 'Одно из имен пустое'
            }
        
        n1 = self.normalize_name(name1)
        n2 = self.normalize_name(name2)
        
        details = {}
        
        # 1. Точное совпадение
        exact_match = n1 == n2
        details['exact_match'] = exact_match
        
        # 2. Нечеткое сопоставление
        fuzzy_score = self.fuzzy_ratio(n1, n2)
        details['fuzzy_score'] = fuzzy_score
        
        # 3. Фонетическое сравнение (Soundex)
        soundex1 = self.soundex(n1)
        soundex2 = self.soundex(n2)
        soundex_match = soundex1 == soundex2
        
        # 4. Фонетическое сравнение (Metaphone)
        metaphone1 = self.metaphone(n1)
        metaphone2 = self.metaphone(n2)
        metaphone_match = metaphone1 == metaphone2
        
        phonetic_score = (self.fuzzy_ratio(soundex1, soundex2) + 
                         self.fuzzy_ratio(metaphone1, metaphone2)) / 2
        details['phonetic_score'] = phonetic_score
        details['soundex'] = (soundex1, soundex2, soundex_match)
        details['metaphone'] = (metaphone1, metaphone2, metaphone_match)
        
        # 5. Проверка вариаций имен
        variants1 = set(self.get_nickname_variants(n1))
        variants2 = set(self.get_nickname_variants(n2))
        variation_match = bool(variants1 & variants2)
        details['variants1'] = list(variants1)[:10]
        details['variants2'] = list(variants2)[:10]
        details['common_variants'] = list(variants1 & variants2)
        
        # 6. Проверка через транслитерацию
        trans1_to_cyrillic = self.transliterate(n1, to_cyrillic=True)
        trans2_to_latin = self.transliterate(n2)
        
        translit_match = (
            trans1_to_cyrillic == n2 or 
            trans2_to_latin == n1 or
            self.transliterate(n1) == self.transliterate(n2)
        )
        details['transliteration_match'] = translit_match
        details['translit_n1'] = trans1_to_cyrillic
        details['translit_n2'] = trans2_to_latin
        
        # 7. Расстояние Левенштейна
        lev_dist = self.levenshtein_distance(n1, n2)
        max_len = max(len(n1), len(n2), 1)
        lev_score = 1 - (lev_dist / max_len)
        details['levenshtein_distance'] = lev_dist
        details['levenshtein_score'] = lev_score
        
        # 8. Jaccard similarity (на уровне символов)
        jaccard_score = self.jaccard_similarity(n1, n2, tokenize=True)
        details['jaccard_score'] = jaccard_score
        
        # Расчет итоговой оценки
        # Если точное совпадение — максимум
        if exact_match:
            final_score = 1.0
        else:
            # Собираем вклад всех метрик
            contributions = []
            
            # Качественные факторы (вариации, транслитерация) — высокий фиксированный балл
            if variation_match:
                contributions.append(0.85)
            if translit_match:
                contributions.append(0.8)
            
            # Нечеткое сходство (fuzzy) — основной фактор для похожих имен
            if fuzzy_score > 0.5:
                contributions.append(fuzzy_score * 0.7)
            
            # Фонетическое сходство
            if phonetic_score > 0.3:
                contributions.append(phonetic_score * 0.6)
            
            # Расстояние Левенштейна
            if lev_score > 0.5:
                contributions.append(lev_score * 0.6)
            
            # Jaccard similarity
            if jaccard_score > 0.4:
                contributions.append(jaccard_score * 0.65)
            
            # Итог — максимум из всех вкладов
            final_score = max(contributions) if contributions else 0.0
            final_score = min(final_score, 1.0)
        
        return {
            'exact_match': exact_match,
            'fuzzy_score': fuzzy_score,
            'phonetic_score': phonetic_score,
            'variation_match': variation_match,
            'transliteration_match': translit_match,
            'levenshtein_score': lev_score,
            'jaccard_score': jaccard_score,
            'final_score': final_score,
            'details': details,
            'interpretation': self._interpret_score(final_score)
        }
    
    def compare_full_names(self, first_name1: str, last_name1: str, 
                          first_name2: str, last_name2: str) -> Dict[str, any]:
        """Сравнивает полные имена (имя + фамилия)"""
        
        first_name_result = self.compare_names(first_name1, first_name2)
        last_name_result = self.compare_names(last_name1, last_name2)
        
        # Также проверяем перестановку (имя в фамилии и наоборот)
        cross_result = self.compare_names(first_name1, last_name2)
        
        # Объединяем результаты
        combined_score = (
            first_name_result['final_score'] * 0.5 +
            last_name_result['final_score'] * 0.4 +
            cross_result['final_score'] * 0.1
        )
        
        # Проверяем, является ли комбинация "сильной"
        strong_match = (
            first_name_result['exact_match'] and last_name_result['exact_match']
        ) or (
            first_name_result['variation_match'] and last_name_result['exact_match']
        ) or (
            first_name_result['exact_match'] and last_name_result['variation_match']
        )
        
        return {
            'first_name_comparison': first_name_result,
            'last_name_comparison': last_name_result,
            'cross_comparison': cross_result,
            'combined_score': combined_score,
            'strong_match': strong_match,
            'interpretation': self._interpret_score(combined_score)
        }
    
    def _interpret_score(self, score: float) -> str:
        """Интерпретирует оценку совпадения"""
        if score >= 0.95:
            return "Практически точно тот же человек"
        elif score >= 0.85:
            return "Очень вероятно тот же человек"
        elif score >= 0.70:
            return "Вероятно тот же человек"
        elif score >= 0.50:
            return "Возможно тот же человек"
        elif score >= 0.30:
            return "Сомнительное совпадение"
        else:
            return "Разные люди"


# Пример использования
if __name__ == "__main__":
    matcher = NameMatcher()
    
    # Тесты
    test_cases = [
        ("Даниил", "Данила"),
        ("Данил", "Danya"),
        ("Александр", "Саша"),
        ("Мария", "Маша"),
        ("Дмитрий", "Дима"),
        ("Екатерина", "Катя"),
        ("Анастасия", "Настя"),
        ("Владимир", "Вова"),
    ]
    
    print("="*60)
    print("ТЕСТ СРАВНЕНИЯ ИМЕН")
    print("="*60)
    
    for n1, n2 in test_cases:
        result = matcher.compare_names(n1, n2)
        print(f"\n{n1} vs {n2}:")
        print(f"  Точное совпадение: {result['exact_match']}")
        print(f"  Нечеткое сходство: {result['fuzzy_score']:.2f}")
        print(f"  Фонетическое сходство: {result['phonetic_score']:.2f}")
        print(f"  Совпадение вариаций: {result['variation_match']}")
        print(f"  Транслитерация: {result['transliteration_match']}")
        print(f"  ИТОГ: {result['final_score']:.2f} - {matcher._interpret_score(result['final_score'])}")
