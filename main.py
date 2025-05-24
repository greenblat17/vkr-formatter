from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from utils.extract_requirements import extract_requirements_from_docx
from utils.apply_formatting import VKRFormatter, apply_formatting
from utils.ai_direct_formatter import AIDirectFormatter, format_with_ai
# новый импорт # новый импорт
from utils.comprehensive_vkr_formatter import comprehensive_format_vkr
import tempfile
import shutil
import os
import logging
from pathlib import Path
from typing import Dict, Any
import json
import traceback
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vkr_formatter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VKR Formatter API",
    description="API для автоматического форматирования ВКР согласно требованиям вуза",
    version="1.0.0"
)

# Глобальная статистика
processing_stats = {
    "total_processed": 0,
    "successful": 0,
    "failed": 0,
    "last_processed": None
}


@app.get("/")
async def root():
    """Информация о сервисе"""
    return {
        "message": "VKR Formatter API",
        "version": "1.0.0",
        "endpoints": {
            "/process": "POST - Двухэтапное форматирование (извлечение + применение)",
            "/process-ai-direct": "POST - Прямое форматирование через ИИ",
            "/validate-requirements": "POST - Валидация требований",
            "/stats": "GET - Статистика обработки"
        }
    }


@app.get("/stats")
async def get_stats():
    """Получить статистику обработки"""
    return processing_stats


@app.post("/validate-requirements")
async def validate_requirements(requirements: UploadFile = File(...)):
    """
    Валидация файла с требованиями без форматирования
    Фокус на заголовках 1 уровня
    """
    if not requirements.filename.endswith(('.docx', '.doc')):
        raise HTTPException(
            status_code=400, detail="Файл требований должен быть в формате .docx или .doc")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_req:
            shutil.copyfileobj(requirements.file, tmp_req)
            tmp_req_path = tmp_req.name

        try:
            # Извлекаем требования (фокус на H1)
            requirements_json = extract_requirements_from_docx(tmp_req_path)
            logger.info("Требования для H1 успешно извлечены для валидации")

            # Валидируем требования
            formatter = VKRFormatter()
            validated_requirements = formatter.validate_formatting(
                requirements_json)

            return {
                "status": "success",
                "message": "Требования для заголовков 1 уровня успешно извлечены и валидированы",
                "extracted_requirements": requirements_json,
                "validated_requirements": validated_requirements,
                "focus": "H1 headers only"
            }

        finally:
            # Удаляем временный файл
            if os.path.exists(tmp_req_path):
                os.unlink(tmp_req_path)

    except Exception as e:
        logger.error(f"Ошибка при валидации требований: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Ошибка при обработке требований: {str(e)}")


@app.post("/process-ai-direct")
async def process_docs_with_ai(vkr: UploadFile = File(...), requirements: UploadFile = File(...)):
    """
    Прямое форматирование через ИИ - одним запросом
    ИИ сам анализирует требования и применяет их к документу
    """
    # Обновляем статистику
    processing_stats["total_processed"] += 1
    processing_stats["last_processed"] = datetime.now().isoformat()

    # Валидация файлов
    if not vkr.filename.endswith(('.docx', '.doc')):
        raise HTTPException(
            status_code=400, detail="Файл ВКР должен быть в формате .docx или .doc")

    if not requirements.filename.endswith(('.docx', '.doc')):
        raise HTTPException(
            status_code=400, detail="Файл требований должен быть в формате .docx или .doc")

    # Создаем временную директорию
    with tempfile.TemporaryDirectory() as tmpdir:
        # Пути к временным файлам
        vkr_path = "vkr.docx"
        req_path = "requirements.docx"
        out_path = "formatted_vkr_ai.docx"

        try:
            logger.info(
                f"Начинаем ИИ форматирование: ВКР={vkr.filename}, Требования={requirements.filename}")

            # Сохраняем загруженные файлы
            with open(vkr_path, "wb") as f:
                shutil.copyfileobj(vkr.file, f)
            logger.info(f"ВКР сохранен: {vkr_path}")

            with open(req_path, "wb") as f:
                shutil.copyfileobj(requirements.file, f)
            logger.info(f"Требования сохранены: {req_path}")

            # Прямое форматирование через ИИ
            logger.info("Запускаем ИИ анализ и форматирование...")
            ai_formatter = AIDirectFormatter()
            success = ai_formatter.format_document_with_ai(
                str(vkr_path), str(req_path), str(out_path))

            if not success:
                processing_stats["failed"] += 1
                raise HTTPException(
                    status_code=500, detail="Ошибка при ИИ форматировании")

            # Получаем статистику обработки
            ai_stats = ai_formatter.get_stats()
            logger.info(f"ИИ форматирование завершено. Статистика: {ai_stats}")

            # Проверяем, что выходной файл создан
            if not Path(out_path).exists():
                processing_stats["failed"] += 1
                raise HTTPException(
                    status_code=500, detail="Отформатированный файл не был создан")

            processing_stats["successful"] += 1

            # Генерируем имя выходного файла
            original_name = Path(vkr.filename).stem
            output_filename = f"{original_name}_ai_formatted.docx"

            logger.info(f"Успешно обработан файл через ИИ: {output_filename}")

            # Возвращаем отформатированный файл
            return FileResponse(
                path=str(out_path),
                filename=output_filename,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "X-Processing-Stats": json.dumps(ai_stats),
                    "X-Processing-Method": "AI-Direct",
                    "X-AI-Analysis": "Requirements analyzed and applied directly by AI"
                }
            )

        except HTTPException:
            # Пробрасываем HTTP исключения дальше
            raise
        except Exception as e:
            processing_stats["failed"] += 1
            logger.error(f"Критическая ошибка при ИИ обработке: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Внутренняя ошибка ИИ форматирования: {str(e)}"
            )


