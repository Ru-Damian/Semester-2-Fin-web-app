"""
Модуль подготовки данных по метрике.

Содержит функции для:
- загрузки сырых данных из API ЦБ РФ;
- построения очищенной wide-таблицы.
"""

import pandas as pd
import requests


def load_cbr_data(y1: int, y2: int, publication_id:int, dataset_id:int) -> dict:
    """
    Загружает сырой JSON по метрике, заданной двумя индитификаторами, из API ЦБ РФ.

    :param y1: Начальный год периода
    :type y1: int
    :param y2: Конечный год периода
    :type y2: int
    :param publication_id: Первый индитификатор метрики
    :type publication_id: int
    :param dataset_id: Второй индитификатор метрики
    :type dataset_id: int
    :return: JSON-ответ API ЦБ РФ в виде словаря
    :rtype: dict
    """
    response = requests.get(
        "https://www.cbr.ru/dataservice/data",
        params={
            "y1": y1,
            "y2": y2,
            "publicationId": publication_id,
            "datasetId": dataset_id
        },
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def build_metric_clean_table(y1: int, y2: int, publication_id:int, dataset_id:int) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """
    Создает очищенную таблицу по метрике.

    :param y1: Начальный год периода
    :type y1: int
    :param y2: Конечный год периода
    :type y2: int
    :param publication_id: Первый индитификатор метрики
    :type publication_id: int
    :param dataset_id: Второй индитификатор метрики
    :type dataset_id: int
    :return: Кортеж (исходный JSON-ответ API, 
                    long-таблица после первичной очистки,
                    wide-таблица с основными колонками метрики)
    :rtype: tuple[dict, pd.DataFrame, pd.DataFrame]
    """
    data = load_cbr_data(y1, y2, publication_id, dataset_id)
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

    column_rename = {}
    for col in wide_df.columns:
        if col != "date":
            col_lower = col.lower().replace(" ", "_").replace("(", "").replace(")", "")
            column_rename[col] = col_lower

    wide_df = wide_df.rename(columns=column_rename)
    wide_df = wide_df.sort_values("date").reset_index(drop=True)

    return data, df, wide_df