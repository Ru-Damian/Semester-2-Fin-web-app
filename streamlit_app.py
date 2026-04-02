import streamlit as st
from datetime import date, timedelta

st.set_page_config(
    page_title='MVP Dashboard ЦБ РФ',
    layout='wide'
)

# показатели REST API 
REST_MVP_INDICATORS = [
    {
        "name": "Денежный агрегат M2",
        "category_id": 5,
        "indicator_id": 7,
        "why": "Базовый показатель денежной массы."
    },
    {
        "name": "Широкая денежная масса",
        "category_id": 5,
        "indicator_id": 8,
        "why": "Дополняет анализ ликвидности и денежного предложения."
    },
    {
        "name": "Номинальный курс",
        "category_id": 33,
        "indicator_id": 127,
        "why": "Позволяет отслеживать динамику курса рубля."
    },
    {
        "name": "Средний номинальный курс за период",
        "category_id": 33,
        "indicator_id": 128,
        "why": "Подходит для сравнения периодов и отчетов."
    },
    {
        "name": "Индекс реального эффективного курса рубля к иностранным валютам",
        "category_id": 34,
        "indicator_id": 132,
        "why": "Показывает более широкий внешний контекст курса рубля."
    },
]


st.title('Веб-приложение для финансовых аналитиков')

st.markdown("### Полезные ссылки")
link_col1, link_col2 = st.columns(2)

with link_col1:
    st.page_link("https://www.cbr.ru/dataservice/categoryNew", label="Список категорий и показателей ЦБ")
    st.page_link("https://www.cbr.ru/statistics/data-service/APIdocumentation/examples/", label="Примеры работы с API на Python")
    st.page_link("https://www.cbr.ru/statistics/data-service/APIdocumentation/", label="Документация API")
    st.page_link("https://www.cbr.ru/statistics/data-service/", label="Обзор раздела «Статистика / Data‑service» ЦБ")
with link_col2:
    st.page_link("https://www.cbr.ru/dataservice/swagger", label="Swagger ЦБ РФ")
    st.page_link("https://github.com/mbk-dev/cbrapi", label="Библиотека cbrapi (GitHub)")
    st.page_link("https://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx?op=KeyRateXML", label="SOAP документация KeyRateXML")
    st.page_link("http://127.0.0.1:8000/docs", label="Локальная документация FastAPI (M2)")

st.divider()

with st.expander("Показать список REST-показателей MVP"):
    for item in REST_MVP_INDICATORS:
        st.markdown(
            f"""
            **{item['name']}**  
            - category_id: `{item['category_id']}`  
            - indicator_id: `{item['indicator_id']}`  
            - Назначение: {item['why']}
            """
        )

st.divider()