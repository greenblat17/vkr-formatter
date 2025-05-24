from docx import Document
from openai import OpenAI
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

client = OpenAI(api_key=api_key)


def extract_requirements_from_docx(doc_path):
    """Извлекает требования к форматированию: глобальные настройки + заголовки 1 уровня"""

    # Считываем требования из .docx
    doc = Document(doc_path)
    full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    # Промпт для извлечения глобальных настроек и H1
    prompt = f"""Вот текст требований к оформлению дипломной работы:
---
{full_text}
---

Извлеки требования и раздели их на две группы:

1. ГЛОБАЛЬНЫЕ НАСТРОЙКИ (применяются ко всему документу):
   - Поля страницы (отступы сверху, снизу, слева, справа)
   - Основной шрифт документа
   - Размер основного шрифта
   - Междустрочный интервал
   - Отступ первой строки абзаца
   - Выравнивание основного текста

2. ЗАГОЛОВКИ 1 УРОВНЯ (главы, разделы):
   - Шрифт заголовков
   - Размер шрифта заголовков  
   - Выравнивание заголовков
   - Жирность заголовков
   - Заглавные буквы
   - Отступы до/после заголовков
   - Должны ли заголовки начинаться с новой страницы

Верни только JSON без пояснений и markdown."""

    # Расширенная схема с глобальными настройками + H1
    function_schema = {
        "name": "document_formatting_rules",
        "description": "Извлечение глобальных настроек документа и требований к заголовкам 1 уровня",
        "parameters": {
            "type": "object",
            "properties": {
                "global_settings": {
                    "type": "object",
                    "properties": {
                        "margins": {
                            "type": "object",
                            "properties": {
                                "top": {"type": "number", "description": "Верхнее поле в см"},
                                "bottom": {"type": "number", "description": "Нижнее поле в см"},
                                "left": {"type": "number", "description": "Левое поле в см"},
                                "right": {"type": "number", "description": "Правое поле в см"}
                            }
                        },
                        "font_name": {
                            "type": "string",
                            "description": "Основной шрифт документа"
                        },
                        "font_size": {
                            "type": "integer",
                            "description": "Размер основного шрифта"
                        },
                        "line_spacing": {
                            "type": "number",
                            "description": "Междустрочный интервал (1.0, 1.5, 2.0)"
                        },
                        "paragraph_indent": {
                            "type": "number",
                            "description": "Отступ первой строки абзаца в см"
                        },
                        "text_alignment": {
                            "type": "string",
                            "enum": ["left", "center", "right", "justify"],
                            "description": "Выравнивание основного текста"
                        }
                    },
                    "required": ["font_name", "font_size", "margins"]
                },
                "h1_formatting": {
                    "type": "object",
                    "properties": {
                        "font_name": {
                            "type": "string",
                            "description": "Шрифт заголовков 1 уровня"
                        },
                        "font_size": {
                            "type": "integer",
                            "description": "Размер шрифта заголовков 1 уровня"
                        },
                        "alignment": {
                            "type": "string",
                            "enum": ["left", "center", "right", "justify"],
                            "description": "Выравнивание заголовков"
                        },
                        "bold": {
                            "type": "boolean",
                            "description": "Должны ли заголовки быть жирными"
                        },
                        "uppercase": {
                            "type": "boolean",
                            "description": "Должны ли заголовки быть заглавными буквами"
                        },
                        "space_before": {
                            "type": "integer",
                            "description": "Отступ перед заголовком в пунктах"
                        },
                        "space_after": {
                            "type": "integer",
                            "description": "Отступ после заголовка в пунктах"
                        },
                        "page_break_before": {
                            "type": "boolean",
                            "description": "Должны ли заголовки начинаться с новой страницы"
                        }
                    },
                    "required": ["font_name", "font_size", "alignment", "bold", "uppercase", "page_break_before"]
                }
            },
            "required": ["global_settings", "h1_formatting"]
        }
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            tools=[{"type": "function", "function": function_schema}],
            tool_choice="required",
        )

        # Логируем ответ
        print("=== GPT RESPONSE FOR GLOBAL + H1 FORMATTING ===")
        print(response)

        args = response.choices[0].message.tool_calls[0].function.arguments
        print("✅ EXTRACTED GLOBAL + H1 JSON:")
        print(args)

        return json.loads(args)

    except Exception as e:
        print(f"❌ Ошибка вызова OpenAI: {e}")
