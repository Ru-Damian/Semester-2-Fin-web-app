from psycopg2.extras import RealDictCursor
from db import get_connection


def read_m2_clean_table(table_name: str = "m2_clean"):
    """Читает таблицу M2 из базы."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        f"""
        SELECT
            date,
            total_m2,
            m1,
            other_deposits_households,
            other_deposits_fin_org,
            other_deposits_nonfin_org
        FROM {table_name}
        ORDER BY date
        """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows