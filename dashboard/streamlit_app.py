import pandas as pd
import requests
import streamlit as st

from pathlib import Path
from datetime import date, datetime
from io import BytesIO
import json

from summary_service import build_summary

API_BASE_URL = "http://127.0.0.1:8000"
PRESETS_FILE = Path(__file__).resolve().parent / "presets.json"
LOG_FILE = Path(__file__).resolve().parent / "app.log"
TEST_API_ERROR = False  # True - включить тестовую ошибку API
TEST_UPLOAD_ERROR = True  # True - включить тестовую ошибку загрузки

st.set_page_config(
    page_title="Fin Web App",
    layout="wide"
)

REST_MVP_INDICATORS = [
    {"name": "Денежный агрегат M2", "endpoint": "m2", "min_year": 2010},
    {"name": "Широкая денежная масса", "endpoint": "m2_broad", "min_year": 2010},
    {"name": "Номинальный курс", "endpoint": "exchange_rate", "min_year": 1999},
    {"name": "Средний номинальный курс", "endpoint": "avg_exchange_rate", "min_year": 1999},
    {"name": "Денежный агрегат M1", "endpoint": "m1", "min_year": 1992}
]


def processing_column_name(col: str) -> str:
    """
    Преобразовывает название столбца в "чистый" формат для пользователя.
    Меняет "_" на пробел, делает первую букву заглавной и переводит название с английского языка на русский.

    :param col: Название столбца
    :type col: str
    :return: Чистое название столбца
    :rtype: str
    """
    if col == "date":
        col = "Дата"
    return col.replace("_", " ").title()


def get_selected_metric_endpoints() -> list[str]:
    """
    Получает список эндпоинтов выбранных метрик из состояния сессии.

    :return: Список эндпоинтов выбранных метрик
    :rtype: list[str]
    """
    result = []
    for item in REST_MVP_INDICATORS:
        if st.session_state.get(f"cb_{item['endpoint']}", False):
            result.append(item["endpoint"])
    return result


def get_selected_metrics() -> list[dict]:
    """
    Получает полные словари выбранных метрик.

    :return: Список словарей с данными выбранных метрик
    :rtype: list[dict]
    """
    selected_endpoints = set(get_selected_metric_endpoints())
    return [item for item in REST_MVP_INDICATORS if item["endpoint"] in selected_endpoints]


def get_year_bounds_for_selected_metrics(selected_metrics: list[dict]) -> tuple[int, int]:
    """
    Определяет минимально возможный год начала для выбранных метрик.

    :param selected_metrics: Список выбранных метрик с полями min_year
    :type selected_metrics: list[dict]
    :return: Кортеж (минимальный год начала, текущий год)
    :rtype: tuple[int, int]
    """
    if not selected_metrics:
        return 2015, date.today().year
    return max(item["min_year"] for item in selected_metrics), date.today().year


def sync_year_widgets_with_bounds():
    """
    Создает список годов для виджета на боковой панели.
    Если текущие значения годов выходят за допустимые пределы, автоматически корректирует их.
    """
    if st.session_state.get("_skip_sync", False):
        st.session_state["_skip_sync"] = False
        return
    selected_metrics = get_selected_metrics()
    min_possible_year, max_possible_year = get_year_bounds_for_selected_metrics(selected_metrics)
    years = list(range(min_possible_year, max_possible_year + 1))

    current_start = st.session_state.get("start_year_widget")
    current_end = st.session_state.get("end_year_widget")

    if current_start not in years:
        st.session_state["start_year_widget"] = years[0]
    if current_end not in years:
        st.session_state["end_year_widget"] = years[-1]


def write_error_log(metric_name: str, y1: int, y2: int, error_text: str) -> None:
    """
    Записывает информацию об ошибке загрузки метрики в лог-файл.

    :param metric_name: Название метрики, при загрузке которой произошла ошибка
    :type metric_name: str
    :param y1: Начальный год периода
    :type y1: int
    :param y2: Конечный год периода
    :type y2: int
    :param error_text: Текст ошибки
    :type error_text: str
    :return: None
    :rtype: None
    """
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    log_line = f"[{timestamp}] metric={metric_name} | period={y1}-{y2} | error={error_text}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)


