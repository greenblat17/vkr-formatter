from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import tempfile
import shutil
import logging
from pathlib import Path
import json
import os
from datetime import datetime
from typing import Optional
from logger_config import api_logger as logger

# Импорты наших модулей
from vkr_requirements_stub import analyze_requirements_stub
from vkr_formatter import format_vkr_document

# Создаем приложение
app = FastAPI(
    title="VKR Formatter API (Clean Version)",
    description="Простое API для форматирования ВКР согласно ГОСТ",
    version="2.0.0"
)

# Глобальная статистика
stats = {
    "total_processed": 0,
    "successful": 0,
    "failed": 0,
    "last_processed": None
}

def cleanup_temp_file(file_path: str):
    """Удаляет временный файл"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Временный файл удален: {file_path}")
    except Exception as e:
        logger.warning(f"Не удалось удалить временный файл {file_path}: {e}")

@app.get("/")
async def root():
    """Информация о сервисе"""
    return {
        "service": "VKR Formatter API (Clean Version)",
        "version": "2.0.0",
        "description": "Простое форматирование ВКР с заглушкой требований",
        "endpoints": {
            "/format": "POST - Форматирование ВКР",
            "/requirements": "GET - Просмотр требований по умолчанию",
            "/stats": "GET - Статистика"
        }
    }

@app.get("/requirements")
async def get_default_requirements():
    """Возвращает требования по умолчанию"""
    try:
        requirements = analyze_requirements_stub("dummy_path")
        return {
            "status": "success",
            "message": "Требования по умолчанию ГОСТ",
            "requirements": requirements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения требований: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Возвращает статистику обработки"""
    return stats

@app.post("/format")
async def format_vkr(
    background_tasks: BackgroundTasks,
    vkr: UploadFile = File(..., description="Файл ВКР в формате .docx"),
    requirements: Optional[UploadFile] = File(default=None, description="Файл требований (опционально, используется заглушка)")
):
    """
    Форматирует ВКР согласно требованиям
    
    - Если файл требований не загружен, используются стандартные требования ГОСТ
    - Обрабатывает H1, H2, списки, базовое форматирование
    - Пропускает шаблонные страницы
    """
    
    # Обновляем статистику
    stats["total_processed"] += 1
    stats["last_processed"] = datetime.now().isoformat()
    
    # Валидация
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
        req_path = tmpdir_path / "requirements.docx" if requirements else None
        output_path = tmpdir_path / "formatted_vkr.docx"
        
        try:
            logger.info(f"📁 Начинаем обработку ВКР: {vkr.filename}")
            
            # Сохраняем файл ВКР
            with open(vkr_path, "wb") as f:
                shutil.copyfileobj(vkr.file, f)
            logger.info(f"💾 ВКР сохранен: {vkr_path}")
            
            logger.info("📋 Используем требования по умолчанию")
            vkr_requirements = analyze_requirements_stub("default")
            
            # Форматируем документ
            logger.info("🚀 Применяем форматирование...")
            logger.info(f"📄 Входной файл: {vkr_path} (существует: {vkr_path.exists()})")
            logger.info(f"📄 Выходной файл: {output_path}")
            
            success, format_stats = format_vkr_document(
                str(vkr_path), 
                vkr_requirements, 
                str(output_path)
            )
            
            logger.info(f"📊 Результат форматирования: success={success}, stats={format_stats}")
            
            if not success:
                stats["failed"] += 1
                raise HTTPException(
                    status_code=500, 
                    detail="Ошибка при форматировании документа"
                )
            
            # Проверяем результат
            logger.info(f"🔍 Проверяем существование выходного файла: {output_path}")
            logger.info(f"✅ Файл существует: {output_path.exists()}")
            
            if not output_path.exists():
                stats["failed"] += 1
                # Давайте попробуем найти файл в директории
                logger.error(f"📂 Содержимое временной директории: {list(tmpdir_path.iterdir())}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Отформатированный файл не был создан. Ожидался: {output_path}"
                )
            
            # ВАЖНО: Копируем файл в новое временное место перед выходом из контекста
            final_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
            shutil.copy2(output_path, final_temp_file.name)
            final_temp_file.close()
            
            stats["successful"] += 1
            
            # Генерируем имя выходного файла
            original_name = Path(vkr.filename).stem
            output_filename = f"{original_name}_formatted.docx"
            
            logger.info(f"🎉 Форматирование завершено успешно: {output_filename}")
            logger.info(f"📈 Статистика форматирования: {format_stats}")
            
        except HTTPException:
            # Пробрасываем HTTP ошибки
            raise
            
        except Exception as e:
            stats["failed"] += 1
            logger.error(f"Критическая ошибка: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )
    
    # Возвращаем файл (уже вне контекста with)
    # Добавляем задачу на удаление файла после отправки
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

# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Необработанная ошибка: {str(exc)}")
    return {
        "error": "Internal server error",
        "detail": str(exc)
    }

