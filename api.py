from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import tempfile
import shutil
import logging
from pathlib import Path
import json
import os
from datetime import datetime
from logger_config import api_logger as logger

# Импорты наших модулей
from requirements_stub import analyze_requirements_stub
from vkr_formatter import format_vkr_document
from document_validator import validate_vkr_document

# Pydantic модели для Swagger документации
class ServiceInfo(BaseModel):
    """Информация о сервисе"""
    service: str = Field(..., description="Название сервиса")
    version: str = Field(..., description="Версия API")
    description: str = Field(..., description="Описание сервиса")
    documentation: str = Field(..., description="Ссылка на документацию")
    features: List[str] = Field(..., description="Основные возможности")

class ValidationSummary(BaseModel):
    """Краткая сводка валидации"""
    total_issues: int = Field(..., description="Общее количество проблем")
    errors: int = Field(..., description="Количество критических ошибок")
    warnings: int = Field(..., description="Количество предупреждений")
    info: int = Field(..., description="Количество информационных сообщений")
    score: int = Field(..., description="Оценка соответствия (0-100)")

class ValidationIssueModel(BaseModel):
    """Модель проблемы валидации"""
    type: str = Field(..., description="Тип проблемы: error, warning, info")
    category: str = Field(..., description="Категория: margins, fonts, headings, etc.")
    description: str = Field(..., description="Описание проблемы")
    location: str = Field(..., description="Местоположение (номер параграфа + превью)")
    expected: str = Field(..., description="Ожидаемое значение")
    actual: str = Field(..., description="Фактическое значение")
    suggestion: str = Field(default="", description="Рекомендация по исправлению")

class ValidationStatistics(BaseModel):
    """Статистика документа"""
    total_paragraphs: int = Field(..., description="Общее количество параграфов")
    total_tables: int = Field(..., description="Количество таблиц")
    total_sections: int = Field(..., description="Количество секций")
    heading_counts: Dict[str, int] = Field(..., description="Количество заголовков по уровням")
    list_items: int = Field(..., description="Количество элементов списков")
    regular_paragraphs: int = Field(..., description="Количество обычных параграфов")
    empty_paragraphs: int = Field(default=0, description="Количество пустых параграфов")

class ValidationResponse(BaseModel):
    """Ответ валидации документа"""
    validation_passed: bool = Field(..., description="Прошла ли валидация успешно")
    summary: ValidationSummary = Field(..., description="Краткая сводка")
    statistics: ValidationStatistics = Field(..., description="Статистика документа")
    issues_by_category: Dict[str, List[ValidationIssueModel]] = Field(..., description="Проблемы по категориям")
    timestamp: str = Field(..., description="Время проведения валидации")

class FormatResponse(BaseModel):
    """Ответ форматирования документа"""
    success: bool = Field(..., description="Успешность форматирования")
    message: str = Field(..., description="Сообщение о результате")
    filename: str = Field(..., description="Имя выходного файла")
    stats: Dict[str, Any] = Field(default={}, description="Статистика форматирования")
    timestamp: str = Field(..., description="Время форматирования")

class ServiceStats(BaseModel):
    """Статистика сервиса"""
    total_processed: int = Field(..., description="Всего обработано документов")
    successful: int = Field(..., description="Успешно обработано")
    failed: int = Field(..., description="Обработано с ошибками")
    validation_requests: int = Field(default=0, description="Запросов валидации")
    format_requests: int = Field(default=0, description="Запросов форматирования")
    last_processed: Optional[str] = Field(None, description="Время последней обработки")
    uptime_start: str = Field(..., description="Время запуска сервиса")

class RequirementsResponse(BaseModel):
    """Ответ с требованиями ГОСТ"""
    status: str = Field(..., description="Статус запроса")
    message: str = Field(..., description="Описание")
    version: str = Field(..., description="Версия требований ГОСТ")
    categories: List[str] = Field(..., description="Категории требований")
    requirements_preview: Dict[str, Any] = Field(..., description="Превью основных требований")

class ErrorResponse(BaseModel):
    """Модель ошибки"""
    detail: str = Field(..., description="Описание ошибки")
    error_code: Optional[str] = Field(None, description="Код ошибки")
    timestamp: str = Field(..., description="Время ошибки")

# Создаем приложение с расширенной конфигурацией
app = FastAPI(
    title="🎓 VKR Formatter API",
    description="""
    ## 📋 Профессиональная система валидации и форматирования ВКР
    
    **Версия 2.0** с детальными отчетами об ошибках!
    
    ### 🎯 Основные возможности:
    
    - **🔍 Валидация**: Детальная проверка соответствия ГОСТ с конкретными рекомендациями
    - **✨ Форматирование**: Автоматическое исправление документа по требованиям
    - **📊 Аналитика**: Подробная статистика и оценка качества документа
    - **🏷️ Категоризация**: Группировка проблем по типам (поля, шрифты, заголовки, etc.)
    
    ### 📖 Поддерживаемые элементы:
    
    - Заголовки всех уровней (H1-H4)
    - Поля документа и ориентация страницы  
    - Шрифты и размеры
    - Отступы и выравнивание
    - Таблицы и списки
    - Структура документа
    
    ### 🎖️ Система оценки:
    
    - **90-100**: ✅ Отлично (соответствует ГОСТ)
    - **70-89**: 🟡 Хорошо (мелкие замечания)
    - **50-69**: ⚠️ Удовлетворительно (требуются исправления)
    - **<50**: ❌ Неудовлетворительно (много нарушений)
    
    ---
    
    **💡 Рекомендуемый workflow:**
    1. Сначала валидируйте документ (`/validate`)
    2. Изучите детальный отчет с ошибками
    3. При необходимости отформатируйте (`/format`)
    4. Повторно проверьте результат
    
    **🔧 Встроенные требования ГОСТ:** Система работает "из коробки" без дополнительных файлов!
    """,
    version="2.0.0",
    contact={
        "name": "VKR Formatter Support",
        "email": "support@vkr-formatter.dev",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    tags_metadata=[
        {
            "name": "validation",
            "description": "🔍 Валидация документов ВКР с детальными отчетами об ошибках",
        },
        {
            "name": "formatting", 
            "description": "✨ Автоматическое форматирование документов по ГОСТ",
        },
        {
            "name": "requirements",
            "description": "📋 Просмотр встроенных требований ГОСТ",
        },
        {
            "name": "service",
            "description": "⚙️ Информация о сервисе и статистика",
        },
    ],
    openapi_tags=[
        {
            "name": "validation",
            "description": "Детальная валидация с конкретными рекомендациями",
        },
        {
            "name": "formatting",
            "description": "Автоматическое исправление форматирования",
        },
        {
            "name": "requirements", 
            "description": "Встроенные требования ГОСТ",
        },
        {
            "name": "service",
            "description": "Информация о сервисе",
        },
    ]
)

# Добавляем поддержку CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники (для разработки)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все HTTP методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

# Расширенная статистика
stats = {
    "total_processed": 0,
    "successful": 0,
    "failed": 0,
    "validation_requests": 0,
    "format_requests": 0,
    "last_processed": None,
    "uptime_start": datetime.now().isoformat()
}

def cleanup_temp_file(file_path: str):
    """Удаляет временный файл"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Временный файл удален: {file_path}")
    except Exception as e:
        logger.warning(f"Не удалось удалить временный файл {file_path}: {e}")

@app.get("/", 
         response_model=ServiceInfo,
         tags=["service"],
         summary="📋 Информация о сервисе",
         description="Возвращает подробную информацию о VKR Formatter API с описанием всех возможностей")
async def root() -> ServiceInfo:
    """
    ## 📋 Базовая информация о сервисе
    
    Возвращает:
    - Название и версию API
    - Описание возможностей  
    - Список основных функций
    - Ссылки на документацию
    """
    return ServiceInfo(
        service="VKR Formatter API",
        version="2.0.0",
        description="Профессиональная система валидации и форматирования ВКР по ГОСТ с детальными отчетами",
        documentation="/docs",
        features=[
            "🔍 Детальная валидация с конкретными рекомендациями",
            "✨ Автоматическое форматирование документов",
            "📊 Система оценки качества (0-100 баллов)",
            "🏷️ Категоризация проблем по типам",
            "📋 Встроенные требования ГОСТ",
            "🎯 Пошаговые инструкции по исправлению",
            "📈 Статистика и аналитика документов"
        ]
    )

@app.get("/requirements", 
         response_model=RequirementsResponse,
         tags=["requirements"],
         summary="📋 Встроенные требования ГОСТ",
         description="Возвращает превью встроенных требований ГОСТ, которые используются для валидации")
async def get_default_requirements() -> RequirementsResponse:
    """
    ## 📋 Просмотр встроенных требований ГОСТ
    
    Система использует встроенные требования ГОСТ для ВКР, которые включают:
    
    - **Базовое форматирование**: шрифты, поля, отступы
    - **Заголовки**: H1-H4 с правильным оформлением  
    - **Списки**: отступы, маркеры, пунктуация
    - **Таблицы**: подписи, выравнивание, заголовки
    - **Специальные разделы**: введение, заключение, список литературы
    
    **💡 Преимущество**: Не нужно искать файл требований - все уже встроено!
    """
    try:
        requirements = analyze_requirements_stub("dummy_path")
        
        # Создаем превью основных требований
        preview = {
            "базовое_форматирование": {
                "шрифт": requirements["base_formatting"]["font_name"],
                "размер": f"{requirements['base_formatting']['font_size']} пт",
                "межстрочный_интервал": requirements["base_formatting"]["line_spacing"],
                "поля_см": requirements["base_formatting"]["margins_cm"]
            },
            "заголовки": {
                "H1": f"{requirements['h1_formatting']['font_size']} пт, жирный, по центру",
                "H2": f"{requirements['h2_formatting']['font_size']} пт, жирный, слева",
                "H3": f"{requirements['h3_formatting']['font_size']} пт, обычный, слева"
            },
            "списки": {
                "отступ": f"{requirements['lists']['bullet_lists']['indent_cm']} см",
                "маркер": requirements['lists']['bullet_lists']['marker']
            }
        }
        
        return RequirementsResponse(
            status="success",
            message="Встроенные требования ГОСТ для ВКР",
            version="ГОСТ 7.32-2017",
            categories=list(requirements.keys()),
            requirements_preview=preview
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка получения требований: {str(e)}"
        )

@app.get("/stats", 
         response_model=ServiceStats,
         tags=["service"],
         summary="📊 Статистика сервиса",
         description="Возвращает подробную статистику использования API")
async def get_stats() -> ServiceStats:
    """
    ## 📊 Статистика использования API
    
    Показывает:
    - Общее количество обработанных документов
    - Соотношение успешных и неудачных операций
    - Количество запросов валидации и форматирования
    - Время работы сервиса
    """
    return ServiceStats(**stats)

@app.post("/format",
         response_class=FileResponse,
         tags=["formatting"],
         summary="✨ Автоматическое форматирование ВКР",
         description="Форматирует документ ВКР по требованиям ГОСТ и возвращает исправленный файл",
         responses={
             200: {
                 "description": "Успешно отформатированный документ",
                 "content": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document": {}},
                 "headers": {
                     "X-Format-Stats": {"description": "JSON статистика форматирования"},
                     "X-Requirements-Source": {"description": "Источник требований: file или default"},
                     "X-Version": {"description": "Версия API"}
                 }
             },
             400: {"model": ErrorResponse, "description": "Неверный формат файла"},
             500: {"model": ErrorResponse, "description": "Ошибка форматирования"}
         })
async def format_vkr(
    background_tasks: BackgroundTasks,
    vkr: UploadFile = File(..., description="📄 Файл ВКР в формате .docx для автоматического форматирования"),
    requirements: Optional[UploadFile] = File(
        default=None, description="📋 Файл требований (необязательно - используются встроенные ГОСТ)")
):
    """
    ## ✨ Автоматическое форматирование документа ВКР
    
    **Что делает этот endpoint:**
    - Автоматически исправляет форматирование документа по ГОСТ
    - Применяет правильные шрифты, отступы, поля
    - Форматирует заголовки всех уровней (H1-H4)
    - Исправляет списки и таблицы
    - Возвращает готовый к печати документ
    
    **Поддерживаемые элементы:**
    - 📋 **Заголовки**: H1 (16пт, жирный, по центру), H2-H4 (14пт, различное выравнивание)
    - 📝 **Параграфы**: красная строка 1.25см, выравнивание по ширине
    - 📊 **Поля документа**: верх/низ 2см, лево 3см, право 1.5см  
    - 🔤 **Шрифты**: Times New Roman, правильные размеры
    - 📌 **Списки**: автоматические отступы и маркеры
    - 📄 **Интервалы**: 1.5 между строками, правильные отступы между элементами
    
    **Специальные возможности:**
    - 🎯 **Умное распознавание**: автоматически определяет тип элементов
    - 🚫 **Пропуск служебных страниц**: титульный лист, задание, календарный план
    - 📊 **Статистика в заголовках**: количество обработанных элементов
    
    **💡 Когда использовать:**
    - Документ имеет много ошибок форматирования (оценка < 70)
    - Нужно быстро привести документ к ГОСТ
    - Исходное форматирование сильно отличается от требований
    
    **⚠️ Важно:**
    - Создается новый файл (исходный не изменяется)
    - Рекомендуется проверить результат валидацией
    - Сложные элементы могут потребовать ручной доработки
    """
    
    # Обновляем статистику
    stats["total_processed"] += 1
    stats["format_requests"] += 1
    stats["last_processed"] = datetime.now().isoformat()

    # Валидация формата файла
    if not vkr.filename.endswith(('.docx', '.doc')):
        raise HTTPException(
            status_code=400,
            detail="Файл ВКР должен быть в формате .docx или .doc"
        )

    # Создаем временную директорию для обработки
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Пути к файлам
        vkr_path = tmpdir_path / "input_vkr.docx"
        output_path = tmpdir_path / "formatted_vkr.docx"

        try:
            logger.info(f"📁 Начинаем форматирование ВКР: {vkr.filename}")

            # Сохраняем файл ВКР
            with open(vkr_path, "wb") as f:
                shutil.copyfileobj(vkr.file, f)
            logger.info(f"💾 ВКР сохранен: {vkr_path}")

            # Используем встроенные требования ГОСТ
            logger.info("📋 Используем встроенные требования ГОСТ")
            vkr_requirements = analyze_requirements_stub("default")

            # Форматируем документ
            logger.info("🚀 Применяем автоматическое форматирование...")
            success, format_stats = format_vkr_document(
                str(vkr_path),
                vkr_requirements,
                str(output_path)
            )

            logger.info(f"📊 Результат форматирования: success={success}")

            if not success:
                stats["failed"] += 1
                raise HTTPException(
                    status_code=500,
                    detail="Ошибка при форматировании документа"
                )

            # Проверяем результат
            if not output_path.exists():
                stats["failed"] += 1
                raise HTTPException(
                    status_code=500,
                    detail="Отформатированный файл не был создан"
                )

            # Копируем файл в безопасное временное место
            final_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
            shutil.copy2(output_path, final_temp_file.name)
            final_temp_file.close()

            stats["successful"] += 1

            # Генерируем имя выходного файла
            original_name = Path(vkr.filename).stem
            output_filename = f"{original_name}_formatted.docx"

            logger.info(f"🎉 Форматирование завершено: {output_filename}")

        except HTTPException:
            raise
        except Exception as e:
            stats["failed"] += 1
            logger.error(f"Критическая ошибка форматирования: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

    # Планируем удаление временного файла после отправки
    background_tasks.add_task(cleanup_temp_file, final_temp_file.name)

    return FileResponse(
        path=final_temp_file.name,
        filename=output_filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "X-Format-Stats": json.dumps(format_stats),
            "X-Requirements-Source": "file" if requirements else "default",
            "X-Version": "2.0.0"
        }
    )

@app.post("/validate",
         response_model=ValidationResponse,
         tags=["validation"],
         summary="🔍 Детальная валидация ВКР",
         description="Проверяет документ на соответствие ГОСТ без изменений и возвращает детальный отчет",
         responses={
             200: {"model": ValidationResponse, "description": "Детальный отчет валидации"},
             400: {"model": ErrorResponse, "description": "Неверный формат файла"},
             500: {"model": ErrorResponse, "description": "Ошибка валидации"}
         })
async def validate_vkr(
    vkr: UploadFile = File(..., description="📄 Файл ВКР в формате .docx для детальной проверки"),
    requirements: Optional[UploadFile] = File(
        default=None, description="📋 Файл требований (необязательно - используются встроенные ГОСТ)")
) -> ValidationResponse:
    """
    ## 🔍 Детальная валидация документа ВКР
    
    **Что делает этот endpoint:**
    - Проверяет документ на соответствие ГОСТ **БЕЗ ИЗМЕНЕНИЙ**
    - Возвращает детальный отчет с конкретными ошибками
    - Дает пошаговые инструкции по исправлению
    - Показывает точное местоположение каждой проблемы
    - Предоставляет оценку качества документа (0-100)
    
    **🎯 Детализация ошибок включает:**
    - 📍 **Точное местоположение**: номер параграфа + превью текста (50 символов)
    - ⚠️ **Ожидаемое vs фактическое**: конкретные значения с единицами измерения
    - 💡 **Пошаговые инструкции**: команды меню Word для исправления
    - 🏷️ **Информация о стилях**: какой стиль применен к элементу
    - 📊 **Категоризация**: группировка по типам проблем
    
    **🏷️ Категории проверки:**
    - **margins**: поля документа, ориентация, формат A4
    - **fonts**: типы шрифтов, размеры в разных элементах
    - **headings**: заголовки H1-H4 (шрифт, размер, выравнивание)
    - **paragraphs**: красная строка, междустрочный интервал
    - **alignment**: выравнивание по ширине/центру/краям
    - **lists**: отступы списков, висячие отступы
    - **tables**: структура таблиц, заголовки, заполненность
    - **structure**: иерархия заголовков, общая структура
    
    **🎖️ Система оценки:**
    - **🔴 Ошибки (вес 3)**: критичные нарушения ГОСТ
    - **🟡 Предупреждения (вес 2)**: важные замечания
    - **🔵 Информация (вес 1)**: рекомендации и подсказки
    
    **📊 Статистика документа:**
    - Количество параграфов, таблиц, заголовков по уровням
    - Анализ структуры и баланса элементов
    - Процент заполненности таблиц
    - Соотношение типов контента
    
    **💡 Когда использовать:**
    - Перед окончательной сдачей работы
    - Для анализа качества существующего документа
    - Если нужны конкретные рекомендации по исправлению
    - Для контроля после форматирования
    
    **⚡ Преимущества:**
    - Документ остается неизменным
    - Максимальная детализация ошибок
    - Конкретные пути исправления
    - Быстрая работа
    """
    
    # Обновляем статистику
    stats["total_processed"] += 1
    stats["validation_requests"] += 1
    stats["last_processed"] = datetime.now().isoformat()

    # Валидация формата файла
    if not vkr.filename.endswith(('.docx', '.doc')):
        raise HTTPException(
            status_code=400,
            detail="Файл ВКР должен быть в формате .docx или .doc"
        )

    # Создаем временную директорию для обработки
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        vkr_path = tmpdir_path / "input_vkr.docx"

        try:
            logger.info(f"🔍 Начинаем валидацию ВКР: {vkr.filename}")

            # Сохраняем файл ВКР
            with open(vkr_path, "wb") as f:
                shutil.copyfileobj(vkr.file, f)

            # Используем встроенные требования ГОСТ
            logger.info("📋 Используем встроенные требования ГОСТ")
            vkr_requirements = analyze_requirements_stub("default")

            # Выполняем валидацию
            logger.info("🔍 Выполняем детальную валидацию...")
            validation_passed, report = validate_vkr_document(str(vkr_path), vkr_requirements)

            logger.info(f"📊 Валидация завершена. Оценка: {report.get_summary()['score']}/100")

            # Группируем ошибки по категориям для API
            issues_by_category = {}
            for issue in report.issues:
                if issue.category not in issues_by_category:
                    issues_by_category[issue.category] = []
                
                issues_by_category[issue.category].append(ValidationIssueModel(
                    type=issue.type,
                    category=issue.category,
                    description=issue.description,
                    location=issue.location,
                    expected=issue.expected,
                    actual=issue.actual,
                    suggestion=issue.suggestion
                ))

            # Создаем ответ
            response = ValidationResponse(
                validation_passed=validation_passed,
                summary=ValidationSummary(**report.get_summary()),
                statistics=ValidationStatistics(**report.statistics),
                issues_by_category=issues_by_category,
                timestamp=datetime.now().isoformat()
            )

            stats["successful"] += 1
            return response

        except HTTPException:
            raise
        except Exception as e:
            stats["failed"] += 1
            logger.error(f"Критическая ошибка валидации: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Внутренняя ошибка валидации: {str(e)}"
            )

@app.get("/demo/validation",
         response_model=ValidationResponse,
         tags=["validation"],
         summary="🎯 Демо валидации с примерами ошибок",
         description="Возвращает пример детального отчета валидации для демонстрации возможностей API")
async def demo_validation() -> ValidationResponse:
    """
    ## 🎯 Демонстрация детального отчета валидации
    
    Этот endpoint показывает пример того, как выглядит детальный отчет валидации.
    Полезно для:
    - Понимания структуры ответа `/validate`
    - Тестирования интеграции
    - Изучения типов ошибок
    
    **Возвращает реалистичный пример с:**
    - Ошибками шрифтов и размеров
    - Проблемами полей и отступов
    - Неправильным выравниванием
    - Проблемами в таблицах
    - Конкретными рекомендациями
    """
    from demo_detailed_errors import create_demo_report
    
    report = create_demo_report()
    
    # Группируем ошибки по категориям
    issues_by_category = {}
    for issue in report.issues:
        if issue.category not in issues_by_category:
            issues_by_category[issue.category] = []
        
        issues_by_category[issue.category].append(ValidationIssueModel(
            type=issue.type,
            category=issue.category,
            description=issue.description,
            location=issue.location,
            expected=issue.expected,
            actual=issue.actual,
            suggestion=issue.suggestion
        ))
    
    return ValidationResponse(
        validation_passed=False,
        summary=ValidationSummary(**report.get_summary()),
        statistics=ValidationStatistics(**report.statistics),
        issues_by_category=issues_by_category,
        timestamp=datetime.now().isoformat()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Обработчик HTTP ошибок с дополнительной информацией"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
            "method": request.method
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик ошибок для отладки"""
    logger.error(f"Необработанная ошибка: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Внутренняя ошибка сервера",
            "error_type": type(exc).__name__,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Запуск VKR Formatter API с Swagger UI")
    logger.info("📖 Документация доступна по адресу: http://localhost:8000/docs")
    logger.info("🔧 Альтернативная документация: http://localhost:8000/redoc")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
