"""
Модуль чтения данных метрики из PostgreSQL.

Содержит функции для:
- чтения wide-таблицы метрики из PostgreSQL.
"""

from src.db.reader import fetch_all


def read_metric_clean_table(table_name:str) -> list[dict]:
    """
    Читает очищенную wide-таблицу метрики из PostgreSQL.

    :param table_name: Название таблицы, которую нужно прочесть
    :type table_name: str
    :return: Список строк таблицы метрики в виде словарей, отсортированный по дате по возрастанию.
    :rtype: list[dict]
    """
    query = f"""
        SELECT * FROM {table_name}
        ORDER BY date
    """
    return fetch_all(query)