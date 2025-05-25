from logger_config import stub_logger as logger


def get_default_vkr_requirements():
    """
    Заглушка: возвращает стандартные требования ГОСТ для ВКР
    Вместо анализа через ИИ - просто возвращаем фиксированные требования
    """

    return {
        # 1-2. Секции для пропуска
        "skip_sections": {
            "title_page_keywords": [
                "ДИПЛОМНАЯ РАБОТА",
                "ВЫПУСКНАЯ КВАЛИФИКАЦИОННАЯ РАБОТА",
                "МИНИСТЕРСТВО ОБРАЗОВАНИЯ"
            ],
            "task_keywords": [
                "ЗАДАНИЕ НА ВЫПУСКНУЮ",
                "ТЕХНИЧЕСКОЕ ЗАДАНИЕ",
                "ЗАДАНИЕ НА ДИПЛОМНУЮ"
            ],
            "calendar_keywords": [
                "КАЛЕНДАРНЫЙ ПЛАН",
                "КАЛЕНДАРНО-ТЕМАТИЧЕСКИЙ ПЛАН"
            ],
            "definitions_keywords": [
                "ОПРЕДЕЛЕНИЯ",
                "ОБОЗНАЧЕНИЯ И СОКРАЩЕНИЯ",
                "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ"
            ]
        },

        # 3. Базовые требования для всего ВКР
        "base_formatting": {
            "font_name": "Times New Roman",
            "font_size": 14,
            "line_spacing": 1.5,
            "text_alignment": "justify",
            "paragraph_indent_cm": 1.25,
            "margins_cm": {
                "top": 2.0,
                "bottom": 2.0,
                "left": 3.0,
                "right": 1.5
            }
        },

        # 4. Заголовки H1 (главы)
        "h1_formatting": {
            "font_name": "Times New Roman",
            "font_size": 16,
            "font_weight": "bold",
            "text_transform": "uppercase",
            "alignment": "center",
            "page_break_before": True,
            "space_before_pt": 0,
            "space_after_pt": 18,
            "detection_patterns": [
                r"^\d+\.\s*[А-ЯЁ\s]+$",           # "1. ВВЕДЕНИЕ"
                r"^ГЛАВА\s+\d+",                   # "ГЛАВА 1"
                r"^(ВВЕДЕНИЕ|ЗАКЛЮЧЕНИЕ|РЕФЕРАТ)$",  # специальные разделы
                r"^[IVX]+\.\s*[А-ЯЁ\s]+$"        # "I. ВВЕДЕНИЕ"
            ]
        },

        # 5. Заголовки H2 (подразделы)
        "h2_formatting": {
            "font_name": "Times New Roman",
            "font_size": 14,
            "font_weight": "bold",
            "text_transform": "none",
            "alignment": "left",
            "page_break_before": False,
            "space_before_pt": 12,
            "space_after_pt": 6,
            "paragraph_indent_cm": 2,
            "detection_patterns": [
                r"^\d+\.\d+\.?\s+[А-Яа-яёЁ]",     # "1.1. Подраздел"
                r"^\d+\.\d+\s+[А-ЯЁ\s]+$"        # "1.1 ПОДРАЗДЕЛ"
            ]
        },

        # 6. Специальные разделы
        "special_sections": {
            "abstract": {
                "font_name": "Times New Roman",
                "font_size": 14,
                "alignment": "justify",
                "line_spacing": 1.5,
                "paragraph_indent_cm": 1.25,
                "keywords": ["РЕФЕРАТ", "ABSTRACT"]
            },
            "annotation": {
                "font_name": "Times New Roman",
                "font_size": 14,
                "alignment": "justify",
                "line_spacing": 1.5,
                "paragraph_indent_cm": 1.25,
                "keywords": ["ANNOTATION", "АННОТАЦИЯ"]
            },
            "introduction": {
                "font_name": "Times New Roman",
                "font_size": 14,
                "alignment": "justify",
                "line_spacing": 1.5,
                "paragraph_indent_cm": 1.25,
                "keywords": ["ВВЕДЕНИЕ", "INTRODUCTION"]
            },
            "conclusion": {
                "font_name": "Times New Roman",
                "font_size": 14,
                "alignment": "justify",
                "line_spacing": 1.5,
                "paragraph_indent_cm": 1.25,
                "keywords": ["ЗАКЛЮЧЕНИЕ", "CONCLUSION"]
            }
        },

        # 7. Содержание
        "table_of_contents": {
            "title": "СОДЕРЖАНИЕ",
            "font_name": "Times New Roman",
            "font_size": 14,
            "alignment": "left",
            "line_spacing": 1.0,
            "dot_leader": True,
            "keywords": ["СОДЕРЖАНИЕ", "ОГЛАВЛЕНИЕ", "CONTENTS"]
        },

        # 8. Список литературы
        "references": {
            "title": "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
            "font_name": "Times New Roman",
            "font_size": 14,
            "alignment": "justify",
            "line_spacing": 1.0,
            "paragraph_indent_cm": 0,
            "hanging_indent_cm": 1.0,
            "keywords": [
                "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
                "СПИСОК ЛИТЕРАТУРЫ",
                "БИБЛИОГРАФИЧЕСКИЙ СПИСОК"
            ]
        },

        # 9. Таблицы
        "tables": {
            "caption": {
                "position": "above",
                "alignment": "left",
                "font_name": "Times New Roman",
                "font_size": 14,
                "format": "Таблица {chapter}.{number} - {title}"
            },
            "content": {
                "font_name": "Times New Roman",
                "font_size": 12,
                "alignment": "center",
                "line_spacing": 1.0
            },
            "spacing": {
                "before_pt": 12,
                "after_pt": 6
            },
            "detection_patterns": [
                r"Таблица\s+\d+",
                r"Табл\.\s+\d+"
            ]
        },

        # 10. Рисунки
        "figures": {
            "caption": {
                "position": "below",
                "alignment": "center",
                "font_name": "Times New Roman",
                "font_size": 14,
                "format": "Рисунок {chapter}.{number} - {title}"
            },
            "alignment": "center",
            "spacing": {
                "before_pt": 6,
                "after_pt": 12
            },
            "detection_patterns": [
                r"Рисунок\s+\d+",
                r"Рис\.\s+\d+",
                r"Figure\s+\d+"
            ]
        },

        # 11. Формулы
        "formulas": {
            "alignment": "center",
            "numbering": {
                "position": "right",
                "format": "({chapter}.{number})"
            },
            "spacing": {
                "before_pt": 6,
                "after_pt": 6
            },
            "variables_explanation": {
                "required": True,
                "format": "где {variable} – {description};",
                "alignment": "left",
                "indent_cm": 2.0
            },
            "detection_patterns": [
                r"\(\d+\.\d+\)",
                r"\(\d+\)"
            ]
        },

        # 12. Ссылки на источники
        "citations": {
            "format": "[{number}]",
            "multiple_format": "[{start}-{end}]",
            "page_reference": "[{number}, с. {page}]",
            "detection_patterns": [
                r"\[\d+\]",
                r"\[\d+-\d+\]",
                r"\[\d+,\s*с\.\s*\d+\]"
            ]
        },

        # 13. Нумерация страниц
        "page_numbering": {
            "style": "arabic",
            "position": "bottom_center",
            "font_name": "Times New Roman",
            "font_size": 12,
            "start_from": 1,
            "exclude_title_page": True,
            "margin_from_edge_cm": 2.0
        },

        # Списки (из предыдущего обсуждения)
        "lists": {
            "bullet_lists": {
                "marker": "–",
                "indent_cm": 1.25,
                "punctuation": {
                    "item_ending": ";",
                    "last_item_ending": "."
                },
                "font": {
                    "name": "Times New Roman",
                    "size": 14,
                    "line_spacing": 1.5
                },
                "alignment": "justify",
                "detection_patterns": [
                    r"^\s*[-–—]\s+",
                    r"^\s*\d+\)\s+",
                    r"^\s*[а-я]\)\s+"
                ]
            }
        }
    }


def analyze_requirements_stub(requirements_file_path: str):
    """
    Заглушка для анализа требований
    Игнорирует файл и возвращает стандартные требования
    """
    logger.info(f"🔮 Анализируем файл требований: {requirements_file_path}")
    logger.info("📋 Возвращаем стандартные требования ГОСТ...")

    return get_default_vkr_requirements()
