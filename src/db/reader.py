"""
Модуль общих функций чтения из PostgreSQL.
"""

from psycopg2.extras import RealDictCursor
import numpy as np

from src.db.connection import get_connection


def _clean_value(value):
    """
    Обработать разные случаи пропусков.
    
    :param value: значение из SELECT-запроса
    :type value: any
    :return: value или None
    :rtype: any|None
    """
    if value is None:
        return None
    
    # Проверка на float NaN и Inf
    if isinstance(value, float):
        if np.isnan(value) or np.isinf(value):
            return None
    
    # Проверка на Decimal NaN
    if hasattr(value, 'is_nan') and callable(value.is_nan):
        if value.is_nan():
            return None
    
    # Проверка на float завернутый в string
    try:
        float_val = float(value)
        if np.isnan(float_val) or np.isinf(float_val):
            return None
    except (TypeError, ValueError):
        pass
    
    return value


def fetch_all(query: str, params: tuple = None) -> list[dict]:
    """
    Выполнить SELECT-запрос и вернуть все найденные строки.

    :param query: SQL-запрос на чтение данных
    :type query: str
    :param params: Кортеж параметров для SQL-запроса, можно не передавать
    :type params: tuple|None
    :return: Список строк результата в виде словарей
    :rtype: list[dict]
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute(query, params or ())
        rows = cur.fetchall()
        
        result = []
        for row in rows:
            dct_row = dict(row)
            cleaned = {key: _clean_value(value) for key, value in dct_row.items()}
            result.append(cleaned)
        return result
    finally:
        cur.close()
        conn.close()


def fetch_one(query: str, params: tuple = None) -> dict | None:
    """
    Выполнить SELECT-запрос и вернуть одну строку.
    
    :param query: SQL-запрос на чтение данных
    :type query: str
    :param params: Кортеж параметров для SQL-запроса, можно не передавать
    :type params: tuple|None
    :return: Одна строка в виде словаря или None, если данных нет
    :rtype: list[dict]|None
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(query, params or ())
        row = cur.fetchone()
        if row:
            dct_row = dict(row)
            return {key: _clean_value(value) for key, value in dct_row.items()}
        return None
    finally:
        cur.close()
        conn.close()