@app.post("/process")
async def process_docs(vkr: UploadFile = File(...), requirements: UploadFile = File(...)):
    """
    Двухэтапное форматирование ВКР (классический метод)
    1. Извлечение требований
    2. Применение форматирования
    """
    # Обновляем статистику
    processing_stats["total_processed"] += 1
    processing_stats["last_processed"] = datetime.now().isoformat()

    # Валидация файлов
    if not vkr.filename.endswith(('.docx', '.doc')):
        raise HTTPException(
            status_code=400, detail="Файл ВКР должен быть в формате .docx или .doc")

    if not requirements.filename.endswith(('.docx', '.doc')):
        raise HTTPException(
            status_code=400, detail="Файл требований должен быть в формате .docx или .doc")

    # Создаем временную директорию
    with tempfile.TemporaryDirectory() as tmpdir:
        # Пути к временным файлам
        vkr_path = "vkr.docx"
        req_path = "requirements.docx"
        out_path = "formatted_vkr.docx"

        try:
            logger.info(
                f"Начинаем обработку файлов: ВКР={vkr.filename}, Требования={requirements.filename}")

            # Сохраняем загруженные файлы
            with open(vkr_path, "wb") as f:
                shutil.copyfileobj(vkr.file, f)
            logger.info(f"ВКР сохранен: {vkr_path}")

            with open(req_path, "wb") as f:
                shutil.copyfileobj(requirements.file, f)
            logger.info(f"Требования сохранены: {req_path}")

            # Шаг 1: Извлекаем требования из документа
            logger.info("Извлекаем требования...")
            requirements_json = extract_requirements_from_docx(str(req_path))
            logger.info(
                f"Требования извлечены: {json.dumps(requirements_json, ensure_ascii=False, indent=2)}")

            # Шаг 2: Создаем форматтер и валидируем требования
            formatter = VKRFormatter()
            validated_requirements = formatter.validate_formatting(
                requirements_json)
            logger.info(
                f"Требования валидированы: {json.dumps(validated_requirements, ensure_ascii=False, indent=2)}")

            # Шаг 3: Применяем форматирование
            logger.info("Применяем форматирование...")
            success = formatter.apply_formatting(
                str(vkr_path), validated_requirements, str(out_path))

            if not success:
                processing_stats["failed"] += 1
                raise HTTPException(
                    status_code=500, detail="Ошибка при применении форматирования")

            # Получаем статистику обработки
            format_stats = formatter.get_stats()
            logger.info(
                f"Форматирование завершено. Статистика: {format_stats}")

            # Проверяем, что выходной файл создан
            if not Path(out_path).exists():
                processing_stats["failed"] += 1
                raise HTTPException(
                    status_code=500, detail="Отформатированный файл не был создан")

            processing_stats["successful"] += 1

            # Генерируем имя выходного файла
            original_name = Path(vkr.filename).stem
            output_filename = f"{original_name}_formatted.docx"

            logger.info(f"Успешно обработан файл: {output_filename}")

            # Возвращаем отформатированный файл
            return FileResponse(
                path=str(out_path),
                filename=output_filename,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "X-Processing-Stats": json.dumps(format_stats),
                    "X-Applied-Requirements": json.dumps(validated_requirements, ensure_ascii=False)
                }
            )

        except HTTPException:
            # Пробрасываем HTTP исключения дальше
            raise
        except Exception as e:
            processing_stats["failed"] += 1
            logger.error(f"Критическая ошибка при обработке: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )


@app.post("/process-with-custom-requirements")
async def process_with_custom_requirements(
    vkr: UploadFile = File(...),
    custom_requirements: Dict[str, Any] = None
):
    """
    Альтернативный endpoint для обработки с переданными требованиями в JSON
    """
    if not vkr.filename.endswith(('.docx', '.doc')):
        raise HTTPException(
            status_code=400, detail="Файл ВКР должен быть в формате .docx или .doc")

    if not custom_requirements:
        raise HTTPException(
            status_code=400, detail="Требования должны быть переданы")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        vkr_path = tmpdir_path / "vkr.docx"
        out_path = tmpdir_path / "formatted_vkr.docx"

        try:
            # Сохраняем ВКР
            with open(vkr_path, "wb") as f:
                shutil.copyfileobj(vkr.file, f)

            # Создаем форматтер и применяем требования
            formatter = VKRFormatter()
            validated_requirements = formatter.validate_formatting(
                custom_requirements)
            success = formatter.apply_formatting(
                str(vkr_path), validated_requirements, str(out_path))

            if not success:
                raise HTTPException(
                    status_code=500, detail="Ошибка при применении форматирования")

            original_name = Path(vkr.filename).stem
            output_filename = f"{original_name}_formatted.docx"

            return FileResponse(
                path=str(out_path),
                filename=output_filename,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        except Exception as e:
            logger.error(
                f"Ошибка при обработке с кастомными требованиями: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка обработки: {str(e)}")


@app.post("/process-comprehensive")
async def process_docs_comprehensive(vkr: UploadFile = File(...), requirements: UploadFile = File(...)):
    """
    Комплексное форматирование ВКР согласно полной структуре
    Анализирует и применяет все типы требований: H1, H2, списки, таблицы, рисунки и т.д.
    """
    # Обновляем статистику
    processing_stats["total_processed"] += 1
    processing_stats["last_processed"] = datetime.now().isoformat()

    # Валидация файлов
    if not vkr.filename.endswith(('.docx', '.doc')):
        raise HTTPException(
            status_code=400, detail="Файл ВКР должен быть в формате .docx или .doc")

    if not requirements.filename.endswith(('.docx', '.doc')):
        raise HTTPException(
            status_code=400, detail="Файл требований должен быть в формате .docx или .doc")

    # Создаем временную директорию
    with tempfile.TemporaryDirectory() as tmpdir:
        # Пути к временным файлам
        vkr_path = "vkr.docx"
        req_path = "requirements.docx"
        out_path = "comprehensive_formatted_vkr.docx"

        try:
            logger.info(
                f"Начинаем комплексное форматирование: ВКР={vkr.filename}, Требования={requirements.filename}")

            # Сохраняем загруженные файлы
            with open(vkr_path, "wb") as f:
                shutil.copyfileobj(vkr.file, f)
            logger.info(f"ВКР сохранен: {vkr_path}")

            with open(req_path, "wb") as f:
                shutil.copyfileobj(requirements.file, f)
            logger.info(f"Требования сохранены: {req_path}")

            # Комплексное форматирование
            logger.info("Запускаем комплексный анализ и форматирование...")
            success, comp_stats = comprehensive_format_vkr(
                str(vkr_path), str(req_path), str(out_path))

            if not success:
                processing_stats["failed"] += 1
                error_msg = comp_stats.get(
                    'error', 'Неизвестная ошибка комплексного форматирования')
                raise HTTPException(
                    status_code=500, detail=f"Ошибка при комплексном форматировании: {error_msg}")

            logger.info(
                f"Комплексное форматирование завершено. Статистика: {comp_stats}")

            # Проверяем, что выходной файл создан
            if not Path(out_path).exists():
                processing_stats["failed"] += 1
                raise HTTPException(
                    status_code=500, detail="Отформатированный файл не был создан")

            processing_stats["successful"] += 1

            # Генерируем имя выходного файла
            original_name = Path(vkr.filename).stem
            output_filename = f"{original_name}_comprehensive_formatted.docx"

            logger.info(
                f"Успешно обработан файл комплексно: {output_filename}")

            # Создаем детальный отчет о форматировании (только на английском для заголовков)
            formatting_report = {
                "method": "comprehensive",
                "sections_processed": {
                    "h1_headers": comp_stats.get('h1_formatted', 0),
                    "h2_headers": comp_stats.get('h2_formatted', 0),
                    "lists": comp_stats.get('lists_formatted', 0),
                    "regular_paragraphs": comp_stats.get('regular_formatted', 0),
                    "skipped_sections": comp_stats.get('skipped_sections', 0)
                },
                "total_paragraphs": comp_stats.get('total_paragraphs', 0),
                "errors": comp_stats.get('errors', 0),
                "features_applied": [
                    "Global page settings and margins",
                    "H1 and H2 headers formatting",
                    "Lists formatting with proper punctuation",
                    "Template pages skipping",
                    "GOST requirements application"
                ]
            }

            # Возвращаем отформатированный файл
            return FileResponse(
                path=str(out_path),
                filename=output_filename,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "X-Processing-Stats": json.dumps(comp_stats),
                    "X-Processing-Method": "Comprehensive",
                    "X-Formatting-Report": json.dumps(formatting_report),
                    "X-Features-Applied": "H1,H2,Lists,GlobalSettings,SkipSections"
                }
            )

        except HTTPException:
            # Пробрасываем HTTP исключения дальше
            raise
        except Exception as e:
            processing_stats["failed"] += 1
            logger.error(
                f"Критическая ошибка при комплексной обработке: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Внутренняя ошибка комплексного форматирования: {str(e)}"
            )


# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Необработанная ошибка: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
