# content_matcher.py
# Модуль анализа контента и стиля написания

import re
from typing import Dict, List, Tuple, Optional, Set
from collections import Counter
from difflib import SequenceMatcher

class ContentMatcher:
    """
    Класс для анализа контента профиля и стиля написания
    
    Функции:
    - Анализ текстов публикаций
    - Анализ стиля написания (характерные обороты, эмодзи)
    - Тематический анализ постов
    - Временные паттерны активности
    - Сравнение контента двух профилей
    """
    
    # Характерные слова-маркеры для разных типов личностей
    PERSONAL_MARKERS = {
        'formal': ['уважаемый', 'господа', 'коллеги', 'согласно', 'вследствие', 'для ознакомления'],
        'informal': ['привет', 'здорово', 'классно', 'круто', 'супер', 'класс', 'шикарно'],
        'humor': ['хех', 'хах', 'лол', 'ржунимагу', 'ахах', 'посмеялся'],
        'emotional': ['очень', 'невероятно', 'потрясающе', 'не могу', 'с ума сойти', 'шок'],
        'analytical': ['во-первых', 'во-вторых', 'следовательно', 'таким образом', 'однако', 'тем не менее'],
        'creative': ['вдохновение', 'мечта', 'творчество', 'искусство', 'красота', 'прекрасный'],
    }
    
    # Часто используемые эмодзи и их категории
    EMOJI_CATEGORIES = {
        'positive': ['😀', '😊', '😍', '🥰', '❤️', '😘', '👍', '🎉', '🎊', '✨', '🌟', '💕', '🤗', '😁'],
        'negative': ['😢', '😭', '💔', '😞', '😔', '😠', '😡', '👎', '💔'],
        'neutral': ['😐', '😑', '🙄', '😏', '🤔', '😴', '💤'],
        'activity': ['🏃', '🚶', '🚗', '✈️', '🎬', '🎮', '📚', '💻', '🎵', '🎤'],
        'objects': ['📱', '💻', '📷', '🎥', '🎤', '🎧', '☕', '🍕', '🍺', '🎁'],
    }
    
    def __init__(self):
        self._build_emoji_pattern()
    
    def _build_emoji_pattern(self):
        """Создает паттерн для поиска эмодзи"""
        all_emoji = []
        for emojis in self.EMOJI_CATEGORIES.values():
            all_emoji.extend(emojis)
        
        # Эмодзи unicode ranges
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+"
        )
    
    def extract_text_features(self, text: str) -> Dict[str, any]:
        """
        Извлекает характеристики текста
        
        Returns:
            Dict с характеристиками текста
        """
        
        if not text:
            return {
                'word_count': 0,
                'char_count': 0,
                'avg_word_length': 0,
                'uppercase_ratio': 0,
                'punctuation_ratio': 0,
                'emoji_count': 0,
                'emoji_types': [],
                'sentence_count': 0,
                'avg_sentence_length': 0,
            }
        
        # Приводим к строке, если передан не строковый тип (например, int)
        if not isinstance(text, str):
            text = str(text)
        
        # Базовая статистика
        words = text.split()
        word_count = len(words)
        char_count = len(text)
        
        # Средняя длина слова
        avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0
        
        # Соотношение заглавных букв
        uppercase_count = sum(1 for c in text if c.isupper())
        uppercase_ratio = uppercase_count / char_count if char_count > 0 else 0
        
        # Соотношение знаков препинания
        punctuation_count = sum(1 for c in text if c in '.,!?;:')
        punctuation_ratio = punctuation_count / char_count if char_count > 0 else 0
        
        # Эмодзи
        emojis = self.emoji_pattern.findall(text)
        emoji_count = len(''.join(emojis))
        emoji_types = list(set(emojis)) if emojis else []
        
        # Периоды (предложения)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Персональные маркеры
        text_lower = text.lower()
        marker_scores = {}
        for category, markers in self.PERSONAL_MARKERS.items():
            score = sum(1 for m in markers if m in text_lower)
            marker_scores[category] = score
        
        return {
            'word_count': word_count,
            'char_count': char_count,
            'avg_word_length': avg_word_length,
            'uppercase_ratio': uppercase_ratio,
            'punctuation_ratio': punctuation_ratio,
            'emoji_count': emoji_count,
            'emoji_types': emoji_types,
            'sentence_count': sentence_count,
            'avg_sentence_length': avg_sentence_length,
            'personal_markers': marker_scores,
        }
    
    def analyze_writing_style(self, texts: List[str]) -> Dict[str, any]:
        """
        Анализирует стиль написания на основе нескольких текстов
        
        Args:
            texts: Список текстов/постов пользователя
        """
        
        if not texts:
            return {
                'style_summary': 'Нет данных',
                'complexity': 0,
                'formality': 0,
                'expressiveness': 0,
            }
        
        # Агрегируем характеристики
        total_features = {
            'word_count': 0,
            'char_count': 0,
            'avg_word_length': [],
            'uppercase_ratio': [],
            'punctuation_ratio': [],
            'emoji_count': 0,
            'emoji_types': Counter(),
            'sentence_count': 0,
            'avg_sentence_length': [],
            'personal_markers': Counter(),
        }
        
        for text in texts:
            features = self.extract_text_features(text)
            total_features['word_count'] += features['word_count']
            total_features['char_count'] += features['char_count']
            total_features['avg_word_length'].append(features['avg_word_length'])
            total_features['uppercase_ratio'].append(features['uppercase_ratio'])
            total_features['punctuation_ratio'].append(features['punctuation_ratio'])
            total_features['emoji_count'] += features['emoji_count']
            total_features['emoji_types'].update(features['emoji_types'])
            total_features['sentence_count'] += features['sentence_count']
            total_features['avg_sentence_length'].append(features['avg_sentence_length'])
            
            for category, score in features['personal_markers'].items():
                total_features['personal_markers'][category] += score
        
        # Средние значения
        n = len(texts)
        avg_word_length = sum(total_features['avg_word_length']) / n
        avg_uppercase = sum(total_features['uppercase_ratio']) / n
        avg_punctuation = sum(total_features['punctuation_ratio']) / n
        avg_sentence_length = sum(total_features['avg_sentence_length']) / n
        
        # Оценка формальности
        formality = 0.0
        if total_features['personal_markers']['formal'] > 0:
            formality += 0.3
        if avg_punctuation > 0.1:
            formality += 0.2
        if avg_sentence_length > 15:
            formality += 0.2
        if avg_uppercase < 0.05:
            formality += 0.2
        
        # Оценка экспрессивности
        expressiveness = 0.0
        if total_features['emoji_count'] > 0:
            expressiveness += 0.4
        if total_features['personal_markers']['emotional'] > 0:
            expressiveness += 0.3
        if total_features['personal_markers']['humor'] > 0:
            expressiveness += 0.3
        
        # Сложность текста
        complexity = min(1.0, avg_word_length / 7)
        
        return {
            'total_posts': n,
            'total_words': total_features['word_count'],
            'total_chars': total_features['char_count'],
            'avg_word_length': avg_word_length,
            'avg_sentence_length': avg_sentence_length,
            'uppercase_ratio': avg_uppercase,
            'punctuation_ratio': avg_punctuation,
            'emoji_count': total_features['emoji_count'],
            'top_emojis': total_features['emoji_types'].most_common(10),
            'personal_markers': dict(total_features['personal_markers']),
            'complexity': complexity,
            'formality': min(1.0, formality),
            'expressiveness': min(1.0, expressiveness),
        }
    
    def compare_content(self, content1: Dict, content2: Dict) -> Dict[str, any]:
        """
        Сравнивает контент двух профилей
        
        Args:
            content1: Данные контента первого профиля {posts: [], status: '', about: ''}
            content2: Данные контента второго профиля
        """
        
        # Извлекаем тексты
        texts1 = []
        texts2 = []
        
        if 'posts' in content1:
            texts1.extend([p.get('text', '') for p in content1['posts'] if p.get('text')])
        if 'status' in content1 and content1['status']:
            texts1.append(content1['status'])
        if 'about' in content1 and content1['about']:
            texts1.append(content1['about'])
        
        if 'posts' in content2:
            texts2.extend([p.get('text', '') for p in content2['posts'] if p.get('text')])
        if 'status' in content2 and content2['status']:
            texts2.append(content2['status'])
        if 'about' in content2 and content2['about']:
            texts2.append(content2['about'])
        
        # Анализируем стиль
        style1 = self.analyze_writing_style(texts1)
        style2 = self.analyze_writing_style(texts2)
        
        # Сравниваем метрики
        scores = {}
        
        # Сложность
        if style1['complexity'] > 0 and style2['complexity'] > 0:
            complexity_diff = abs(style1['complexity'] - style2['complexity'])
            scores['complexity'] = 1 - complexity_diff
        
        # Формальность
        if style1['formality'] > 0 or style2['formality'] > 0:
            formality_diff = abs(style1['formality'] - style2['formality'])
            scores['formality'] = 1 - formality_diff
        
        # Экспрессивность
        if style1['expressiveness'] > 0 or style2['expressiveness'] > 0:
            express_diff = abs(style1['expressiveness'] - style2['expressiveness'])
            scores['expressiveness'] = 1 - express_diff
        
        # Эмодзи
        emojis1 = set(e for e, _ in style1['top_emojis'])
        emojis2 = set(e for e, _ in style2['top_emojis'])
        emoji_overlap = len(emojis1 & emojis2) / max(len(emojis1 | emojis2), 1)
        scores['emoji_style'] = emoji_overlap
        
        # Средняя оценка
        avg_score = sum(scores.values()) / len(scores) if scores else 0
        
        return {
            'style1': style1,
            'style2': style2,
            'metric_scores': scores,
            'overall_content_score': avg_score,
            'interpretation': self._interpret_content_score(avg_score)
        }
    
    def _interpret_content_score(self, score: float) -> str:
        """Интерпретирует оценку контента"""
        if score >= 0.8:
            return "Очень похожий стиль написания"
        elif score >= 0.6:
            return "Похожий стиль написания"
        elif score >= 0.4:
            return "Частично похожий стиль"
        elif score >= 0.2:
            return "Разный стиль написания"
        else:
            return "Совершенно разный контент"
    
    def extract_interests(self, profile_data: Dict) -> Set[str]:
        """Извлекает интересы из данных профиля"""
        
        interest_fields = ['activities', 'interests', 'music', 'movies', 'books', 'games', 'quotes']
        interests = set()
        
        for field in interest_fields:
            if field in profile_data and profile_data[field]:
                value = profile_data[field]
                if not isinstance(value, str):
                    value = str(value)
                # Разбиваем на отдельные интересы
                items = re.split(r'[,;]', value.lower())
                for item in items:
                    cleaned = item.strip()
                    if len(cleaned) > 2:
                        interests.add(cleaned)
        
        return interests
    
    def compare_interests(self, profile1: Dict, profile2: Dict) -> Dict[str, any]:
        """Сравнивает интересы двух профилей"""
        
        interests1 = self.extract_interests(profile1)
        interests2 = self.extract_interests(profile2)
        
        if not interests1 or not interests2:
            return {
                'common_interests': [],
                'interest_overlap': 0.0,
                'score': 0.0
            }
        
        common = interests1 & interests2
        union = interests1 | interests2
        
        overlap = len(common) / len(union) if union else 0
        
        return {
            'common_interests': list(common),
            'interests_1_count': len(interests1),
            'interests_2_count': len(interests2),
            'interest_overlap': overlap,
            'score': overlap
        }
    
    def analyze_activity_patterns(self, posts: List[Dict]) -> Dict[str, any]:
        """
        Анализирует временные паттерны активности
        
        Args:
            posts: Список постов с датами
        """
        
        if not posts:
            return {
                'total_posts': 0,
                'avg_posts_per_day': 0,
                'most_active_hours': [],
                'most_active_days': [],
            }
        
        # Подсчет постов по часам
        hour_counts = Counter()
        day_counts = Counter()
        
        for post in posts:
            # Предполагаем, что есть timestamp
            timestamp = post.get('date', 0)
            if timestamp:
                from datetime import datetime
                dt = datetime.fromtimestamp(timestamp)
                hour_counts[dt.hour] += 1
                day_counts[dt.strftime('%A')] += 1
        
        return {
            'total_posts': len(posts),
            'most_active_hours': hour_counts.most_common(5),
            'most_active_days': day_counts.most_common(3),
        }


# Пример использования
if __name__ == "__main__":
    matcher = ContentMatcher()
    
    # Тест анализа стиля
    texts1 = [
        "Привет всем! Как дела? 😊",
        "Сегодня отличный день, всё классно! ✨",
        "Работаю над новым проектом, очень интересно...",
    ]
    
    texts2 = [
        "Привет! Как жизнь? 😄",
        "Классный день сегодня! 🌟",
        "Новый проект - это супер интересно!",
    ]
    
    content1 = {'posts': [{'text': t} for t in texts1], 'status': 'test', 'about': ''}
    content2 = {'posts': [{'text': t} for t in texts2], 'status': 'test', 'about': ''}
    
    print("="*60)
    print("ТЕСТ АНАЛИЗА КОНТЕНТА")
    print("="*60)
    
    result = matcher.compare_content(content1, content2)
    print(f"\nОценка контента: {result['overall_content_score']:.3f}")
    print(f"Интерпретация: {result['interpretation']}")
    print(f"\nМетрики:")
    for metric, score in result['metric_scores'].items():
        print(f"  {metric}: {score:.3f}")
