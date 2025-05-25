from docx import Document
from docx.shared import Cm
from typing import Dict, Any, Tuple
from pathlib import Path

from paragraph_classifier import ParagraphClassifier
from paragraph_formatter import ParagraphFormatter
from statistics_tracker import StatisticsTracker
from document_state import logger

class VKRFormatter:
    """Основной класс для форматирования ВКР"""
    
    def __init__(self, requirements: Dict[str, Any]):
        self.requirements = requirements
        self.classifier = ParagraphClassifier(requirements)
        self.formatter = ParagraphFormatter(requirements)
        self.stats = StatisticsTracker()
    
    def format_document(self, input_path: str, output_path: str) -> bool:
        """Форматирует документ"""
        try:
            logger.info(f"📂 Начинаем форматирование: {input_path}")
            logger.info(f"💾 Выходной путь: {output_path}")
            
            # Проверяем входной файл
            input_file = Path(input_path)
            if not input_file.exists():
                logger.error(f"❌ Входной файл не существует: {input_path}")
                return False
            
            # Загружаем документ
            logger.info("📖 Загружаем документ...")
            doc = Document(input_path)
            logger.info(f"✅ Документ загружен, параграфов: {len(doc.paragraphs)}")
            
            # Применяем глобальные настройки
            logger.info("⚙️  Применяем глобальные настройки...")
            self._apply_global_settings(doc)
            
            # Обрабатываем параграфы
            logger.info("🔄 Обрабатываем параграфы...")
            self._process_all_paragraphs(doc)
            
            # Сохраняем результат
            logger.info(f"💾 Сохраняем документ в: {output_path}")
            doc.save(output_path)
            
            # Проверяем результат
            output_file = Path(output_path)
            if output_file.exists():
                logger.info(f"✅ Файл создан, размер: {output_file.stat().st_size} байт")
            else:
                logger.error(f"❌ Файл НЕ создался: {output_path}")
                return False
            
            final_stats = self.get_statistics()
            logger.info(f"🎉 Форматирование завершено! Статистика: {final_stats}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка форматирования: {e}")
            import traceback
            logger.error(f"Полная трассировка: {traceback.format_exc()}")
            return False
    
    def _apply_global_settings(self, doc: Document) -> None:
        """Применяет глобальные настройки документа"""
        try:
            margins = self.requirements["base_formatting"]["margins_cm"]
            
            for section in doc.sections:
                section.top_margin = Cm(margins["top"])
                section.bottom_margin = Cm(margins["bottom"])
                section.left_margin = Cm(margins["left"])
                section.right_margin = Cm(margins["right"])
            
            logger.info(f"Применены поля: {margins}")
            
        except Exception as e:
            logger.error(f"Ошибка применения глобальных настроек: {e}")
            self.stats.increment('errors')
    
    def _process_all_paragraphs(self, doc: Document) -> None:
        """Обрабатывает все параграфы документа"""
        logger.info("Начинаем обработку параграфов...")
        
        for i, paragraph in enumerate(doc.paragraphs):
            self.stats.increment('total_paragraphs')
            
            try:
                text = paragraph.text.strip()
                paragraph_type = self.classifier.classify_paragraph(text)
                
                # Логируем непустые параграфы
                if text:
                    logger.debug(f"Параграф {i+1}: тип='{paragraph_type}', текст='{text[:100]}{'...' if len(text) > 100 else ''}'")
                
                # Применяем форматирование
                self._apply_paragraph_formatting(paragraph, paragraph_type, i+1, text)
                
            except Exception as e:
                logger.warning(f"Ошибка обработки параграфа {i+1}: {e}")
                self.stats.increment('errors')
        
        final_stats = self.stats.stats
        logger.info(f"Обработка параграфов завершена. Статистика: {final_stats}")
    
    def _apply_paragraph_formatting(self, paragraph, paragraph_type: str, index: int, text: str) -> None:
        """Применяет форматирование к параграфу"""
        if paragraph_type == "skip":
            self.stats.increment('skipped_paragraphs')
            logger.info(f"⏭️  ПРОПУСК #{index}: {text[:60]}{'...' if len(text) > 60 else ''}")
            
        elif paragraph_type == "h1":
            self.formatter.format_h1(paragraph)
            self.stats.increment('h1_formatted')
            logger.info(f"📝 H1 #{index}: {text[:40]}...")
            
        elif paragraph_type == "h2":
            self.formatter.format_h2(paragraph)
            self.stats.increment('h2_formatted')
            logger.info(f"📄 H2 #{index}: {text[:40]}...")
            
        elif paragraph_type == "list":
            self.formatter.format_list(paragraph)
            self.stats.increment('lists_formatted')
            logger.debug(f"📋 СПИСОК #{index}: {text[:40]}...")
            
        else:  # regular
            self.formatter.format_regular(paragraph)
            self.stats.increment('regular_formatted')
    
    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику обработки"""
        return self.stats.get_statistics(self.classifier.get_state())

def format_vkr_document(input_path: str, requirements: Dict[str, Any], output_path: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Форматирует ВКР согласно требованиям
    
    Args:
        input_path: путь к исходному файлу ВКР
        requirements: словарь требований
        output_path: путь к результирующему файлу
        
    Returns:
        tuple: (успех, статистика)
    """
    formatter = VKRFormatter(requirements)
    success = formatter.format_document(input_path, output_path)
    stats = formatter.get_statistics()
    
    return success, stats 