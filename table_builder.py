import requests
import pandas as pd
from db import get_connection
from psycopg2.extras import execute_values


def load_cbr_data(y1: int, y2: int) -> dict:
    """Загружает сырой JSON из API ЦБ."""
    response = requests.get(
        "https://www.cbr.ru/dataservice/data",
        params={
            "y1": y1,
            "y2": y2,
            "publicationId": 5,
            "datasetId": 7,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def build_m2_dataframe(y1: int, y2: int):
    """Собирает DataFrame из ответа ЦБ."""
    data = load_cbr_data(y1, y2)
    df = pd.DataFrame(data["RawData"])
    return data, df


def build_m2_clean_table(y1: int, y2: int):
    """Формирует очищенную wide-таблицу M2."""
    data, df = build_m2_dataframe(y1, y2)

    header_map = {item["id"]: item["elname"] for item in data["headerData"]}
    unit_map = {item["id"]: item["val"] for item in data["units"]}

    df = df[["date", "element_id", "unit_id", "obs_val"]].copy()
    df["date"] = pd.to_datetime(df["date"])
    df["indicator_name"] = df["element_id"].map(header_map)
    df["unit_name"] = df["unit_id"].map(unit_map)

    wide_df = df.pivot_table(
        index="date",
        columns="indicator_name",
        values="obs_val",
        aggfunc="first"
    ).reset_index()

    wide_df = wide_df.rename(columns={
        "Всего": "total_m2",
        "Денежный агрегат М1": "m1",
        "Другие депозиты других финансовых организаций": "other_deposits_fin_org",
        "Другие депозиты нефинансовых организаций": "other_deposits_nonfin_org",
        "Другие депозиты домашних хозяйств": "other_deposits_households",
    })

    wide_df = wide_df.sort_values("date").reset_index(drop=True)

    return data, df, wide_df


def save_m2_clean_table_to_db(y1: int, y2: int, table_name: str = "m2_clean"):
    """Сохраняет wide-таблицу M2 в PostgreSQL."""
    _, _, wide_df = build_m2_clean_table(y1, y2)

    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor()

    cur.execute(f"""
        DROP TABLE IF EXISTS {table_name};
        CREATE TABLE {table_name} (
            date date PRIMARY KEY,
            total_m2 numeric,
            m1 numeric,
            other_deposits_households numeric,
            other_deposits_fin_org numeric,
            other_deposits_nonfin_org numeric
        );
    """)

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
        rows
    )

    conn.commit()
    cur.close()
    conn.close()