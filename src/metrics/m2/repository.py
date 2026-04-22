"""
Модуль чтения данных по метрике M2 из PostgreSQL.

Содержит функции для:
- чтения wide-таблицы M2 из PostgreSQL.
"""

from src.db.reader import fetch_all


def read_m2_clean_table(table_name: str = "m2_clean") -> list[dict]:
    """
    Читает очищенную wide-таблицу M2 из PostgreSQL.

    :param table_name: Название таблицы, которую нужно прочесть(по умолчанию "m2_clean")
    :type table_name: str
    :return: Список строк таблицы M2 в виде словарей, отсортированный по дате по возрастанию.
    :rtype: list[dict]
    """
    query = f"""
        SELECT
            date,
            total_m2,
            m1,
            other_deposits_households,
            other_deposits_fin_org,
            other_deposits_nonfin_org
        FROM {table_name}
        ORDER BY date
    """
    return fetch_all(query)
