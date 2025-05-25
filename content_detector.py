import re
from formatting_constants import FormattingConstants

class ContentDetector:
    """Определяет типы контента в документе"""
    
    @staticmethod
    def is_title_page_content(text: str) -> bool:
        """Определяет содержимое титульного листа"""
        text_upper = text.upper()
        
        # Проверка маркеров титульной страницы
        for marker in FormattingConstants.TITLE_PAGE_MARKERS:
            if marker in text_upper:
                return True
        
        # Паттерны для ФИО
        fio_patterns = [
            r"[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.[А-ЯЁ]\.",  # Иванов И.И.
            r"[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+",  # Иванов Иван Иванович
        ]
        
        for pattern in fio_patterns:
            if re.search(pattern, text):
                return True
        
        # Короткие строки с высоким процентом заглавных букв
        if len(text) < 200:
            alpha_chars = [c for c in text if c.isalpha()]
            if alpha_chars:
                upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
                if upper_ratio > 0.8 and len(text.split()) <= 5:
                    return True
        
        return False
    
    @staticmethod
    def is_contents_header(text: str) -> bool:
        """Определяет заголовок страницы содержания"""
        text_upper = text.upper().strip()
        return text_upper in FormattingConstants.CONTENT_HEADERS
    
    @staticmethod
    def is_contents_line(text: str) -> bool:
        """Определяет строку содержания с номерами страниц"""
        text_clean = text.strip()
        
        if not text_clean:
            return False
        
        # Паттерны для строк содержания
        content_patterns = [
            # С точками и номерами страниц
            r".+\.{3,}.+\d+$",  # "Введение...........3"
            r".+\.{2,}\s*\d+$",  # "1. Обзор литературы..5" 
            r"^[А-ЯЁ\d\.\s]+\.{3,}\d+$",  # "ГЛАВА 1...10"
            r"^\d+[\.\s][А-ЯЁа-яё\s]+\.{3,}\d+$",  # "1 Введение.....4"
            r"^\d+\.\d+[\.\s][А-ЯЁа-яё\s]+\.{3,}\d+$",  # "1.1 Подраздел.....8"
            
            # С пробелами и номерами страниц (без точек)
            r"^[А-ЯЁа-яё\s]+\s+\d+$",  # "Введение    8"
            r"^\d+\.\s*[А-ЯЁа-яё\s]+\s+\d+$",  # "1. Анализ предметной области   11"
            r"^\d+\s+[А-ЯЁа-яё\s]+\s+\d+$",  # "1 Введение   4"
            r"^\d+\.\d+\s+[А-ЯЁа-яё\s]+\s+\d+$",  # "1.1 Недостатки   11"
            
            # Специальные случаи
            r"^[А-ЯЁа-яё\s,]+\d+$",  # "Определения, обозначения и сокращения5"
        ]
        
        for pattern in content_patterns:
            if re.search(pattern, text_clean):
                return True
        
        # Дополнительная эвристика: строка заканчивается числом и содержит мало слов
        if re.search(r'\d+$', text_clean):
            words = text_clean.split()
            if 2 <= len(words) <= 8:
                try:
                    int(words[-1])
                    return True
                except ValueError:
                    pass
        
        return False
    
    @staticmethod
    def is_service_content(text: str) -> bool:
        """Определяет служебные разделы"""
        text_upper = text.upper()
        
        for marker in FormattingConstants.SERVICE_MARKERS:
            if marker in text_upper:
                return True
        
        return False
    
    @staticmethod
    def is_main_content_start(text: str) -> bool:
        """Определяет начало основного содержания"""
        text_upper = text.upper().strip()
        
        # Исключаем строки содержания
        if ContentDetector.is_contents_line(text):
            return False
        
        # Точные совпадения с маркерами
        for marker in FormattingConstants.MAIN_CONTENT_MARKERS:
            if text_upper == marker:
                return True
        
        # Паттерны для глав (без номеров страниц в конце)
        chapter_patterns = [
            r"^ГЛАВА\s+\d+$",  # "ГЛАВА 1"
            r"^\d+\.\s*[А-ЯЁ][А-ЯЁа-яё\s]*$",  # "1. ВВЕДЕНИЕ"
            r"^\d+\s+[А-ЯЁ][А-ЯЁа-яё\s]*$",    # "1 ВВЕДЕНИЕ"
        ]
        
        for pattern in chapter_patterns:
            if re.match(pattern, text_upper):
                if not re.search(r'\s+\d+$', text.strip()):
                    return True
        
        return False 