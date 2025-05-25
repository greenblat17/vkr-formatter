from docx.shared import Pt, Cm
from docx.enum.text import WD_BREAK
from typing import Dict, Any
from formatting_constants import FormattingConstants
from document_state import logger

class ParagraphFormatter:
    """Форматирует параграфы разных типов"""
    
    def __init__(self, requirements: Dict[str, Any]):
        self.requirements = requirements
    
    def format_h1(self, paragraph) -> None:
        """Форматирует заголовок H1"""
        try:
            config = self.requirements["h1_formatting"]
            
            # Разрыв страницы
            if config["page_break_before"] and self._not_first_paragraph(paragraph):
                self._add_page_break_before(paragraph)
            
            # Форматирование
            self._apply_font_formatting(paragraph, config)
            
            # Заглавные буквы
            if config["text_transform"] == "uppercase":
                self._make_text_uppercase(paragraph, config)
            
            # Выравнивание и отступы
            paragraph.alignment = FormattingConstants.ALIGN_MAP[config["alignment"]]
            
            pf = paragraph.paragraph_format
            pf.space_before = Pt(config["space_before_pt"])
            pf.space_after = Pt(config["space_after_pt"])
            
            logger.debug(f"H1 отформатирован: {paragraph.text[:30]}...")
            
        except Exception as e:
            logger.error(f"Ошибка форматирования H1: {e}")
            raise
    
    def format_h2(self, paragraph) -> None:
        """Форматирует заголовок H2"""
        try:
            config = self.requirements["h2_formatting"]
            
            self._apply_font_formatting(paragraph, config)
            paragraph.alignment = FormattingConstants.ALIGN_MAP[config["alignment"]]
            
            pf = paragraph.paragraph_format
            pf.space_before = Pt(config["space_before_pt"])
            pf.space_after = Pt(config["space_after_pt"])
            pf.left_indent = Cm(config.get("paragraph_indent_cm", 0))
            
            logger.debug(f"H2 отформатирован: {paragraph.text[:30]}...")
            
        except Exception as e:
            logger.error(f"Ошибка форматирования H2: {e}")
            raise
    
    def format_list(self, paragraph) -> None:
        """Форматирует элемент списка"""
        try:
            config = self.requirements["lists"]["bullet_lists"]
            font_config = config["font"]
            
            self._apply_font_formatting(paragraph, {
                "font_name": font_config["name"],
                "font_size": font_config["size"]
            })
            
            paragraph.alignment = FormattingConstants.ALIGN_MAP[config["alignment"]]
            
            pf = paragraph.paragraph_format
            pf.left_indent = Cm(config["indent_cm"])
            
            line_spacing = font_config["line_spacing"]
            if line_spacing in FormattingConstants.LINE_SPACING_MAP:
                pf.line_spacing_rule = FormattingConstants.LINE_SPACING_MAP[line_spacing]
            
            logger.debug(f"Список отформатирован: {paragraph.text[:30]}...")
            
        except Exception as e:
            logger.error(f"Ошибка форматирования списка: {e}")
            raise
    
    def format_regular(self, paragraph) -> None:
        """Форматирует обычный параграф"""
        try:
            if not paragraph.text.strip():
                return
            
            config = self.requirements["base_formatting"]
            
            self._apply_font_formatting(paragraph, config)
            paragraph.alignment = FormattingConstants.ALIGN_MAP[config["text_alignment"]]
            
            pf = paragraph.paragraph_format
            pf.first_line_indent = Cm(config["paragraph_indent_cm"])
            
            line_spacing = config["line_spacing"]
            if line_spacing in FormattingConstants.LINE_SPACING_MAP:
                pf.line_spacing_rule = FormattingConstants.LINE_SPACING_MAP[line_spacing]
            
        except Exception as e:
            logger.error(f"Ошибка форматирования обычного параграфа: {e}")
            raise
    
    def _apply_font_formatting(self, paragraph, config: Dict[str, Any]) -> None:
        """Применяет форматирование шрифта"""
        if not paragraph.runs:
            paragraph.add_run()
        
        for run in paragraph.runs:
            font = run.font
            
            if "font_name" in config:
                font.name = config["font_name"]
            
            if "font_size" in config:
                font.size = Pt(config["font_size"])
            
            if config.get("font_weight") == "bold":
                font.bold = True
    
    def _make_text_uppercase(self, paragraph, config: Dict[str, Any]) -> None:
        """Преобразует текст в верхний регистр"""
        original_text = paragraph.text
        paragraph.clear()
        run = paragraph.add_run(original_text.upper())
        
        font = run.font
        font.name = config["font_name"]
        font.size = Pt(config["font_size"])
        if config["font_weight"] == "bold":
            font.bold = True
    
    def _add_page_break_before(self, paragraph) -> None:
        """Добавляет разрыв страницы"""
        if paragraph.runs:
            first_run = paragraph.runs[0]
            first_run.add_break(WD_BREAK.PAGE)
        else:
            run = paragraph.add_run()
            run.add_break(WD_BREAK.PAGE)
    
    def _not_first_paragraph(self, target_paragraph) -> bool:
        """Проверяет, что параграф не первый"""
        try:
            doc = target_paragraph._parent
            while hasattr(doc, '_parent') and doc._parent is not None:
                doc = doc._parent
            
            for i, paragraph in enumerate(doc.paragraphs):
                if paragraph == target_paragraph:
                    for j in range(i):
                        if doc.paragraphs[j].text.strip():
                            return True
                    return False
            
            return True
            
        except Exception:
            return True 