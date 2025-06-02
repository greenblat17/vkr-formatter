"""
Классификатор параграфов на основе стилей документа
"""

from typing import Dict, Any
from content_detector import ContentDetector
from document_state import DocumentState, logger


class StyleBasedClassifier:
    """Классифицирует параграфы на основе стилей документа"""

    def __init__(self, requirements: Dict[str, Any], strict_style_mode: bool = False):
        self.requirements = requirements
        self.detector = ContentDetector()
        self.state = DocumentState()
        self.strict_style_mode = strict_style_mode  # Если True, игнорирует паттерны для Normal стиля

    def classify_paragraph_by_style(self, paragraph, text: str) -> str:
        """
        Классифицирует параграф на основе его стиля

        Args:
            paragraph: объект параграфа из python-docx
            text: текст параграфа

        Returns:
            str: "skip", "h1", "h2", "list", "regular"
        """
        if not text:
            return "skip"

        text_clean = text.strip()

        # 1. Проверяем заголовок содержания
        if self.detector.is_contents_header(text_clean):
            logger.info(f"📑 НАЧАЛО СОДЕРЖАНИЯ: {text_clean[:50]}...")
            self.state.start_contents_section()
            return "skip"

        # 2. Если в содержании
        if self.state.in_contents_section:
            return self._classify_in_contents_section(text_clean)

        # 3. Проверяем служебные разделы
        if (self.detector.is_title_page_content(text_clean) or
                self.detector.is_service_content(text_clean)):
            logger.debug(f"🔴 СЛУЖЕБНЫЙ РАЗДЕЛ: {text_clean[:50]}...")
            return "skip"

        # 4. Проверяем начало основного содержания
        if (not self.state.found_main_content and
                self.detector.is_main_content_start(text_clean)):
            logger.info(f"🟢 НАЧАЛО ОСНОВНОГО СОДЕРЖАНИЯ: {text_clean[:60]}...")
            self.state.start_main_content()
            return self._classify_content_paragraph_by_style(paragraph, text_clean)

        # 5. Если в титульной секции
        if self.state.in_title_section:
            logger.debug(f"⚪ ПРОПУСК (титульная): {text_clean[:50]}...")
            return "skip"

        # 6. Классифицируем как обычное содержание
        return self._classify_content_paragraph_by_style(paragraph, text_clean)

    def _classify_in_contents_section(self, text_clean: str) -> str:
        """Классифицирует параграфы в разделе содержания"""
        # Если это строка содержания - пропускаем
        if self.detector.is_contents_line(text_clean):
            logger.debug(f"📑 СОДЕРЖАНИЕ (строка): {text_clean[:50]}...")
            return "skip"

        # Если начинается основное содержание
        if self.detector.is_main_content_start(text_clean):
            logger.info(
                f"🟢 КОНЕЦ СОДЕРЖАНИЯ, НАЧАЛО ОСНОВНОГО СОДЕРЖАНИЯ: {text_clean[:60]}...")
            self.state.start_main_content()
            # Здесь нужен объект параграфа, но у нас его нет в этом контексте
            # Поэтому используем fallback на текстовые паттерны
            return self._classify_by_text_patterns(text_clean)
        else:
            # Пустая строка или неопределенное в содержании
            logger.debug(f"📑 СОДЕРЖАНИЕ (прочее): {text_clean[:50]}...")
            return "skip"

    def _classify_content_paragraph_by_style(self, paragraph, text_clean: str) -> str:
        """Классифицирует параграфы основного содержания по стилю"""
        logger.debug(f"🎨 Классифицируем по стилю: '{text_clean[:50]}...'")
        
        # Получаем стиль параграфа
        style_name = self._get_paragraph_style_name(paragraph)
        logger.debug(f"   📝 Стиль параграфа: '{style_name}'")
        
        # Проверяем изображения (параграфы с встроенными объектами)
        if self._contains_image(paragraph):
            logger.debug(f"   ↳ Определен как изображение рисунка")
            return "figure_image"
        
        # Проверяем таблицы и рисунки
        content_type = self._classify_content_elements(text_clean)
        if content_type != "regular":
            logger.debug(f"   ↳ Определен как элемент контента: {content_type}")
            return content_type
        
        # Классифицируем по стилю (приоритет стилям!)
        if self._is_h1_style(style_name):
            # Для H1 стилей проверяем, не является ли это специальным разделом
            # НО только если это НЕ нумерованная глава
            if self._is_numbered_chapter(text_clean):
                logger.debug(f"   ↳ Определен как H1 (нумерованная глава)")
                return "h1"
            elif self._is_special_h1_section(text_clean):
                logger.debug(f"   ↳ H1 стиль, но это специальный раздел")
                return self._classify_special_sections(text_clean)
            else:
                logger.debug(f"   ↳ Определен как H1 по стилю")
                return "h1"
        elif self._is_h2_style(style_name):
            logger.debug(f"   ↳ Определен как H2 по стилю")
            return "h2"
        elif self._is_h3_style(style_name):
            logger.debug(f"   ↳ Определен как H3 по стилю")
            return "h3"
        elif self._is_h4_style(style_name):
            logger.debug(f"   ↳ Определен как H4 по стилю")
            return "h4"
        elif self._is_list_style(style_name):
            logger.debug(f"   ↳ Определен как список по стилю")
            return "list"
        elif style_name == "Normal":
            if self.strict_style_mode:
                # В строгом режиме стиль Normal всегда считается обычным текстом
                logger.debug(f"   🔒 Строгий режим: стиль Normal = обычный текст")
                return "regular"
            else:
                # Для стиля Normal используем fallback на текстовые паттерны
                logger.debug(f"   🔄 Стиль Normal: проверяем по текстовым паттернам")
                return self._classify_by_text_patterns(text_clean)
        else:
            # Для других стилей (не заголовочных) проверяем специальные разделы
            special_type = self._classify_special_sections(text_clean)
            if special_type != "regular":
                logger.debug(f"   ↳ Определен как специальный раздел: {special_type}")
                return special_type
            else:
                logger.debug(f"   ↳ Неизвестный стиль '{style_name}', считаем обычным текстом")
                return "regular"

    def _get_paragraph_style_name(self, paragraph) -> str:
        """Получает название стиля параграфа"""
        try:
            if paragraph.style and paragraph.style.name:
                return paragraph.style.name
            else:
                return "Normal"
        except Exception as e:
            logger.debug(f"   ⚠️  Ошибка получения стиля: {e}")
            return "Normal"

    def _is_h1_style(self, style_name: str) -> bool:
        """Проверяет, является ли стиль заголовком 1 уровня"""
        h1_styles = [
            "Heading 1",
            "Заголовок 1", 
            "Title",
            "Название",
            "Header 1",
            "H1"
        ]
        
        # Точное совпадение
        if style_name in h1_styles:
            logger.debug(f"      ✅ Точное совпадение H1 стиля: {style_name}")
            return True
        
        # Частичное совпадение (нечувствительно к регистру)
        style_lower = style_name.lower()
        for h1_style in h1_styles:
            if h1_style.lower() in style_lower:
                logger.debug(f"      ✅ Частичное совпадение H1 стиля: {style_name} содержит {h1_style}")
                return True
        
        logger.debug(f"      ❌ Не является H1 стилем: {style_name}")
        return False

    def _is_h2_style(self, style_name: str) -> bool:
        """Проверяет, является ли стиль заголовком 2 уровня"""
        h2_styles = [
            "Heading 2",
            "Заголовок 2",
            "Subtitle", 
            "Подзаголовок",
            "Header 2",
            "H2",
            "Heading2",
            "Заголовок2",
            "Sub Heading",
            "Подраздел",
            "Section Heading"
        ]
        
        # Точное совпадение
        if style_name in h2_styles:
            logger.debug(f"      ✅ Точное совпадение H2 стиля: {style_name}")
            return True
        
        # Частичное совпадение (нечувствительно к регистру)
        style_lower = style_name.lower()
        for h2_style in h2_styles:
            if h2_style.lower() in style_lower:
                logger.debug(f"      ✅ Частичное совпадение H2 стиля: {style_name} содержит {h2_style}")
                return True
        
        logger.debug(f"      ❌ Не является H2 стилем: {style_name}")
        return False

    def _is_h3_style(self, style_name: str) -> bool:
        """Проверяет, является ли стиль заголовком 3 уровня"""
        h3_styles = [
            "Heading 3",
            "Заголовок 3",
            "Heading3",
            "Заголовок3",
            "Header 3",
            "H3",
            "Sub Sub Heading",
            "Подподраздел",
            "Subsection Heading"
        ]
        
        # Точное совпадение
        if style_name in h3_styles:
            logger.debug(f"      ✅ Точное совпадение H3 стиля: {style_name}")
            return True
        
        # Частичное совпадение (нечувствительно к регистру)
        style_lower = style_name.lower()
        for h3_style in h3_styles:
            if h3_style.lower() in style_lower:
                logger.debug(f"      ✅ Частичное совпадение H3 стиля: {style_name} содержит {h3_style}")
                return True
        
        logger.debug(f"      ❌ Не является H3 стилем: {style_name}")
        return False

    def _is_h4_style(self, style_name: str) -> bool:
        """Проверяет, является ли стиль заголовком 4 уровня"""
        h4_styles = [
            "Heading 4",
            "Заголовок 4",
            "Heading4",
            "Заголовок4",
            "Header 4",
            "H4",
            "Paragraph Heading",
            "Пункт",
            "Point Heading"
        ]
        
        # Точное совпадение
        if style_name in h4_styles:
            logger.debug(f"      ✅ Точное совпадение H4 стиля: {style_name}")
            return True
        
        # Частичное совпадение (нечувствительно к регистру)
        style_lower = style_name.lower()
        for h4_style in h4_styles:
            if h4_style.lower() in style_lower:
                logger.debug(f"      ✅ Частичное совпадение H4 стиля: {style_name} содержит {h4_style}")
                return True
        
        logger.debug(f"      ❌ Не является H4 стилем: {style_name}")
        return False

    def _is_list_style(self, style_name: str) -> bool:
        """Проверяет, является ли стиль списком"""
        list_styles = [
            "List Paragraph",
            "Список",
            "Bullet",
            "Numbered",
            "Маркированный список",
            "Нумерованный список"
        ]
        
        # Точное совпадение
        if style_name in list_styles:
            return True
        
        # Частичное совпадение
        style_lower = style_name.lower()
        for list_style in list_styles:
            if list_style.lower() in style_lower:
                return True
        
        return False

    def _classify_by_text_patterns(self, text_clean: str) -> str:
        """Fallback: классификация по текстовым паттернам"""
        logger.debug(f"   🔍 Fallback: анализ текстовых паттернов")
        
        # Используем старые паттерны как fallback
        if self._is_h1_by_pattern(text_clean):
            logger.debug(f"   ↳ Определен как H1 по паттерну")
            return "h1"
        elif self._is_h2_by_pattern(text_clean):
            logger.debug(f"   ↳ Определен как H2 по паттерну")
            return "h2"
        elif self._is_h3_by_pattern(text_clean):
            logger.debug(f"   ↳ Определен как H3 по паттерну")
            return "h3"
        elif self._is_h4_by_pattern(text_clean):
            logger.debug(f"   ↳ Определен как H4 по паттерну")
            return "h4"
        elif self._is_list_by_pattern(text_clean):
            logger.debug(f"   ↳ Определен как список по паттерну")
            return "list"
        else:
            logger.debug(f"   ↳ Определен как обычный параграф")
            return "regular"

    def _is_h1_by_pattern(self, text: str) -> bool:
        """Проверяет H1 заголовок по паттернам (fallback)"""
        import re
        patterns = self.requirements["h1_formatting"]["detection_patterns"]
        text_upper = text.upper().strip()
        
        for pattern in patterns:
            if re.match(pattern, text_upper):
                return True

        # Дополнительная эвристика
        if len(text) < 100:
            alpha_chars = [c for c in text if c.isalpha()]
            if alpha_chars:
                upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
                if upper_ratio > 0.7:
                    return True

        return False

    def _is_h2_by_pattern(self, text: str) -> bool:
        """Проверяет H2 заголовок по паттернам (fallback)"""
        import re
        patterns = self.requirements["h2_formatting"]["detection_patterns"]

        for pattern in patterns:
            if re.match(pattern, text.strip()):
                return True

        return False

    def _is_h3_by_pattern(self, text: str) -> bool:
        """Проверяет H3 заголовок по паттернам (fallback)"""
        import re
        patterns = self.requirements["h3_formatting"]["detection_patterns"]

        for pattern in patterns:
            if re.match(pattern, text.strip()):
                return True

        return False

    def _is_h4_by_pattern(self, text: str) -> bool:
        """Проверяет H4 заголовок по паттернам (fallback)"""
        import re
        patterns = self.requirements["h4_formatting"]["detection_patterns"]

        for pattern in patterns:
            if re.match(pattern, text.strip()):
                return True

        return False

    def _is_list_by_pattern(self, text: str) -> bool:
        """Проверяет элемент списка по паттернам (fallback)"""
        import re
        patterns = self.requirements["lists"]["bullet_lists"]["detection_patterns"]

        for pattern in patterns:
            if re.match(pattern, text):
                return True

        return False

    def _classify_special_sections(self, text_clean: str) -> str:
        """Классифицирует специальные разделы"""
        text_upper = text_clean.upper()
        
        # Проверяем заголовок списка литературы
        references_keywords = self.requirements["special_sections"]["references"]["keywords"]
        for keyword in references_keywords:
            if keyword.upper() in text_upper:
                logger.debug(f"   📚 Обнаружен заголовок списка литературы: {keyword}")
                self.state.start_references_section()
                return "references_header"
        
        # Если мы в разделе списка литературы, различаем начало записи и продолжение
        if self.state.in_references_section:
            if text_clean.strip():  # Любая непустая строка в списке литературы
                if self._is_bibliography_entry_start(text_clean):
                    return "bibliography_entry"
                else:
                    # Проверяем, может ли это быть началом записи без номера
                    if self._looks_like_bibliography_start(text_clean):
                        return "bibliography_entry"
                    else:
                        return "bibliography_continuation"
        
        # Проверяем специальные разделы
        special_sections = self.requirements["special_sections"]
        for section_name, section_config in special_sections.items():
            for keyword in section_config["keywords"]:
                if keyword.upper() in text_upper:
                    return f"special_{section_name}"
        
        return "regular"

    def _classify_content_elements(self, text_clean: str) -> str:
        """Классифицирует элементы контента (таблицы, рисунки, формулы)"""
        # Проверяем таблицы
        table_patterns = self.requirements["tables"]["detection_patterns"]
        for pattern in table_patterns:
            import re
            if re.search(pattern, text_clean, re.IGNORECASE):
                return "table_caption"
        
        # Проверяем подписи рисунков
        figure_patterns = self.requirements["figures"]["detection_patterns"]
        for pattern in figure_patterns:
            import re
            if re.search(pattern, text_clean, re.IGNORECASE):
                return "figure_caption"
        
        # Проверяем формулы и их элементы
        formula_patterns = self.requirements["formulas"]["detection_patterns"]
        import re
        
        # Проверяем нумерацию формул (в скобках)
        numbering_patterns = [r"\(\d+\.\d+\)", r"\(\d+\)"]
        for pattern in numbering_patterns:
            if re.search(pattern, text_clean):
                return "formula_numbering"
        
        # Проверяем пояснения к переменным
        explanation_patterns = [
            r"^где\s+[а-яёА-ЯЁ]",  # "где x – переменная"
            r"^[а-яёА-ЯЁ]\s*[-–—]\s*",  # "x – переменная"
            r"^в\s+которой\s+",  # "в которой x – переменная"
            r"^здесь\s+[а-яёА-ЯЁ]"  # "здесь x – переменная"
        ]
        for pattern in explanation_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                return "formula_explanation"
        
        # Проверяем заголовки формул
        formula_title_patterns = [r"^Формула\s+\d+", r"^Formula\s+\d+"]
        for pattern in formula_title_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                return "formula"
        
        # Проверяем математические выражения (простая эвристика)
        math_indicators = [
            r"[=+\-*/^]",  # Математические операторы
            r"[∑∏∫∂∆∇]",  # Математические символы
            r"[αβγδεζηθικλμνξοπρστυφχψω]",  # Греческие буквы
            r"[ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ]",  # Греческие буквы заглавные
            r"\b(sin|cos|tan|log|ln|exp|sqrt|lim|max|min)\b",  # Математические функции
            r"[₀₁₂₃₄₅₆₇₈₉]",  # Нижние индексы
            r"[⁰¹²³⁴⁵⁶⁷⁸⁹]"   # Верхние индексы
        ]
        
        # Если текст содержит математические элементы, считаем его формулой
        for pattern in math_indicators:
            if re.search(pattern, text_clean):
                return "formula"
        
        return "regular"

    def _is_bibliography_entry_start(self, text: str) -> bool:
        """Определяет, является ли текст НАЧАЛОМ библиографической записи (с номером)"""
        import re
        
        # Проверяем начало с номера - это главный признак начала новой записи
        # Паттерн 1: номер с пробелом и текстом ("1. Автор...")
        if re.match(r'^\s*\d+\.\s+', text):
            return True
        
        # Паттерн 2: только номер ("1.", "2.", "3.")
        if re.match(r'^\s*\d+\.\s*$', text):
            return True
        
        return False

    def _looks_like_bibliography_start(self, text: str) -> bool:
        """Определяет, похож ли текст на начало библиографической записи (без номера)"""
        import re
        
        # Паттерны для начала библиографических записей
        start_patterns = [
            r'^[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.',  # "Иванов И."
            r'^[A-Z][a-z]+\s+[A-Z]\.',       # "Smith J."
            r'^[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.',  # "Иванов И.И."
            r'^[A-Z][a-z]+\s+[A-Z]\.\s*[A-Z]\.',       # "Smith J.A."
            r'^[А-ЯЁ][а-яё\s]+\s*[:/]',     # "Название книги:"
            r'^[A-Z][a-zA-Z\s]+\s*[:/]',     # "Book Title:"
            r'^Документация\s+',             # "Документация Docker"
            r'^Официальный\s+сайт',          # "Официальный сайт"
            r'^Сайт\s+',                     # "Сайт вакансий"
        ]
        
        for pattern in start_patterns:
            if re.match(pattern, text):
                return True
        
        # Если строка начинается с заглавной буквы и содержит точку (возможно автор)
        if re.match(r'^[А-ЯЁA-Z]', text) and '.' in text[:50]:
            return True
        
        return False

    def _is_bibliography_entry(self, text: str) -> bool:
        """Определяет, является ли текст библиографической записью (устаревший метод, оставлен для совместимости)"""
        return self._is_bibliography_entry_start(text)

    def _is_special_h1_section(self, text_clean: str) -> bool:
        """Проверяет, является ли H1 заголовок специальным разделом"""
        text_upper = text_clean.upper()
        
        # Проверяем все специальные разделы
        special_sections = self.requirements["special_sections"]
        for section_name, section_config in special_sections.items():
            for keyword in section_config["keywords"]:
                if keyword.upper() in text_upper:
                    logger.debug(f"      🎯 Найден специальный раздел '{section_name}' по ключевому слову '{keyword}'")
                    return True
        
        return False

    def _contains_image(self, paragraph) -> bool:
        """Проверяет, содержит ли параграф изображение"""
        try:
            text = paragraph.text.strip()
            
            # Проверяем заглушки изображений (для тестирования)
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
                if placeholder in text.upper():
                    logger.debug(f"      🖼️ Найдена заглушка изображения: {text}")
                    return True
            
            # Проверяем наличие встроенных объектов (изображений)
            for run in paragraph.runs:
                # Проверяем встроенные объекты в run
                if hasattr(run, '_element') and run._element is not None:
                    # Ищем элементы изображений в XML
                    for child in run._element:
                        tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                        if tag_name in ['drawing', 'pict', 'object']:
                            logger.debug(f"      🖼️ Найдено изображение в параграфе (тег: {tag_name})")
                            return True
                        
                        # Проверяем вложенные элементы
                        for subchild in child:
                            subtag_name = subchild.tag.split('}')[-1] if '}' in subchild.tag else subchild.tag
                            if subtag_name in ['inline', 'anchor', 'pict', 'blip', 'graphic']:
                                logger.debug(f"      🖼️ Найдено встроенное изображение (тег: {subtag_name})")
                                return True
                            
                            # Проверяем еще глубже для сложных структур
                            for subsubchild in subchild:
                                subsubtag_name = subsubchild.tag.split('}')[-1] if '}' in subsubchild.tag else subsubchild.tag
                                if subsubtag_name in ['blip', 'graphic', 'pic']:
                                    logger.debug(f"      🖼️ Найдено глубоко вложенное изображение (тег: {subsubtag_name})")
                                    return True
            
            # Дополнительная проверка: если параграф очень короткий или пустой,
            # но содержит runs, возможно это изображение
            if len(text) == 0 and len(paragraph.runs) > 0:
                # Проверяем, есть ли в runs что-то кроме текста
                for run in paragraph.runs:
                    if hasattr(run, '_element') and run._element is not None:
                        # Если есть элементы, но нет текста - возможно изображение
                        if len(run._element) > 0 and not run.text.strip():
                            logger.debug(f"      🖼️ Пустой параграф с элементами - возможно изображение")
                            return True
                
            return False
            
        except Exception as e:
            logger.debug(f"      ⚠️ Ошибка проверки изображения: {e}")
            return False

    def _is_numbered_chapter(self, text: str) -> bool:
        """Проверяет, является ли текст нумерованной главой"""
        import re
        
        # Паттерны для нумерованных глав
        numbered_patterns = [
            r'^\d+\.\s+[А-ЯЁ]',  # "1. ВВЕДЕНИЕ", "2. АРХИТЕКТУРА"
            r'^ГЛАВА\s+\d+',      # "ГЛАВА 1"
            r'^\d+\s+[А-ЯЁ]'     # "1 ВВЕДЕНИЕ"
        ]
        
        text_upper = text.upper().strip()
        for pattern in numbered_patterns:
            if re.match(pattern, text_upper):
                return True
        
        return False

    def get_state(self) -> DocumentState:
        """Возвращает текущее состояние"""
        return self.state 