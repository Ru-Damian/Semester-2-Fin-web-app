from fastapi import FastAPI, HTTPException
import requests
from table_builder import load_cbr_data, build_m2_dataframe, build_m2_clean_table
from db_reader import read_m2_clean_table

app = FastAPI()


@app.get("/m2-from-db")
def get_m2_from_db():
    """Читает очищенную таблицу M2 из PostgreSQL."""
    try:
        rows = read_m2_clean_table()
        return {
            "row_count": len(rows),
            "data": rows
        }
    except Exception as e:
        return {
            "error_type": type(e).__name__,
            "error_text": str(e)
        }


@app.get("/m2/{y1}/{y2}")
def get_m2(y1: int, y2: int):
    """Загружает сырой JSON по M2 из API."""
    try:
        return load_cbr_data(y1, y2)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ошибка запроса к ЦБ: {e}")


@app.get("/m2-short/{y1}/{y2}")
def get_m2_short(y1: int, y2: int):
    """Возвращает из API заданные параментры."""
    try:
        data = load_cbr_data(y1, y2)
        return {
            "date_range": data["DTRange"],
            "dataset_name": data["SType"][0]["dsName"],
            "publication_name": data["SType"][0]["PublName"],
            "headers": data["headerData"],
            "units": data["units"],
            "raw_count": len(data["RawData"]),
            "raw_preview": data["RawData"][:10],
        }
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ошибка запроса к ЦБ: {e}")


@app.get("/m2-table-preview/{y1}/{y2}")
def get_m2_table_preview(y1: int, y2: int):
    """Показывает предварительный просмотр DataFrame по M2."""
    try:
        data, df = build_m2_dataframe(y1, y2)
        return {
            "date_range": data["DTRange"],
            "dataset_name": data["SType"][0]["dsName"],
            "publication_name": data["SType"][0]["PublName"],
            "headers": data["headerData"],
            "units": data["units"],
            "columns": df.columns.tolist(),
            "row_count": len(df),
            "preview": df.head(10).to_dict(orient="records"),
        }
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ошибка запроса к ЦБ: {e}")


@app.get("/m2-clean-table/{y1}/{y2}")
def get_m2_clean_table(y1: int, y2: int):
    """Формирует таблицу M2."""
    try:
        data, long_df, wide_df = build_m2_clean_table(y1, y2)
        return {
            "dataset_name": data["SType"][0]["dsName"],
            "publication_name": data["SType"][0]["PublName"],
            "row_count_long": len(long_df),
            "row_count_wide": len(wide_df),
            "columns_wide": wide_df.columns.tolist(),
            "preview_wide": wide_df.head(10).to_dict(orient="records"),
        }
    except Exception as e:
        return {
            "error_type": type(e).__name__,
            "error_text": str(e)
        }