def load_data_for_selected_metrics():
    """
    Загружает данные для выбранных метрик за указанный период из API.

    Выполняет POST запросы для загрузки данных, затем GET запросы для их получения.
    Результаты сохраняются в session_state (loaded_dataframes, last_loaded_params).

    :return: None
    :rtype: None
    """
    selected_metrics = get_selected_metrics()
    start_year = st.session_state.get("start_year_widget")
    end_year = st.session_state.get("end_year_widget")

    if not selected_metrics:
        st.session_state["action_message"] = ("warning", "Сначала выберите хотя бы одну метрику.")
        return

    if start_year is None or end_year is None:
        st.session_state["action_message"] = ("warning", "Сначала выберите диапазон лет.")
        return

    if start_year > end_year:
        st.session_state["action_message"] = ("error", "Год начала не может быть позже года конца.")
        return

    y1 = start_year
    y2 = end_year
    updated_at = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    results = []

    for item in selected_metrics:
        endpoint = item["endpoint"]
        try:
            if TEST_API_ERROR:
                raise Exception("ТЕСТ: имитация недоступности API ЦБ РФ")
            resp = requests.post(f"{API_BASE_URL}/{endpoint}/rebuild/{y1}/{y2}", timeout=15)
            resp.raise_for_status()
            payload = resp.json()
            results.append({
                "name": item["name"],
                "status": "success",
                "rows": payload.get("rows_inserted")
            })
        except Exception as e:
            write_error_log(item["name"], y1, y2, str(e))
            results.append({
                "name": item["name"],
                "status": "error",
                "error": str(e)
            })

    loaded_dataframes: dict[str, pd.DataFrame] = {}
    total_rows_for_export = 0

    for item in selected_metrics:
        endpoint = item["endpoint"]
        try:
            resp = requests.get(f"{API_BASE_URL}/{endpoint}/from-db", timeout=30)
            resp.raise_for_status()
            rows = resp.json().get("data", [])
            if rows:
                df = pd.DataFrame(rows)
                loaded_dataframes[item["name"]] = df
                total_rows_for_export += len(df)
        except Exception:
            pass

    st.session_state["loaded_dataframes"] = loaded_dataframes
    st.session_state["last_loaded_params"] = {
        "y1": y1,
        "y2": y2,
        "updated_at": updated_at,
        "results": results,
        "total_rows_for_export": total_rows_for_export,
    }


def build_csv_file(dataframes: dict[str, pd.DataFrame]) -> bytes:
    """
    Сохраняет все выбранные метрики в CSV файл.

    :param dataframes: Словарь с парами {"название метрики": DataFrame}
    :type dataframes: dict[str, pd.DataFrame]
    :return: Байтовое представление CSV файла
    :rtype: bytes
    """
    combined_parts = []
    for sheet_name, df in dataframes.items():
        export_df = df.copy()
        if "date" in export_df.columns:
            export_df["date"] = pd.to_datetime(export_df["date"]).dt.strftime("%Y-%m-%d")
        export_df = export_df.rename(columns=processing_column_name)
        combined_parts.append(f"### {sheet_name}")
        combined_parts.append(export_df.to_csv(index=False))
        combined_parts.append("")
    return "\n".join(combined_parts).encode("utf-8-sig")


