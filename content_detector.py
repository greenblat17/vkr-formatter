import re
from formatting_constants import FormattingConstants


class ContentDetector:
    """Определяет типы контента в документе"""

    @staticmethod
    def is_title_page_content(text: str) -> bool:
        """Определяет содержимое титульного листа"""
        text_upper = text.upper()

        # ВАЖНО: Исключаем список литературы из титульной страницы
        references_keywords = [
            "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
            "СПИСОК ЛИТЕРАТУРЫ", 
            "БИБЛИОГРАФИЧЕСКИЙ СПИСОК",
            "REFERENCES",
            "BIBLIOGRAPHY"
        ]
        
        for keyword in references_keywords:
            if keyword in text_upper:
                return False  # Это список литературы, не титульная страница

        # ВАЖНО: Сначала проверяем, не является ли это H1 заголовком
        # Если это H1, то НЕ считаем титульной страницей
        h1_patterns = [
            r"^\d+\.\s*[А-ЯЁ\s]+$",           # "1. ВВЕДЕНИЕ"
            r"^ГЛАВА\s+\d+",                   # "ГЛАВА 1"
            r"^(ВВЕДЕНИЕ|ЗАКЛЮЧЕНИЕ|РЕФЕРАТ)$", # специальные разделы
            r"^[IVX]+\.\s*[А-ЯЁ\s]+$"        # "I. ВВЕДЕНИЕ"
        ]
        
        for pattern in h1_patterns:
            if re.match(pattern, text_upper.strip()):
                return False  # Это H1 заголовок, не титульная страница

        # Проверка маркеров титульной страницы
        for marker in FormattingConstants.TITLE_PAGE_MARKERS:
            if marker in text_upper:
                return True

        # Паттерны для ФИО
        fio_patterns = [
            r"[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.[А-ЯЁ]\.",  # Иванов И.И.
            # Иванов Иван Иванович
            r"[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+",
        ]

        for pattern in fio_patterns:
            if re.search(pattern, text):
                return True

        # Короткие строки с высоким процентом заглавных букв
        # НО исключаем потенциальные заголовки и заглушки изображений
        if len(text) < 200:
            # Исключаем заглушки изображений
            image_placeholders = [
                '[ЗДЕСЬ ДОЛЖНО БЫТЬ ИЗОБРАЖЕНИЕ]',
                '[ВТОРОЕ ИЗОБРАЖЕНИЕ]',
                '[ИЗОБРАЖЕНИЕ]',
                '[IMAGE]',
                '[РИСУНОК]',
                '[FIGURE]',
                '[РЕАЛЬНОЕ ИЗОБРАЖЕНИЕ АРХИТЕКТУРЫ]',
                '[ИЗОБРАЖЕНИЕ В РАЗДЕЛЕ 2]',
                '[ИЗОБРАЖЕНИЕ 1]',
                '[ИЗОБРАЖЕНИЕ 2]',
                '[ИЗОБРАЖЕНИЕ 3]',
                '[ИЗОБРАЖЕНИЕ В ПЕРВОЙ ГЛАВЕ]',
                '[ИЗОБРАЖЕНИЕ ВО ВТОРОЙ ГЛАВЕ]'
            ]
            
            for placeholder in image_placeholders:
                if placeholder in text_upper:
                    return False  # Это заглушка изображения, не титульная страница
            
            alpha_chars = [c for c in text if c.isalpha()]
            if alpha_chars:
                upper_ratio = sum(
                    1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
                if upper_ratio > 0.8 and len(text.split()) <= 5:
                    # Дополнительная проверка: не начинается ли с номера главы
                    if not re.match(r'^\d+\.', text.strip()):
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
            # "1. Анализ предметной области   11"
            r"^\d+\.\s*[А-ЯЁа-яё\s]+\s+\d+$",
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

        # ВАЖНО: Исключаем список литературы из служебных разделов
        references_keywords = [
            "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
            "СПИСОК ЛИТЕРАТУРЫ", 
            "БИБЛИОГРАФИЧЕСКИЙ СПИСОК",
            "REFERENCES",
            "BIBLIOGRAPHY"
        ]
        
        for keyword in references_keywords:
            if keyword in text_upper:
                return False  # Это список литературы, не служебный раздел

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
