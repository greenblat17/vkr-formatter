import re
from typing import Dict, Any
from content_detector import ContentDetector
from document_state import DocumentState, logger


class ParagraphClassifier:
    """Классифицирует типы параграфов"""

    def __init__(self, requirements: Dict[str, Any]):
        self.requirements = requirements
        self.detector = ContentDetector()
        self.state = DocumentState()

    def classify_paragraph(self, text: str) -> str:
        """
        Классифицирует параграф

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
            return self._classify_content_paragraph(text_clean)

        # 5. Если в титульной секции
        if self.state.in_title_section:
            logger.debug(f"⚪ ПРОПУСК (титульная): {text_clean[:50]}...")
            return "skip"

        # 6. Классифицируем как обычное содержание
        return self._classify_content_paragraph(text_clean)

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
            return self._classify_content_paragraph(text_clean)
        else:
            # Пустая строка или неопределенное в содержании
            logger.debug(f"📑 СОДЕРЖАНИЕ (прочее): {text_clean[:50]}...")
            return "skip"

    def _classify_content_paragraph(self, text_clean: str) -> str:
        """Классифицирует параграфы основного содержания"""
        logger.debug(f"🔍 Классифицируем содержание: '{text_clean[:50]}...'")
        
        if self._is_h1_paragraph(text_clean):
            logger.debug(f"   ↳ Определен как H1")
            return "h1"
        elif self._is_h2_paragraph(text_clean):
            logger.debug(f"   ↳ Определен как H2")
            return "h2"
        elif self._is_list_paragraph(text_clean):
            logger.debug(f"   ↳ Определен как список")
            return "list"
        else:
            logger.debug(f"   ↳ Определен как обычный параграф")
            return "regular"

    def _is_h1_paragraph(self, text: str) -> bool:
        """Проверяет H1 заголовок"""
        patterns = self.requirements["h1_formatting"]["detection_patterns"]
        text_upper = text.upper().strip()
        
        logger.debug(f"      🔎 Проверяем H1: '{text_upper}'")

        for i, pattern in enumerate(patterns):
            if re.match(pattern, text_upper):
                logger.debug(f"         ✅ Совпадение с паттерном {i+1}: {pattern}")
                return True

        # Дополнительная проверка: короткий текст с заглавными буквами
        if len(text) < 100:
            alpha_chars = [c for c in text if c.isalpha()]
            if alpha_chars:
                upper_ratio = sum(
                    1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
                if upper_ratio > 0.7:
                    logger.debug(f"         ✅ Совпадение по эвристике (заглавные буквы: {upper_ratio:.2f})")
                    return True

        logger.debug(f"         ❌ Не является H1")
        return False

    def _is_h2_paragraph(self, text: str) -> bool:
        """Проверяет H2 заголовок"""
        patterns = self.requirements["h2_formatting"]["detection_patterns"]

        for pattern in patterns:
            if re.match(pattern, text.strip()):
                return True

        return False

    def _is_list_paragraph(self, text: str) -> bool:
        """Проверяет элемент списка"""
        patterns = self.requirements["lists"]["bullet_lists"]["detection_patterns"]

        for pattern in patterns:
            if re.match(pattern, text):
                return True

        return False

    def get_state(self) -> DocumentState:
        """Возвращает текущее состояние"""
        return self.state
