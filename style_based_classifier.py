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
        
        # Классифицируем по стилю (приоритет стилям!)
        if self._is_h1_style(style_name):
            logger.debug(f"   ↳ Определен как H1 по стилю")
            return "h1"
        elif self._is_h2_style(style_name):
            logger.debug(f"   ↳ Определен как H2 по стилю")
            return "h2"
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
            # Для других стилей (не заголовочных) считаем обычным текстом
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

    def _is_list_by_pattern(self, text: str) -> bool:
        """Проверяет элемент списка по паттернам (fallback)"""
        import re
        patterns = self.requirements["lists"]["bullet_lists"]["detection_patterns"]

        for pattern in patterns:
            if re.match(pattern, text):
                return True

        return False

    def get_state(self) -> DocumentState:
        """Возвращает текущее состояние"""
        return self.state 