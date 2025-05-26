import logging
from typing import Dict
import colorlog

# Настройка логирования


def setup_colored_logging():
    """Настраивает цветное логирование"""
    color_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(levelname)-8s%(reset)s %(message)s',
        datefmt='%H:%M:%S',
        log_colors={
            'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow',
            'ERROR': 'red', 'CRITICAL': 'red,bg_white',
        },
        style='%'
    )

    handler = colorlog.StreamHandler()
    handler.setFormatter(color_formatter)

    logger = colorlog.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger


logger = setup_colored_logging()


class DocumentState:
    """Управляет состоянием обработки документа"""

    def __init__(self):
        self.in_title_section = True
        self.in_contents_section = False
        self.in_references_section = False
        self.found_main_content = False
        self.pages_skipped = 0

    def start_contents_section(self):
        """Начинает раздел содержания"""
        self.in_contents_section = True
        logger.info("📑 Переход в режим содержания")

    def start_main_content(self):
        """Начинает основное содержание"""
        self.in_title_section = False
        self.in_contents_section = False
        self.in_references_section = False
        self.found_main_content = True
        logger.info("🟢 Переход к основному содержанию")

    def start_references_section(self):
        """Начинает раздел списка литературы"""
        self.in_references_section = True
        logger.info("📚 Переход в режим списка литературы")

    def is_in_service_section(self) -> bool:
        """Находимся ли в служебной секции"""
        return self.in_title_section or self.in_contents_section

    def get_state_info(self) -> Dict[str, bool]:
        """Возвращает информацию о текущем состоянии"""
        return {
            'in_title_section': self.in_title_section,
            'in_contents_section': self.in_contents_section,
            'in_references_section': self.in_references_section,
            'found_main_content': self.found_main_content
        }
