"""
Модуль сервисных функций для работы с метриками.

Содержит функции для:
- сохранения wide-таблицы метрики в PostgreSQL.
"""

from psycopg2.extras import execute_values

from src.db.connection import get_connection
from src.utils.table_builder import build_metric_clean_table


def save_metric_clean_table_to_db(y1:int, y2:int, publication_id:int, dataset_id:int, table_name:str) -> int:
    """
    Сохраняет wide-таблицу метрики в PostgreSQL.

    :param y1: Начальный год периода
    :type y1: int
    :param y2: Конечный год периода
    :type y2: int
    :param publication_id: Первый индитификатор метрики
    :type publication_id: int
    :param dataset_id: Второй индитификатор метрики
    :type dataset_id: int
    :param table_name: Название таблицы
    :type table_name: str
    :return: Количество вставленных строк в сохранненой таблице
    :rtype: int
    """
    _, _, wide_df = build_metric_clean_table(y1, y2, publication_id, dataset_id)

    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        columns = wide_df.columns.tolist()
        columns_def = ", ".join([f"{col} numeric" for col in columns if col != "date"])

        cur.execute(
            f"""
            DROP TABLE IF EXISTS {table_name};
            CREATE TABLE {table_name} (
                date date PRIMARY KEY,
                {columns_def}
            );
            """
        )

        rows = [tuple(row) for _, row in wide_df.iterrows()]

        execute_values(
            cur,
            f"""
            INSERT INTO {table_name} ({", ".join(columns)}) VALUES %s
            """,
            rows,
        )

        conn.commit()
        return len(rows)
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()