"""
Модуль сервисных функций для работы с метрикой M2.

Содержит функции для:
- сохранения wide-таблицы M2 в PostgreSQL.
"""

from psycopg2.extras import execute_values

from src.db.connection import get_connection
from src.metrics.m2.table_builder import build_m2_clean_table


def save_m2_clean_table_to_db(y1: int, y2: int, table_name: str = "m2_clean") -> int:
    """
    Сохраняет wide-таблицу M2 в PostgreSQL.

    :param y1: Начальный год периода
    :type y1: int
    :param y2: Конечный год периода
    :type y2: int
    :param table_name: Название таблицы(по умолчанию "m2_clean")
    :type table_name: str
    :return: Количество вставленных строк в сохранненой таблице
    :rtype: int
    """
    _, _, wide_df = build_m2_clean_table(y1, y2)

    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Создаём таблицу заново
        cur.execute(
            f"""
            DROP TABLE IF EXISTS {table_name};
            CREATE TABLE {table_name} (
                date date PRIMARY KEY,
                total_m2 numeric,
                m1 numeric,
                other_deposits_households numeric,
                other_deposits_fin_org numeric,
                other_deposits_nonfin_org numeric
            );
            """
        )

        rows = [
            (
                row["date"].date(),
                row["total_m2"],
                row["m1"],
                row["other_deposits_households"],
                row["other_deposits_fin_org"],
                row["other_deposits_nonfin_org"],
            )
            for _, row in wide_df.iterrows()
        ]

        execute_values(
            cur,
            f"""
            INSERT INTO {table_name} (
                date,
                total_m2,
                m1,
                other_deposits_households,
                other_deposits_fin_org,
                other_deposits_nonfin_org
            ) VALUES %s
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