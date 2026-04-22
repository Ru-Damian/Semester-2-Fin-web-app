"""
Модуль подготовки данных по метрике M2.

Содержит функции для:
- загрузки сырых данных из API ЦБ РФ;
- построения очищенной wide-таблицы.
"""

import pandas as pd
import requests

PUBLICATION_ID = 5
DATASET_ID = 7

def load_cbr_data(y1: int, y2: int) -> dict:
    """
    Загружает сырой JSON по метрике M2 из API ЦБ РФ.

    :param y1: Начальный год периода
    :type y1: int
    :param y2: Конечный год периода
    :type y2: int
    :return: JSON-ответ API ЦБ РФ в виде словаря
    :rtype: dict
    """
    response = requests.get(
        "https://www.cbr.ru/dataservice/data",
        params={
            "y1": y1,
            "y2": y2,
            "publicationId": PUBLICATION_ID,
            "datasetId": DATASET_ID
        },
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def build_m2_clean_table(y1: int, y2: int) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """
    Создает очищенную таблицу по метрике M2.

    :param y1: Начальный год периода
    :type y1: int
    :param y2: Конечный год периода
    :type y2: int
    :return: Кортеж (исходный JSON-ответ API, 
                    long-таблица после первичной очистки,
                    wide-таблица с основными колонками M2)
    :rtype: tuple[dict, pd.DataFrame, pd.DataFrame]
    """
    data = load_cbr_data(y1, y2)
    df = pd.DataFrame(data["RawData"])

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

    wide_df = wide_df.rename(
        columns={
            "Всего": "total_m2",
            "Денежный агрегат М1": "m1",
            "Другие депозиты домашних хозяйств": "other_deposits_households",
            "Другие депозиты других финансовых организаций": "other_deposits_fin_org",
            "Другие депозиты нефинансовых организаций": "other_deposits_nonfin_org"
        }
    )

    wide_df = wide_df.sort_values("date").reset_index(drop=True)

    return data, df, wide_df