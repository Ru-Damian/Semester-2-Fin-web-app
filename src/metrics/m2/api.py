"""
Модуль HTTP-API для работы с метрикой M2.

Содержит эндпоинты для:
- загрузки сырых данных по M2 из API ЦБ РФ;
- сборки таблицы M2 в PostgreSQL;
- чтения очищенных данные из локальной БД.
"""

from fastapi import APIRouter, HTTPException
import requests

from src.metrics.m2.table_builder import load_cbr_data
from src.metrics.m2.repository import read_m2_clean_table
from src.metrics.m2.service import save_m2_clean_table_to_db


router = APIRouter(
    prefix="/m2",
    tags=["M2"],
)


@router.get("/from-db")
def get_m2_from_db():
    """Читает очищенную таблицу M2 из PostgreSQL."""
    try:
        rows = read_m2_clean_table()
        return {
            "row_count": len(rows),
            "data": rows,
        }
    except Exception as e:
        return {
            "error_type": type(e).__name__,
            "error_text": str(e),
        }


@router.get("/{y1}/{y2}")
def get_m2(y1: int, y2: int):
    """Загружает сырой JSON по M2 из API."""
    try:
        return load_cbr_data(y1, y2)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ошибка запроса к ЦБ: {e}")

@router.post("/rebuild/{y1}/{y2}")
def rebuild_m2_table(y1: int, y2: int):
    """Пересобрает таблицу m2_clean в БД за указанный период."""
    if y1 > y2:
        raise HTTPException(status_code=400, detail="Начальный год больше конечного.")

    try:
        rows_inserted = save_m2_clean_table_to_db(y1, y2)
        return {
            "status": "ok",
            "rows_inserted": rows_inserted,
            "message": f"Таблица m2_clean пересчитана за {y1}–{y2} гг.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при пересборке таблицы M2: {type(e).__name__}: {e}",
        )