from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
from docx.enum.style import WD_STYLE_TYPE
import logging
from typing import Dict, Any, Optional, List
import traceback

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VKRFormatter:
    """Класс для форматирования ВКР согласно требованиям (упрощенная версия для заголовков 1 уровня)"""

    ALIGN_MAP = {
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
        "по ширине": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "по левому краю": WD_ALIGN_PARAGRAPH.LEFT,
        "по центру": WD_ALIGN_PARAGRAPH.CENTER,
        "по правому краю": WD_ALIGN_PARAGRAPH.RIGHT
    }

    LINE_SPACING_MAP = {
        1.0: WD_LINE_SPACING.SINGLE,
        1.5: WD_LINE_SPACING.ONE_POINT_FIVE,
        2.0: WD_LINE_SPACING.DOUBLE
    }

    def __init__(self):
        self.stats = {
            'total_paragraphs': 0,
            'h1_found': 0,
            'h1_processed': 0,
            'regular_paragraphs_processed': 0,
            'global_settings_applied': False,
            'errors': 0
        }

    def apply_formatting(self, input_path: str, formatting: Dict[str, Any], output_path: str) -> bool:
        """
        Применяет глобальные настройки ко всему документу + форматирование заголовков 1 уровня

        Args:
            input_path: путь к исходному документу
            formatting: словарь с требованиями к форматированию
            output_path: путь к выходному документу

        Returns:
            bool: успешность операции
        """
        try:
            # Сбрасываем статистику
            self.stats = {
                'total_paragraphs': 0,
                'h1_found': 0,
                'h1_processed': 0,
                'regular_paragraphs_processed': 0,
                'global_settings_applied': False,
                'errors': 0
            }

            doc = Document(input_path)

            # Шаг 1: Применяем глобальные настройки к документу
            self._apply_global_settings(doc, formatting)

            # Шаг 2: Обрабатываем все параграфы
            self._format_document_paragraphs(doc, formatting)

            # Сохраняем документ
            doc.save(output_path)

            logger.info(f"Форматирование завершено. Статистика: {self.stats}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при форматировании: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def _apply_global_settings(self, doc: Document, formatting: Dict[str, Any]) -> None:
        """Применяет глобальные настройки к документу"""
        try:
            global_settings = formatting.get("global_settings", {})

            # Применяем поля страницы
            margins = global_settings.get("margins", {})
            if margins:
                for section in doc.sections:
                    section.top_margin = Cm(margins.get("top", 2.0))
                    section.bottom_margin = Cm(margins.get("bottom", 2.0))
                    section.left_margin = Cm(margins.get("left", 3.0))
                    section.right_margin = Cm(margins.get("right", 1.5))

                logger.info(f"Применены глобальные поля: {margins}")

            self.stats['global_settings_applied'] = True

        except Exception as e:
            logger.error(f"Ошибка при применении глобальных настроек: {e}")
            self.stats['errors'] += 1

    def _format_document_paragraphs(self, doc: Document, formatting: Dict[str, Any]) -> None:
        """Форматирует все параграфы: H1 особо, остальные по глобальным настройкам"""

        for paragraph in doc.paragraphs:
            self.stats['total_paragraphs'] += 1

            try:
                # Проверяем, является ли параграф заголовком 1 уровня
                if self._is_h1_header(paragraph):
                    self.stats['h1_found'] += 1
                    logger.info(f"Найден H1: '{paragraph.text[:50]}...'")

                    # Применяем специальное форматирование для H1
                    self._format_h1_paragraph(paragraph, formatting)
                    self.stats['h1_processed'] += 1
                else:
                    # Применяем глобальные настройки к обычному тексту
                    self._format_regular_paragraph(paragraph, formatting)
                    self.stats['regular_paragraphs_processed'] += 1

            except Exception as e:
                logger.warning(f"Ошибка при обработке параграфа: {e}")
                self.stats['errors'] += 1
                continue

    def _format_regular_paragraph(self, paragraph, formatting: Dict[str, Any]) -> None:
        """Применяет глобальные настройки к обычному параграфу"""

        # Пропускаем пустые параграфы
        if not paragraph.text.strip():
            return

        global_settings = formatting.get("global_settings", {})

        # Форматируем runs
        if not paragraph.runs:
            paragraph.add_run()

        for run in paragraph.runs:
            font = run.font

            # Основной шрифт и размер
            font.name = global_settings.get("font_name", "Times New Roman")
            font.size = Pt(global_settings.get("font_size", 14))

        # Форматирование параграфа
        pf = paragraph.paragraph_format

        # Выравнивание
        alignment = global_settings.get("text_alignment", "justify")
        paragraph.alignment = self.ALIGN_MAP.get(
            alignment, WD_ALIGN_PARAGRAPH.JUSTIFY)

        # Отступ первой строки
        indent = global_settings.get("paragraph_indent", 1.25)
        if isinstance(indent, (int, float)):
            pf.first_line_indent = Cm(indent)

        # Междустрочный интервал
        line_spacing = global_settings.get("line_spacing", 1.5)
        if line_spacing in self.LINE_SPACING_MAP:
            pf.line_spacing_rule = self.LINE_SPACING_MAP[line_spacing]
        elif isinstance(line_spacing, (int, float)):
            pf.line_spacing = line_spacing

    def _is_h1_header(self, paragraph) -> bool:
        """
        Определяет, является ли параграф заголовком 1 уровня
        Используем несколько критериев:
        1. Стиль параграфа содержит "Heading 1" или "Заголовок 1"
        2. Текст короткий (меньше 100 символов) и написан заглавными буквами
        3. Параграф имеет больший размер шрифта
        """

        # Критерий 1: Проверяем стиль
        if paragraph.style and paragraph.style.name:
            style_name = paragraph.style.name.lower()
            if any(keyword in style_name for keyword in ['heading 1', 'заголовок 1', 'title']):
                logger.debug(f"H1 найден по стилю: {paragraph.style.name}")
                return True

        # Критерий 2: Короткий текст заглавными буквами
        text = paragraph.text.strip()
        if text and len(text) < 100:
            # Проверяем процент заглавных букв
            upper_ratio = sum(1 for c in text if c.isupper()) / \
                len([c for c in text if c.isalpha()])
            if upper_ratio > 0.7:  # Больше 70% заглавных букв
                logger.debug(f"H1 найден по заглавным буквам: {text[:30]}")
                return True

        # Критерий 3: Больший размер шрифта
        if paragraph.runs:
            for run in paragraph.runs:
                if run.font.size and run.font.size.pt > 16:  # Размер больше 16pt
                    logger.debug(
                        f"H1 найден по размеру шрифта: {run.font.size.pt}pt")
                    return True

        # Критерий 4: Простые числовые заголовки (1., 2., ГЛАВА 1 и т.д.)
        if text and len(text) < 50:
            import re
            # Проверяем паттерны типа "1.", "ГЛАВА 1", "1. ВВЕДЕНИЕ"
            patterns = [
                r'^\d+\.\s*[А-ЯЁ\s]+$',  # "1. ВВЕДЕНИЕ"
                r'^ГЛАВА\s+\d+',          # "ГЛАВА 1"
                r'^\d+\.$',               # "1."
                r'^[IVX]+\.\s*[А-ЯЁ\s]+$'  # "I. ВВЕДЕНИЕ"
            ]
            for pattern in patterns:
                if re.match(pattern, text.upper()):
                    logger.debug(f"H1 найден по паттерну: {text}")
                    return True

        return False

    def _format_h1_paragraph(self, paragraph, formatting: Dict[str, Any]) -> None:
        """Применяет форматирование к заголовку 1 уровня"""

        # Получаем настройки для H1 из форматирования
        h1_settings = formatting.get("h1_formatting", {})

        # Если специальных настроек для H1 нет, используем общие
        if not h1_settings:
            h1_settings = {
                "font_name": formatting.get("font_name", "Times New Roman"),
                "font_size": formatting.get("font_size_h1", formatting.get("font_size_main", 16)),
                "alignment": formatting.get("h1_alignment", "center"),
                "bold": formatting.get("h1_bold", True),
                "uppercase": formatting.get("h1_uppercase", True),
                "page_break_before": formatting.get("h1_page_break_before", False)
            }

        # Добавляем разрыв страницы ПЕРЕД заголовком, если нужно
        if h1_settings.get("page_break_before", False):
            # Проверяем, не первый ли это параграф в документе
            if self._is_not_first_paragraph(paragraph):
                # Добавляем разрыв страницы в начало параграфа
                if paragraph.runs:
                    # Вставляем разрыв в первый run
                    first_run = paragraph.runs[0]
                    first_run.text = first_run.text
                    first_run.add_break(WD_BREAK.PAGE)
                else:
                    # Создаем новый run с разрывом
                    run = paragraph.add_run()
                    run.add_break(WD_BREAK.PAGE)

                logger.info(
                    f"Добавлен разрыв страницы перед H1: {paragraph.text[:30]}...")

        # Форматируем runs
        if not paragraph.runs:
            paragraph.add_run()

        for run in paragraph.runs:
            font = run.font

            # Шрифт и размер
            font.name = h1_settings.get("font_name", "Times New Roman")
            font.size = Pt(h1_settings.get("font_size", 16))

            # Жирность
            if h1_settings.get("bold", True):
                font.bold = True

        # Приводим к верхнему регистру если нужно
        if h1_settings.get("uppercase", True):
            # Сохраняем исходный текст и преобразуем только видимую часть
            original_text = paragraph.text
            paragraph.clear()
            paragraph.add_run(original_text.upper())

        # Выравнивание
        alignment = h1_settings.get("alignment", "center")
        paragraph.alignment = self.ALIGN_MAP.get(
            alignment, WD_ALIGN_PARAGRAPH.CENTER)

        # Отступы и интервалы
        pf = paragraph.paragraph_format
        pf.space_before = Pt(h1_settings.get("space_before", 12))
        pf.space_after = Pt(h1_settings.get("space_after", 12))

        logger.info(f"H1 отформатирован: {paragraph.text[:30]}...")

    def _is_not_first_paragraph(self, target_paragraph) -> bool:
        """Проверяет, не является ли параграф первым в документе"""
        try:
            # Получаем родительский документ
            doc = target_paragraph._parent
            while hasattr(doc, '_parent') and doc._parent is not None:
                doc = doc._parent

            # Находим все параграфы
            all_paragraphs = doc.paragraphs

            # Проверяем, есть ли до этого параграфа другие непустые параграфы
            for i, paragraph in enumerate(all_paragraphs):
                if paragraph == target_paragraph:
                    # Проверяем, есть ли до него непустые параграфы
                    for j in range(i):
                        if all_paragraphs[j].text.strip():
                            return True
                    return False

            return True  # По умолчанию считаем, что не первый

        except Exception as e:
            logger.warning(f"Ошибка при проверке позиции параграфа: {e}")
            return True  # В случае ошибки лучше добавить разрыв

    def validate_formatting(self, formatting: Dict[str, Any]) -> Dict[str, Any]:
        """Валидирует форматирование для глобальных настроек + H1"""
        validated = {}

        # Глобальные настройки
        global_settings = formatting.get("global_settings", {})
        validated["global_settings"] = {
            "margins": {
                "top": max(1, global_settings.get("margins", {}).get("top", 2.0)),
                "bottom": max(1, global_settings.get("margins", {}).get("bottom", 2.0)),
                "left": max(1, global_settings.get("margins", {}).get("left", 3.0)),
                "right": max(1, global_settings.get("margins", {}).get("right", 1.5))
            },
            "font_name": global_settings.get("font_name", "Times New Roman"),
            "font_size": max(8, min(72, global_settings.get("font_size", 14))),
            "line_spacing": max(1.0, global_settings.get("line_spacing", 1.5)),
            "paragraph_indent": max(0, global_settings.get("paragraph_indent", 1.25)),
            "text_alignment": global_settings.get("text_alignment", "justify")
        }

        # Настройки для H1
        h1_formatting = formatting.get("h1_formatting", {})
        validated["h1_formatting"] = {
            "font_name": h1_formatting.get("font_name", validated["global_settings"]["font_name"]),
            "font_size": max(8, min(72, h1_formatting.get("font_size", 16))),
            "alignment": h1_formatting.get("alignment", "center"),
            "bold": h1_formatting.get("bold", True),
            "uppercase": h1_formatting.get("uppercase", True),
            "space_before": max(0, h1_formatting.get("space_before", 12)),
            "space_after": max(0, h1_formatting.get("space_after", 12)),
            "page_break_before": h1_formatting.get("page_break_before", False)
        }

        return validated

    def get_stats(self) -> Dict[str, int]:
        """Возвращает статистику обработки"""
        return self.stats.copy()


def apply_formatting(input_path: str, formatting: Dict[str, Any], output_path: str) -> bool:
    """
    Функция-обертка для обратной совместимости
    """
    formatter = VKRFormatter()
    validated_formatting = formatter.validate_formatting(formatting)
    return formatter.apply_formatting(input_path, validated_formatting, output_path)