def build_excel_file(dataframes: dict[str, pd.DataFrame]) -> bytes:
    """
    Сохраняет все выбранные метрики в Excel файл.

    :param dataframes: Словарь с парами {"название метрики": DataFrame}
    :type dataframes: dict[str, pd.DataFrame]
    :return: Байтовое представление Excel файла
    :rtype: bytes
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for sheet_name, df in dataframes.items():
            export_df = df.copy()
            if "date" in export_df.columns:
                export_df["date"] = pd.to_datetime(export_df["date"]).dt.strftime("%Y-%m-%d")
            export_df = export_df.rename(columns=processing_column_name)
            safe_sheet_name = sheet_name[:31]
            export_df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
    return output.getvalue()


def load_presets() -> dict:
    """
    Загружает сохраненные пресеты слотов из JSON файла.

    :return: Словарь с данными пресетов
    :rtype: dict
    """
    if not PRESETS_FILE.exists():
        return {}

    try:
        with open(PRESETS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_presets(presets: dict):
    """
    Сохраняет словарь пресетов в JSON файл с форматированием.

    :param presets: Словарь с данными пресетов для сохранения
    :type presets: dict
    :return: None
    :rtype: None
    """
    with open(PRESETS_FILE, "w", encoding="utf-8") as f:
        json.dump(presets, f, ensure_ascii=False, indent=2)


def get_slot_labels(presets: dict) -> dict:
    """
    Извлекает пользовательские названия слотов из словаря пресетов.

    :param presets: Словарь с названиями пресетов
    :type presets: dict
    :return: Словарь с парами {номер_слота: название}
    :rtype: dict
    """
    labels = presets.get("_slot_labels", {})
    return labels if isinstance(labels, dict) else {}


def save_current_slot_label():
    """
    Сохраняет пользовательское название для текущего выбранного слота.

    Читает значение из session_state, обновляет словарь меток и сохраняет пресеты.
    При пустом названии удаляет метку для слота.

    :return: None
    :rtype: None
    """
    presets = load_presets()
    labels = get_slot_labels(presets)

    slot = st.session_state["selected_slot"]
    label = st.session_state.get("slot_custom_name", "").strip()

    if label:
        labels[slot] = label
    else:
        labels.pop(slot, None)

    presets["_slot_labels"] = labels
    save_presets(presets)
    st.session_state["action_message"] = ("success", f"Название для слота {slot} сохранено.")


def build_slot_payload(metric_endpoints: list[str], start_year: int, end_year: int) -> dict:
    """
    Формирует словарь с параметрами слота для сохранения в пресет.

    :param metric_endpoints: Список эндпоинтов выбранных метрик
    :type metric_endpoints: list[str]
    :param start_year: Начальный год периода
    :type start_year: int
    :param end_year: Конечный год периода
    :type end_year: int
    :return: Словарь с параметрами слота
    :rtype: dict
    """
    return {
        "metric_endpoints": metric_endpoints,
        "y1": start_year,
        "y2": end_year
    }


def get_slot_status_text(slot_data: dict | None) -> str:
    """
    Формирует текстовое описание состояния слота с эмодзи.

    :param slot_data: Данные слота (словарь) или None для пустого слота
    :type slot_data: dict | None
    :return: Текстовое описание состояния слота
    :rtype: str
    """
    if not slot_data:
        return "🟢 Слот свободен"

    metric_count = len(slot_data.get("metric_endpoints", []))
    y1 = slot_data.get("y1", "—")
    y2 = slot_data.get("y2", "—")
    return f"🔴 В слоте: {metric_count} метрики, {y1}–{y2}"


def apply_pending_changes():
    """
    Применяет отложенные изменения к виджетам ДО их создания.

    :return: None
    :rtype: None
    """

    pending_metrics = st.session_state.get("pending_metric_endpoints")
    if pending_metrics is not None:
        for item in REST_MVP_INDICATORS:
            st.session_state[f"cb_{item['endpoint']}"] = item["endpoint"] in pending_metrics
        st.session_state["pending_metric_endpoints"] = None

    pending_start = st.session_state.get("pending_start_year")
    pending_end = st.session_state.get("pending_end_year")

    if pending_start is not None and pending_end is not None:
        selected_metrics = get_selected_metrics()
        min_possible_year, max_possible_year = get_year_bounds_for_selected_metrics(selected_metrics)

        start_year = max(pending_start, min_possible_year)
        end_year = min(pending_end, max_possible_year)

        st.session_state["start_year_widget"] = start_year
        st.session_state["end_year_widget"] = end_year

        st.session_state["pending_start_year"] = None
        st.session_state["pending_end_year"] = None

    if st.session_state.get("should_load_data", False):
        st.session_state["loaded_dataframes"] = {}
        st.session_state["last_loaded_params"] = None
        st.session_state["should_load_data"] = False
        load_data_for_selected_metrics()


def on_save_slot():
    """
    Обработчик сохранения текущей конфигурации в выбранный слот.

    Проверяет наличие выбранных метрик и корректность диапазона лет.
    Если слот занят, устанавливает флаг для подтверждения перезаписи.
    При успешном сохранении обновляет пресеты в JSON файле.

    :return: None
    :rtype: None
    """
    presets = load_presets()
    selected_slot = st.session_state["selected_slot"]

    metric_endpoints = get_selected_metric_endpoints()
    start_year = st.session_state.get("start_year_widget")
    end_year = st.session_state.get("end_year_widget")

    if not metric_endpoints:
        st.session_state["action_message"] = ("warning", "Сначала выберите хотя бы одну метрику.")
        return

    if start_year is None or end_year is None:
        st.session_state["action_message"] = ("warning", "Сначала выберите диапазон лет.")
        return

    if start_year > end_year:
        st.session_state["action_message"] = ("warning", "Год начала не может быть позже года конца.")
        return

    slot_is_occupied = presets.get(selected_slot) is not None
    if slot_is_occupied:
        st.session_state["overwrite_requested"] = True
        st.session_state["target_slot_for_overwrite"] = selected_slot
        return

    presets[selected_slot] = build_slot_payload(metric_endpoints, start_year, end_year)
    save_presets(presets)
    st.session_state["action_message"] = ("success", f"Сохранено в слот {selected_slot}.")


def on_confirm_overwrite():
    """
    Обработчик подтверждения перезаписи занятого слота.

    Перезаписывает данные в указанном слоте новой конфигурацией.
    Сбрасывает флаги состояния перезаписи после выполнения.

    :return: None
    :rtype: None
    """
    presets = load_presets()
    target_slot = st.session_state.get("target_slot_for_overwrite")

    metric_endpoints = get_selected_metric_endpoints()
    start_year = st.session_state.get("start_year_widget")
    end_year = st.session_state.get("end_year_widget")

    if not target_slot:
        st.session_state["action_message"] = ("warning", "Слот для перезаписи не выбран.")
        return

    presets[target_slot] = build_slot_payload(metric_endpoints, start_year, end_year)
    save_presets(presets)

    st.session_state["overwrite_requested"] = False
    st.session_state["target_slot_for_overwrite"] = None
    st.session_state["action_message"] = ("success", f"Слот {target_slot} перезаписан.")


def on_cancel_overwrite():
    """
    Обработчик отмены перезаписи занятого слота.

    Сбрасывает флаги состояния перезаписи и очищает информацию о целевом слоте.

    :return: None
    :rtype: None
    """
    st.session_state["overwrite_requested"] = False
    st.session_state["target_slot_for_overwrite"] = None
    st.session_state["action_message"] = ("info", "Перезапись отменена.")


def on_load_slot():
    """
    Обработчик загрузки конфигурации из выбранного слота.
    Сохраняет данные в session_state и вызывает перезапуск.
    """
    presets = load_presets()
    selected_slot = st.session_state["selected_slot"]
    slot_data = presets.get(selected_slot)

    if not slot_data:
        st.session_state["action_message"] = ("warning", "Этот слот пуст.")
        return

    metric_endpoints = slot_data.get("metric_endpoints", [])
    start_year = slot_data.get("y1")
    end_year = slot_data.get("y2")

    st.session_state["pending_metric_endpoints"] = metric_endpoints
    st.session_state["pending_start_year"] = start_year
    st.session_state["pending_end_year"] = end_year
    st.session_state["should_load_data"] = True
    st.session_state["_skip_sync"] = True
    st.session_state["action_message"] = ("success", f"Слот {selected_slot} загружен.")

    st.rerun()


if "pending_start_year" not in st.session_state:
    st.session_state["pending_start_year"] = None

if "pending_end_year" not in st.session_state:
    st.session_state["pending_end_year"] = None

if "should_load_data" not in st.session_state:
    st.session_state["should_load_data"] = False

if "overwrite_requested" not in st.session_state:
    st.session_state["overwrite_requested"] = False

if "target_slot_for_overwrite" not in st.session_state:
    st.session_state["target_slot_for_overwrite"] = None

if "action_message" not in st.session_state:
    st.session_state["action_message"] = None

if "selected_slot" not in st.session_state:
    st.session_state["selected_slot"] = "1"

if "slot_custom_name" not in st.session_state:
    st.session_state["slot_custom_name"] = ""

if "loaded_dataframes" not in st.session_state:
    st.session_state["loaded_dataframes"] = {}

if "last_loaded_params" not in st.session_state:
    st.session_state["last_loaded_params"] = None

if "_skip_sync" not in st.session_state:
    st.session_state["_skip_sync"] = False

apply_pending_changes()

st.title("Выбранные параметры ЦБ РФ")

with st.sidebar:
    st.header("Параметры")

    st.subheader("Метрики")

    message = st.session_state.get("action_message")
    if message:
        level, text = message
        if level == "success":
            st.success(text)
        elif level == "warning":
            st.warning(text)
        elif level == "info":
            st.info(text)
        elif level == "error":
            st.error(text)
        st.session_state["action_message"] = None

    for item in REST_MVP_INDICATORS:
        st.checkbox(item["name"], key=f"cb_{item['endpoint']}")

    selected_metrics = get_selected_metrics()
    min_possible_year, max_possible_year = get_year_bounds_for_selected_metrics(selected_metrics)
    years = list(range(min_possible_year, max_possible_year + 1))

    saved_start_year = st.session_state.get("start_year_saved")
    saved_end_year = st.session_state.get("end_year_saved")

    if "start_year_widget" not in st.session_state:
        st.session_state["start_year_widget"] = saved_start_year if saved_start_year in years else years[0]

    if "end_year_widget" not in st.session_state:
        st.session_state["end_year_widget"] = saved_end_year if saved_end_year in years else years[-1]

    if saved_start_year in years:
        st.session_state["start_year_widget"] = saved_start_year
        st.session_state["start_year_saved"] = None

    if saved_end_year in years:
        st.session_state["end_year_widget"] = saved_end_year
        st.session_state["end_year_saved"] = None

    sync_year_widgets_with_bounds()

    st.selectbox("Год начала", years, key="start_year_widget")
    st.selectbox("Год конца", years, key="end_year_widget")

    if st.button("Загрузить или обновить", type="primary"):
        load_data_for_selected_metrics()

    st.subheader("Мои конфигурации")

    presets = load_presets()
    slot_labels = get_slot_labels(presets)

    slot_display_map = {}
    slot_display_options = []

    for i in range(1, 11):
        slot = str(i)
        label = slot_labels.get(slot, "").strip()
        display_value = f"{slot} — {label}" if label else slot
        slot_display_map[display_value] = slot
        slot_display_options.append(display_value)

    current_slot = st.session_state["selected_slot"]
    current_label = slot_labels.get(current_slot, "").strip()
    current_display_value = f"{current_slot} — {current_label}" if current_label else current_slot

    selected_slot_display = st.selectbox(
        "Слот конфигурации",
        slot_display_options,
        index=slot_display_options.index(current_display_value)
    )

    selected_slot = slot_display_map[selected_slot_display]

    slot_changed = selected_slot != st.session_state["selected_slot"]
    st.session_state["selected_slot"] = selected_slot

    if slot_changed:
        st.session_state["slot_custom_name"] = slot_labels.get(selected_slot, "")

    current_slot_data = presets.get(st.session_state["selected_slot"])
    st.markdown(get_slot_status_text(current_slot_data))

    st.text_input(
        "Название слота",
        key="slot_custom_name",
        placeholder="Например: Курсы и M2"
    )

    if st.button("Переименовать слот"):
        save_current_slot_label()

    col_slot_1, col_slot_2 = st.columns(2)
    with col_slot_1:
        if st.button("Сохранить"):
            on_save_slot()
    with col_slot_2:
        if st.button("Загрузить"):
            on_load_slot()

    if st.session_state.get("overwrite_requested", False):
        target_slot = st.session_state["target_slot_for_overwrite"]
        st.warning(f"⚠️ Слот {target_slot} уже содержит данные. Перезаписать?")
        col_yes, col_no = st.columns(2)

        with col_yes:
            st.button(
                "✅ Да, перезаписать",
                key="btn_confirm_overwrite",
                on_click=on_confirm_overwrite,
            )
        with col_no:
            st.button(
                "❌ Отмена",
                key="btn_cancel_overwrite",
                on_click=on_cancel_overwrite,
            )


selected_metrics = get_selected_metrics()
start_year = st.session_state.get("start_year_widget")
end_year = st.session_state.get("end_year_widget")
stored_data = st.session_state.get("loaded_dataframes", {})
last_loaded = st.session_state.get("last_loaded_params")

if not selected_metrics:
    st.info("Выберите метрики слева")
elif start_year is None or end_year is None:
    st.info("Выберите диапазон лет")
elif start_year > end_year:
    st.error("Год начала не может быть позже года конца")
elif not last_loaded or not stored_data:
    st.info("Нажмите \"Загрузить или обновить\"")
else:
    y1 = last_loaded["y1"]
    y2 = last_loaded["y2"]
    updated_at = last_loaded["updated_at"]
    results = last_loaded["results"]
    total_rows_for_export = last_loaded["total_rows_for_export"]
    loaded_dataframes = stored_data

    for r in results:
        if r["status"] == "success":
            st.success(
                f"{r['name']}: загружено {r['rows']} строк "
                f"за период {y1}–{y2}. Обновлено: {updated_at}"
            )
        else:
            st.warning(
                f"{r['name']}: не обновлён за период {y1}–{y2}. "
                f"Не получилось соединиться с сервером ЦБ РФ."
            )

    tabs = st.tabs([item["name"] for item in selected_metrics])

    for idx, item in enumerate(selected_metrics):
        metric_name = item["name"]
        with tabs[idx]:
            df = loaded_dataframes.get(metric_name)
            if df is None or df.empty:
                st.info("Нет данных")
                continue

            chart_tab, table_tab = st.tabs(["График", "Таблица"])

            with chart_tab:
                numeric_cols = [
                    c for c in df.columns
                    if c != "date" and pd.api.types.is_numeric_dtype(df[c])
                ]
                if numeric_cols:
                    plot_cols = numeric_cols[:5]
                    chart_df = df[["date"] + plot_cols].copy()
                    chart_df["date"] = pd.to_datetime(chart_df["date"])
                    chart_df = chart_df.set_index("date")
                    chart_df = chart_df.rename(columns=processing_column_name)
                    st.line_chart(chart_df, height=350)

            with table_tab:
                display_df = df.head(30).copy()
                if "date" in display_df.columns:
                    display_df["date"] = pd.to_datetime(display_df["date"]).dt.strftime("%Y-%m-%d")
                display_df = display_df.rename(columns=processing_column_name)
                st.dataframe(display_df, width="stretch")

    if loaded_dataframes:
        st.subheader("Сводка")
        for metric_name, df in loaded_dataframes.items():
            st.write("- " + build_summary(metric_name, df))

        if total_rows_for_export > 15000 or TEST_UPLOAD_ERROR:
            st.warning("Скачивание недоступно. Слишком большой размер выгрузки. Ограничьте период или уменьшите количество показателей.")
        else:
            csv_bytes = build_csv_file(loaded_dataframes)
            excel_bytes = build_excel_file(loaded_dataframes)

            col1, col2, _ = st.columns([1, 1, 10])
            with col1:
                st.download_button(
                    label="Экспорт в CSV",
                    data=csv_bytes,
                    file_name=f"cbrf_export_{y1}_{y2}.csv",
                    mime="text/csv",
                    on_click="ignore"
                )
            with col2:
                st.download_button(
                    label="Экспорт в Excel",
                    data=excel_bytes,
                    file_name=f"cbrf_export_{y1}_{y2}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    on_click="ignore"
                )