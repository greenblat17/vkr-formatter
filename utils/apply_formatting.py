from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.style import WD_STYLE_TYPE
import logging
from typing import Dict, Any, Optional, List
import traceback

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
    
    def __init__(self):
        self.stats = {
            'total_paragraphs': 0,
            'h1_found': 0,
            'h1_processed': 0,
            'title_page_paragraphs': 0,
            'errors': 0
        }
    
    def _is_title_page(self, paragraph) -> bool:
        """
        Определяет, является ли параграф частью титульного листа
        """
        # Проверяем стиль
        if paragraph.style and paragraph.style.name:
            style_name = paragraph.style.name.lower()
            if any(keyword in style_name for keyword in ['title', 'титул', 'cover']):
                return True
        
        # Проверяем содержимое
        text = paragraph.text.strip().lower()
        title_keywords = [
            'министерство', 'образования', 'науки', 'федеральное', 'государственное',
            'бюджетное', 'образовательное', 'учреждение', 'высшего', 'образования',
            'дипломная', 'работа', 'выполнил', 'студент', 'группы', 'научный',
            'руководитель', 'должность', 'ученая', 'степень', 'город', 'год'
        ]
        
        # Если параграф содержит ключевые слова титульного листа
        if any(keyword in text for keyword in title_keywords):
            return True
            
        # Проверяем форматирование
        if paragraph.runs:
            for run in paragraph.runs:
                # Если текст отцентрирован и имеет большой размер шрифта
                if (paragraph.alignment == WD_ALIGN_PARAGRAPH.CENTER and 
                    run.font.size and run.font.size.pt > 14):
                    return True
        
        return False
    
    def apply_formatting(self, input_path: str, formatting: Dict[str, Any], output_path: str) -> bool:
        """
        Применяет форматирование только к заголовкам 1 уровня, пропуская титульный лист
        
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
                'title_page_paragraphs': 0,
                'errors': 0
            }
            
            doc = Document(input_path)
            
            # Обрабатываем только заголовки 1 уровня, пропуская титульный лист
            self._format_h1_headers(doc, formatting)
            
            # Сохраняем документ
            doc.save(output_path)
            
            logger.info(f"Форматирование H1 завершено. Статистика: {self.stats}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при форматировании: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _format_h1_headers(self, doc: Document, formatting: Dict[str, Any]) -> None:
        """Ищет и форматирует только заголовки 1 уровня, пропуская титульный лист"""
        
        for paragraph in doc.paragraphs:
            self.stats['total_paragraphs'] += 1
            
            try:
                # Пропускаем параграфы титульного листа
                if self._is_title_page(paragraph):
                    self.stats['title_page_paragraphs'] += 1
                    logger.debug(f"Пропущен параграф титульного листа: '{paragraph.text[:50]}...'")
                    continue
                
                # Определяем, является ли параграф заголовком 1 уровня
                if self._is_h1_header(paragraph):
                    self.stats['h1_found'] += 1
                    logger.info(f"Найден H1: '{paragraph.text[:50]}...'")
                    
                    # Применяем форматирование к H1
                    self._format_h1_paragraph(paragraph, formatting)
                    self.stats['h1_processed'] += 1
                    
            except Exception as e:
                logger.warning(f"Ошибка при обработке параграфа: {e}")
                self.stats['errors'] += 1
                continue
    
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
            upper_ratio = sum(1 for c in text if c.isupper()) / len([c for c in text if c.isalpha()])
            if upper_ratio > 0.7:  # Больше 70% заглавных букв
                logger.debug(f"H1 найден по заглавным буквам: {text[:30]}")
                return True
        
        # Критерий 3: Больший размер шрифта
        if paragraph.runs:
            for run in paragraph.runs:
                if run.font.size and run.font.size.pt > 16:  # Размер больше 16pt
                    logger.debug(f"H1 найден по размеру шрифта: {run.font.size.pt}pt")
                    return True
        
        # Критерий 4: Простые числовые заголовки (1., 2., ГЛАВА 1 и т.д.)
        if text and len(text) < 50:
            import re
            # Проверяем паттерны типа "1.", "ГЛАВА 1", "1. ВВЕДЕНИЕ"
            patterns = [
                r'^\d+\.\s*[А-ЯЁ\s]+$',  # "1. ВВЕДЕНИЕ"
                r'^ГЛАВА\s+\d+',          # "ГЛАВА 1"
                r'^\d+\.$',               # "1."
                r'^[IVX]+\.\s*[А-ЯЁ\s]+$' # "I. ВВЕДЕНИЕ"
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
                "uppercase": formatting.get("h1_uppercase", True)
            }
        
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
            paragraph.text = paragraph.text.upper()
        
        # Выравнивание
        alignment = h1_settings.get("alignment", "center")
        paragraph.alignment = self.ALIGN_MAP.get(alignment, WD_ALIGN_PARAGRAPH.CENTER)
        
        # Отступы и интервалы
        pf = paragraph.paragraph_format
        pf.space_before = Pt(h1_settings.get("space_before", 12))
        pf.space_after = Pt(h1_settings.get("space_after", 12))
        
        logger.info(f"H1 отформатирован: {paragraph.text[:30]}...")
    
    def validate_formatting(self, formatting: Dict[str, Any]) -> Dict[str, Any]:
        """Валидирует форматирование для H1"""
        validated = {}
        
        # Основные настройки
        validated["font_name"] = formatting.get("font_name", "Times New Roman")
        validated["font_size_main"] = max(8, min(72, formatting.get("font_size_main", 14)))
        
        # Настройки для H1
        h1_formatting = formatting.get("h1_formatting", {})
        validated["h1_formatting"] = {
            "font_name": h1_formatting.get("font_name", validated["font_name"]),
            "font_size": max(8, min(72, h1_formatting.get("font_size", 16))),
            "alignment": h1_formatting.get("alignment", "center"),
            "bold": h1_formatting.get("bold", True),
            "uppercase": h1_formatting.get("uppercase", True),
            "space_before": max(0, h1_formatting.get("space_before", 12)),
            "space_after": max(0, h1_formatting.get("space_after", 12))
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


    # formatter = VKRFormatter()
    # success = formatter.apply_formatting("input.docx", sample_formatting, "output.docx")
    # print(f"Форматирование H1 {'успешно' if success else 'не удалось'}")
    # print(f"Статистика: {formatter.get_stats()}")