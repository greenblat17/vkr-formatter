"""
Централизованная конфигурация логирования для VKR Formatter
"""

import logging
import colorlog
from typing import Optional


def setup_colored_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    info_color: str = "green"
) -> colorlog.ColoredFormatter:
    """
    Создает и настраивает цветной логгер
    
    Args:
        name: имя логгера
        level: уровень логирования
        format_string: кастомный формат (опционально)
        info_color: цвет для INFO сообщений
        
    Returns:
        настроенный логгер
    """
    
    # Базовый формат если не указан кастомный
    if format_string is None:
        if len(name) <= 8:
            format_string = '%(log_color)s%(asctime)s - %(name)-8s - %(levelname)-8s%(reset)s %(message)s'
        else:
            format_string = '%(log_color)s%(asctime)s - %(name)-12s - %(levelname)-8s%(reset)s %(message)s'
    
    # Создаем цветной форматтер
    color_formatter = colorlog.ColoredFormatter(
        format_string,
        datefmt='%H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': info_color,
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    
    # Настраиваем handler
    handler = colorlog.StreamHandler()
    handler.setFormatter(color_formatter)
    
    # Настраиваем логгер
    logger = colorlog.getLogger(name)
    logger.setLevel(level)
    
    # Очищаем существующие handlers чтобы избежать дублирования
    logger.handlers.clear()
    logger.addHandler(handler)
    
    # Предотвращаем передачу в родительские логгеры
    logger.propagate = False
    
    return logger


def get_formatter_logger() -> colorlog.ColoredFormatter:
    """Получить логгер для форматтера ВКР"""
    return setup_colored_logger("VKR-Format", info_color="green")


def get_api_logger() -> colorlog.ColoredFormatter:
    """Получить логгер для API"""
    return setup_colored_logger("API", info_color="light_blue")


def get_stub_logger() -> colorlog.ColoredFormatter:
    """Получить логгер для заглушек"""
    return setup_colored_logger("STUB", info_color="purple")


# Предустановленные логгеры для удобства
formatter_logger = get_formatter_logger()
api_logger = get_api_logger()
stub_logger = get_stub_logger()