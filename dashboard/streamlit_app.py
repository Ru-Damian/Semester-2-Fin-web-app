import streamlit as st
from datetime import date, timedelta
import requests
import pandas as pd

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Fin Web App",
    layout="wide"
)

def processing_column_name(col: str) -> str:
    if col == "date":
        col = "Дата"
    return col.replace("_", " ").title()

REST_MVP_INDICATORS = [
    {"name": "Денежный агрегат M2", "endpoint": "m2", "min_year": 2010},
    {"name": "Широкая денежная масса", "endpoint": "m2_broad", "min_year": 2010},
    {"name": "Номинальный курс", "endpoint": "exchange_rate", "min_year": 1999},
    {"name": "Средний номинальный курс", "endpoint": "avg_exchange_rate", "min_year": 1999},
    {"name": "Денежный агрегат M1", "endpoint": "m1", "min_year": 1992}
]

st.title("Выбранные параметры ЦБ РФ")

with st.sidebar:
    st.header("Параметры")
    st.subheader("Метрики")
    
    selected_metrics = []
    for item in REST_MVP_INDICATORS:
        if st.checkbox(item["name"], key=f"cb_{item["endpoint"]}"):
            selected_metrics.append(item)

    if not selected_metrics:
        min_possible_year = 2015
        max_possible_year = date.today().year
    else:
        min_possible_year = max(item["min_year"] for item in selected_metrics)
        max_possible_year = date.today().year

    years = list(range(min_possible_year, max_possible_year + 1))
    
    start_year = st.selectbox("Год начала", years, index=0)
    end_year = st.selectbox("Год конца", years, index=len(years)-1)

    load_clicked = st.button("Загрузить данные", width="stretch")

if not selected_metrics:
    st.info("Выберите метрики слева")
elif not load_clicked:
    st.info("Нажмите \"Загрузить данные\"")
elif start_year > end_year:
    st.error("Год начала не может быть позже года конца")
else:
    y1 = start_year
    y2 = end_year
    
    results = []
    for item in selected_metrics:
        endpoint = item["endpoint"]
        try:
            resp = requests.post(f"{API_BASE_URL}/{endpoint}/rebuild/{y1}/{y2}", timeout=60)
            resp.raise_for_status()
            payload = resp.json()
            results.append({"name": item["name"], "status": "success", "rows": payload.get("rows_inserted")})
        except Exception as e:
            results.append({"name": item["name"], "status": "error", "error": str(e)})
    
    for r in results:
        if r["status"] == "success":
            st.success(f"{r["name"]}: загружено {r["rows"]} строк")
        else:
            st.error(f"{r["name"]}: ошибка")
    
    tabs = st.tabs([item["name"] for item in selected_metrics])

    for idx, item in enumerate(selected_metrics):
        endpoint = item["endpoint"]
        with tabs[idx]:
            try:
                resp = requests.get(f"{API_BASE_URL}/{endpoint}/from-db", timeout=30)
                resp.raise_for_status()
                rows = resp.json().get("data", [])

                if rows:
                    df = pd.DataFrame(rows)
                    chart_tab, table_tab = st.tabs(["График", "Таблица"])

                    with chart_tab:
                        numeric_cols = [c for c in df.columns if c != "date" and pd.api.types.is_numeric_dtype(df[c])]
                        if numeric_cols:
                            plot_cols = numeric_cols[:5]
                            chart_df = df[["date"] + plot_cols].copy()
                            chart_df["date"] = pd.to_datetime(chart_df["date"])
                            chart_df = chart_df.set_index("date")
                            chart_df = chart_df.rename(columns=processing_column_name)
                            st.line_chart(chart_df, height=350)

                    with table_tab:
                        display_df = df.head(30).copy()
                        display_df["date"] = pd.to_datetime(display_df["date"]).dt.strftime("%Y-%m-%d")
                        display_df = display_df.rename(columns=processing_column_name)
                        st.dataframe(display_df, width="stretch")
                else:
                    st.info("Нет данных")
            except Exception as e:
                st.error(f"Ошибка: {e}")