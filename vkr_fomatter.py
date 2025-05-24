from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
import re
import logging
from typing import Dict, Any, List
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleVKRFormatter:
    """Простой и понятный форматтер ВКР"""
    
    def __init__(self, requirements: Dict[str, Any]):
        """
        Args:
            requirements: словарь требований из заглушки
        """
        self.requirements = requirements
        self.stats = {
            'total_paragraphs': 0,
            'skipped_paragraphs': 0,
            'h1_formatted': 0,
            'h2_formatted': 0,
            'lists_formatted': 0,
            'regular_formatted': 0,
            'errors': 0
        }
        
        # Маппинги для удобства
        self.align_map = {
            "left": WD_ALIGN_PARAGRAPH.LEFT,
            "center": WD_ALIGN_PARAGRAPH.CENTER,
            "right": WD_ALIGN_PARAGRAPH.RIGHT,
            "justify": WD_ALIGN_PARAGRAPH.JUSTIFY
        }
        
        self.line_spacing_map = {
            1.0: WD_LINE_SPACING.SINGLE,
            1.5: WD_LINE_SPACING.ONE_POINT_FIVE,
            2.0: WD_LINE_SPACING.DOUBLE
        }
    
    def format_document(self, input_path: str, output_path: str) -> bool:
        """
        Основная функция форматирования документа
        
        Args:
            input_path: путь к исходному документу
            output_path: путь к результату
            
        Returns:
            bool: успешность операции
        """
        try:
            logger.info(f"Начинаем форматирование: {input_path}")
            logger.info(f"Выходной путь: {output_path}")
            
            # Проверяем входной файл
            input_file = Path(input_path)
            if not input_file.exists():
                logger.error(f"Входной файл не существует: {input_path}")
                return False
            
            # Загружаем документ
            logger.info("Загружаем документ...")
            doc = Document(input_path)
            logger.info(f"Документ загружен, параграфов: {len(doc.paragraphs)}")
            
            # Шаг 1: Применяем глобальные настройки (поля, базовый шрифт)
            logger.info("Применяем глобальные настройки...")
            self._apply_global_settings(doc)
            
            # Шаг 2: Обрабатываем каждый параграф
            logger.info("Обрабатываем параграфы...")
            self._process_all_paragraphs(doc)
            
            # Шаг 3: Сохраняем результат
            logger.info(f"Сохраняем документ в: {output_path}")
            doc.save(output_path)
            
            # Проверяем, что файл создался
            output_file = Path(output_path)
            if output_file.exists():
                logger.info(f"Файл успешно создан, размер: {output_file.stat().st_size} байт")
            else:
                logger.error(f"Файл НЕ создался: {output_path}")
                return False
            
            logger.info(f"Форматирование завершено успешно. Статистика: {self.stats}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка форматирования: {e}")
            import traceback
            logger.error(f"Полная трассировка: {traceback.format_exc()}")
            return False
    
    def _apply_global_settings(self, doc: Document) -> None:
        """Применяет глобальные настройки: поля страницы"""
        
        try:
            margins = self.requirements["base_formatting"]["margins_cm"]
            
            # Применяем поля ко всем секциям
            for section in doc.sections:
                section.top_margin = Cm(margins["top"])
                section.bottom_margin = Cm(margins["bottom"])
                section.left_margin = Cm(margins["left"])
                section.right_margin = Cm(margins["right"])
            
            logger.info(f"Применены поля: {margins}")
            
        except Exception as e:
            logger.error(f"Ошибка применения глобальных настроек: {e}")
            self.stats['errors'] += 1
    
    def _process_all_paragraphs(self, doc: Document) -> None:
        """Обрабатывает все параграфы документа"""
        
        for paragraph in doc.paragraphs:
            self.stats['total_paragraphs'] += 1
            
            try:
                # Определяем тип параграфа
                paragraph_type = self._classify_paragraph(paragraph.text.strip())
                
                # Применяем соответствующее форматирование
                if paragraph_type == "skip":
                    self.stats['skipped_paragraphs'] += 1
                    logger.debug(f"Пропускаем: {paragraph.text[:50]}...")
                    
                elif paragraph_type == "h1":
                    self._format_h1_paragraph(paragraph)
                    self.stats['h1_formatted'] += 1
                    
                elif paragraph_type == "h2":
                    self._format_h2_paragraph(paragraph)
                    self.stats['h2_formatted'] += 1
                    
                elif paragraph_type == "list":
                    self._format_list_paragraph(paragraph)
                    self.stats['lists_formatted'] += 1
                    
                else:  # regular
                    self._format_regular_paragraph(paragraph)
                    self.stats['regular_formatted'] += 1
                    
            except Exception as e:
                logger.warning(f"Ошибка обработки параграфа: {e}")
                self.stats['errors'] += 1
    
    def _classify_paragraph(self, text: str) -> str:
        """
        Классифицирует тип параграфа
        
        Returns:
            str: "skip", "h1", "h2", "list", "regular"
        """
        if not text:
            return "skip"
        
        # 1. Проверяем, нужно ли пропустить
        if self._should_skip_paragraph(text):
            return "skip"
        
        # 2. Проверяем H1
        if self._is_h1_paragraph(text):
            return "h1"
        
        # 3. Проверяем H2
        if self._is_h2_paragraph(text):
            return "h2"
        
        # 4. Проверяем список
        if self._is_list_paragraph(text):
            return "list"
        
        # 5. Обычный параграф
        return "regular"
    
    def _should_skip_paragraph(self, text: str) -> bool:
        """Проверяет, нужно ли пропустить параграф"""
        
        skip_sections = self.requirements["skip_sections"]
        text_upper = text.upper()
        
        # Проверяем все категории для пропуска
        for category, keywords in skip_sections.items():
            for keyword in keywords:
                if keyword.upper() in text_upper:
                    return True
        
        return False
    
    def _is_h1_paragraph(self, text: str) -> bool:
        """Проверяет, является ли параграф заголовком H1"""
        
        patterns = self.requirements["h1_formatting"]["detection_patterns"]
        
        for pattern in patterns:
            if re.match(pattern, text.upper().strip()):
                return True
        
        # Дополнительная проверка: короткий текст с большим процентом заглавных букв
        if len(text) < 100:
            alpha_chars = [c for c in text if c.isalpha()]
            if alpha_chars:
                upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
                if upper_ratio > 0.7:
                    return True
        
        return False
    
    def _is_h2_paragraph(self, text: str) -> bool:
        """Проверяет, является ли параграф заголовком H2"""
        
        patterns = self.requirements["h2_formatting"]["detection_patterns"]
        
        for pattern in patterns:
            if re.match(pattern, text.strip()):
                return True
        
        return False
    
    def _is_list_paragraph(self, text: str) -> bool:
        """Проверяет, является ли параграф элементом списка"""
        
        patterns = self.requirements["lists"]["bullet_lists"]["detection_patterns"]
        
        for pattern in patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _format_h1_paragraph(self, paragraph) -> None:
        """Форматирует заголовок H1"""
        
        try:
            h1_config = self.requirements["h1_formatting"]
            
            # Добавляем разрыв страницы если нужно
            if h1_config["page_break_before"] and self._not_first_paragraph(paragraph):
                self._add_page_break_before(paragraph)
            
            # Форматируем текст
            self._apply_font_formatting(paragraph, h1_config)
            
            # Заглавные буквы
            if h1_config["text_transform"] == "uppercase":
                self._make_text_uppercase(paragraph)
            
            # Выравнивание
            paragraph.alignment = self.align_map[h1_config["alignment"]]
            
            # Отступы
            pf = paragraph.paragraph_format
            pf.space_before = Pt(h1_config["space_before_pt"])
            pf.space_after = Pt(h1_config["space_after_pt"])
            
            logger.debug(f"H1 отформатирован: {paragraph.text[:30]}...")
            
        except Exception as e:
            logger.error(f"Ошибка форматирования H1: {e}")
            raise
    
    def _format_h2_paragraph(self, paragraph) -> None:
        """Форматирует заголовок H2"""
        
        try:
            h2_config = self.requirements["h2_formatting"]
            
            # Форматируем текст
            self._apply_font_formatting(paragraph, h2_config)
            
            # Выравнивание
            paragraph.alignment = self.align_map[h2_config["alignment"]]
            
            # Отступы
            pf = paragraph.paragraph_format
            pf.space_before = Pt(h2_config["space_before_pt"])
            pf.space_after = Pt(h2_config["space_after_pt"])
            pf.left_indent = Cm(h2_config.get("paragraph_indent_cm", 0))
            
            logger.debug(f"H2 отформатирован: {paragraph.text[:30]}...")
            
        except Exception as e:
            logger.error(f"Ошибка форматирования H2: {e}")
            raise
    
    def _format_list_paragraph(self, paragraph) -> None:
        """Форматирует элемент списка"""
        
        try:
            list_config = self.requirements["lists"]["bullet_lists"]
            font_config = list_config["font"]
            
            # Форматируем шрифт
            self._apply_font_formatting(paragraph, {
                "font_name": font_config["name"],
                "font_size": font_config["size"]
            })
            
            # Выравнивание
            paragraph.alignment = self.align_map[list_config["alignment"]]
            
            # Отступ
            pf = paragraph.paragraph_format
            pf.left_indent = Cm(list_config["indent_cm"])
            
            # Междустрочный интервал
            line_spacing = font_config["line_spacing"]
            if line_spacing in self.line_spacing_map:
                pf.line_spacing_rule = self.line_spacing_map[line_spacing]
            
            logger.debug(f"Список отформатирован: {paragraph.text[:30]}...")
            
        except Exception as e:
            logger.error(f"Ошибка форматирования списка: {e}")
            raise
    
    def _format_regular_paragraph(self, paragraph) -> None:
        """Форматирует обычный параграф"""
        
        try:
            if not paragraph.text.strip():
                return
            
            base_config = self.requirements["base_formatting"]
            
            # Форматируем шрифт
            self._apply_font_formatting(paragraph, base_config)
            
            # Выравнивание
            paragraph.alignment = self.align_map[base_config["text_alignment"]]
            
            # Отступы и интервалы
            pf = paragraph.paragraph_format
            pf.first_line_indent = Cm(base_config["paragraph_indent_cm"])
            
            # Междустрочный интервал
            line_spacing = base_config["line_spacing"]
            if line_spacing in self.line_spacing_map:
                pf.line_spacing_rule = self.line_spacing_map[line_spacing]
            
        except Exception as e:
            logger.error(f"Ошибка форматирования обычного параграфа: {e}")
            raise
    
    def _apply_font_formatting(self, paragraph, config: Dict[str, Any]) -> None:
        """Применяет форматирование шрифта к параграфу"""
        
        # Создаем run если его нет
        if not paragraph.runs:
            paragraph.add_run()
        
        # Применяем ко всем runs
        for run in paragraph.runs:
            font = run.font
            
            if "font_name" in config:
                font.name = config["font_name"]
            
            if "font_size" in config:
                font.size = Pt(config["font_size"])
            
            if config.get("font_weight") == "bold":
                font.bold = True
    
    def _make_text_uppercase(self, paragraph) -> None:
        """Преобразует текст параграфа в верхний регистр"""
        
        original_text = paragraph.text
        paragraph.clear()
        run = paragraph.add_run(original_text.upper())
        
        # Сохраняем базовое форматирование
        font = run.font
        font.name = self.requirements["h1_formatting"]["font_name"]
        font.size = Pt(self.requirements["h1_formatting"]["font_size"])
        if self.requirements["h1_formatting"]["font_weight"] == "bold":
            font.bold = True
    
    def _add_page_break_before(self, paragraph) -> None:
        """Добавляет разрыв страницы перед параграфом"""
        
        if paragraph.runs:
            # Вставляем разрыв в начало первого run
            first_run = paragraph.runs[0]
            first_run.add_break(WD_BREAK.PAGE)
        else:
            # Создаем новый run с разрывом
            run = paragraph.add_run()
            run.add_break(WD_BREAK.PAGE)
    
    def _not_first_paragraph(self, target_paragraph) -> bool:
        """Проверяет, что параграф не первый в документе"""
        
        try:
            # Получаем документ
            doc = target_paragraph._parent
            while hasattr(doc, '_parent') and doc._parent is not None:
                doc = doc._parent
            
            # Проверяем позицию
            for i, paragraph in enumerate(doc.paragraphs):
                if paragraph == target_paragraph:
                    # Есть ли непустые параграфы до этого?
                    for j in range(i):
                        if doc.paragraphs[j].text.strip():
                            return True
                    return False
            
            return True
            
        except Exception:
            return True  # В случае ошибки считаем, что не первый
    
    def get_statistics(self) -> Dict[str, int]:
        """Возвращает статистику обработки"""
        return self.stats.copy()


# Главная функция для использования в API
def format_vkr_document(input_path: str, requirements: Dict[str, Any], output_path: str) -> tuple[bool, Dict[str, int]]:
    """
    Форматирует ВКР согласно требованиям
    
    Args:
        input_path: путь к исходному файлу ВКР
        requirements: словарь требований (из заглушки)
        output_path: путь к результирующему файлу
        
    Returns:
        tuple: (успех, статистика)
    """
    
    formatter = SimpleVKRFormatter(requirements)
    success = formatter.format_document(input_path, output_path)
    stats = formatter.get_statistics()
    
    return success, stats
