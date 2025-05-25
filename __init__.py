"""
VKR Formatter - Модульная система форматирования ВКР согласно ГОСТ

Основные компоненты:
- FormattingConstants: Константы форматирования
- DocumentState: Управление состоянием документа
- ContentDetector: Определение типов контента
- ParagraphClassifier: Классификация параграфов
- ParagraphFormatter: Форматирование параграфов
- StatisticsTracker: Отслеживание статистики
- VKRFormatter: Основной класс форматтера
"""

from .formatting_constants import FormattingConstants
from .document_state import DocumentState
from .content_detector import ContentDetector
from .paragraph_classifier import ParagraphClassifier
from .paragraph_formatter import ParagraphFormatter
from .statistics_tracker import StatisticsTracker
from .vkr_formatter import VKRFormatter, format_vkr_document

__version__ = "2.0.0"
__author__ = "VKR Formatter Team"

__all__ = [
    "FormattingConstants",
    "DocumentState",
    "ContentDetector",
    "ParagraphClassifier",
    "ParagraphFormatter",
    "StatisticsTracker",
    "VKRFormatter",
    "format_vkr_document"
]
