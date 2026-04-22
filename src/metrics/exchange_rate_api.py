"""
Модуль HTTP-API для работы с метрикой exchange_rate(номинальный курс валют).

Содержит эндпоинты для:
- загрузки сырых данных по exchange_rate из API ЦБ РФ;
- сборки таблицы exchange_rate в PostgreSQL;
- чтения очищенных данные из локальной БД.
"""

from fastapi import APIRouter, HTTPException
import requests

from src.utils.table_builder import load_cbr_data
from src.utils.repository import read_metric_clean_table
from src.utils.service import save_metric_clean_table_to_db


PUBLICATION_ID = 33
DATASET_ID = 127
DEFAULT_TABLE_NAME = "exchange_rate_clean"

router = APIRouter(
    prefix="/exchange_rate",
    tags=["exchange_rate"]
)


@router.get("/from-db")
def get_exchange_rate_from_db():
    """Читает очищенную таблицу exchange_rate из PostgreSQL."""
    try:
        rows = read_metric_clean_table(DEFAULT_TABLE_NAME)
        return {
            "row_count": len(rows),
            "data": rows
        }
    except Exception as e:
        return {
            "error_type": type(e).__name__,
            "error_text": str(e)
        }


@router.get("/{y1}/{y2}")
def get_exchange_rate(y1: int, y2: int):
    """Загружает сырой JSON по exchange_rate из API."""
    try:
        return load_cbr_data(y1, y2, PUBLICATION_ID, DATASET_ID)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ошибка запроса к ЦБ: {e}")


@router.post("/rebuild/{y1}/{y2}")
def rebuild_exchange_rate_table(y1: int, y2: int):
    """Пересобрает таблицу m2_clean в БД за указанный период."""
    if y1 > y2:
        raise HTTPException(status_code=400, detail="Начальный год больше конечного.")

    try:
        rows_inserted = save_metric_clean_table_to_db(y1, y2, PUBLICATION_ID, DATASET_ID, DEFAULT_TABLE_NAME)
        return {
            "status": "ok",
            "rows_inserted": rows_inserted,
            "message": f"Таблица {DEFAULT_TABLE_NAME} пересчитана за {y1}–{y2} гг."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при пересборке таблицы exchange_rate: {type(e).__name__}: {e}"
        )