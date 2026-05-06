"""
Модуль сервисных функций для работы со сводками к метрикам.

Содержит функции для:
- создания краткого описания для метрики.
"""
import pandas as pd


def build_summary(metric_name: str, df: pd.DataFrame) -> str:
    """
    Создает краткое описание для метрики.

    :param metric_name: Название метрики
    :type metric_name: str
    :param df: Конечный год периода
    :type df: pd.DataFrame
    :return: Краткое описание для метрики
    :rtype: str
    """
    if "date" not in df.columns:
        return f"{metric_name}: недостаточно данных для оценки динамики."

    numeric_cols = [
        c for c in df.columns
        if c != "date" and pd.api.types.is_numeric_dtype(df[c])
    ]
    if not numeric_cols:
        return f"{metric_name}: недостаточно данных для оценки динамики."

    value_col = numeric_cols[0]

    work_df = df[["date", value_col]].copy()
    work_df["date"] = pd.to_datetime(work_df["date"], errors="coerce")
    work_df[value_col] = pd.to_numeric(work_df[value_col], errors="coerce")
    work_df = work_df.dropna().sort_values("date")

    if len(work_df) < 2:
        return f"{metric_name}: недостаточно данных для оценки динамики."

    first_value = float(work_df.iloc[0][value_col])
    last_value = float(work_df.iloc[-1][value_col])
    delta = last_value - first_value

    if first_value != 0:
        pct = (delta / first_value) * 100
        pct_text = f"{pct:+.2f}%"
    else:
        pct_text = "н/д"

    if delta > 0:
        trend = "вырос"
    elif delta < 0:
        trend = "снизился"
    else:
        trend = "не изменился"

    return (
        f"{metric_name}: {trend} с {first_value:.2f} до {last_value:.2f} "
        f"({delta:+.2f}; {pct_text})."
    )