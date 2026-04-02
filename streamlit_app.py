import streamlit as st

st.set_page_config(
    page_title='Fin-web-app',
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

st.markdown("### Источники ЦБ")
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


st.markdown("### Локальные ссылки FastAPI")

local_col1, local_col2 = st.columns(2)

with local_col1:
    st.page_link(
        "http://127.0.0.1:8000/docs",
        label="Докальная документация FastAPI (M2)",
        
    )
    st.page_link(
        "http://127.0.0.1:8000/m2/2024/2025",
        label="Сырой JSON M2 (2024–2025)",
        
    )
    st.page_link(
        "http://127.0.0.1:8000/m2-short/2024/2025",
        label="Короткий ответ M2 (2024–2025)",
    )

with local_col2:
    st.page_link(
        "http://127.0.0.1:8000/m2-table-preview/2024/2025",
        label="Предпросмотр таблицы M2 как стала DataFrame (2024–2025)",
    )
    st.page_link(
        "http://127.0.0.1:8000/m2-clean-table/2024/2025",
        label="Очищенная таблица M2 до БД(2024–2025)",
    
    )
    st.page_link(
        "http://127.0.0.1:8000/m2-from-db",
        label="M2 из локальной БД",
    )


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