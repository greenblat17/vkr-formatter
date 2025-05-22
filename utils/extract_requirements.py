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
    """Извлекает требования к форматированию заголовков 1 уровня из .docx файла"""
    
    # Считываем требования из .docx
    doc = Document(doc_path)
    full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    # Промпт с фокусом на заголовки 1 уровня
    prompt = f"""Вот текст требований к оформлению дипломной работы:
---
{full_text}
---

Извлеки ТОЛЬКО требования к заголовкам 1 уровня (главам, разделам) и преобразуй в JSON.
Обрати внимание на:
- Шрифт заголовков
- Размер шрифта заголовков  
- Выравнивание заголовков (по центру, слева и т.д.)
- Должны ли заголовки быть жирными
- Должны ли заголовки быть заглавными буквами
- Отступы до/после заголовков

Верни только JSON без пояснений и markdown."""

    # Упрощенная схема только для заголовков 1 уровня
    function_schema = {
        "name": "h1_formatting_rules",
        "description": "Извлечение требований к форматированию заголовков 1 уровня",
        "parameters": {
            "type": "object",
            "properties": {
                "font_name": {
                    "type": "string",
                    "description": "Название шрифта для основного текста"
                },
                "font_size_main": {
                    "type": "integer",
                    "description": "Размер шрифта основного текста"
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
                        }
                    },
                    "required": ["font_name", "font_size", "alignment", "bold", "uppercase"]
                }
            },
            "required": ["font_name", "font_size_main", "h1_formatting"]
        }
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            tools=[{"type": "function", "function": function_schema}],
            tool_choice="required",
        )

        # Логируем ответ
        print("=== GPT RESPONSE FOR H1 FORMATTING ===")
        print(response)

        args = response.choices[0].message.tool_calls[0].function.arguments
        print("✅ EXTRACTED H1 JSON:")
        print(args)

        return json.loads(args)

    except Exception as e:
        print(f"❌ Ошибка вызова OpenAI: {e}")
        
        # Возвращаем значения по умолчанию в случае ошибки
        return {
            "font_name": "Times New Roman",
            "font_size_main": 14,
            "h1_formatting": {
                "font_name": "Times New Roman",
                "font_size": 16,
                "alignment": "center",
                "bold": True,
                "uppercase": True,
                "space_before": 12,
                "space_after": 12
            }
        }