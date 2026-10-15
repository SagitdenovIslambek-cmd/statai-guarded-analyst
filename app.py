import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(
    page_title="StatAI | Official Statistics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
    .stApp { background: #0b1020; color: #eef2ff; }
    [data-testid="stSidebar"] { background: #11182b; }
    .hero {
        padding: 1.35rem 1.5rem;
        border: 1px solid #293653;
        border-radius: 18px;
        background: linear-gradient(120deg, #151f39, #101728);
        margin-bottom: 1rem;
    }
    .hero h1 { margin: 0; color: #f8fafc; font-size: 2.25rem; }
    .hero p { color: #b9c5dc; margin: .5rem 0 0 0; }
    .small-muted { color: #a7b4ce; font-size: .9rem; }
    .pill {
        display:inline-block; padding: .25rem .65rem; border-radius: 999px;
        border: 1px solid #3b4d70; color: #b9d4ff; background:#162442;
        font-size:.8rem; margin-right:.35rem;
    }
    div[data-testid="stMetric"] {
        background: #111a2d; border: 1px solid #263451;
        padding: 1rem; border-radius: 14px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <span class="pill">AI for Official Statistics</span>
  <span class="pill">Prototype · T001</span>
  <h1>StatAI</h1>
  <p>Guarded analyst for statistical microdata — ask a question, inspect the calculation, and review limitations.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## StatAI")
    st.caption("Guarded Statistical Analyst")
    page = st.radio("Навигация", ["Анализ данных", "Как это работает", "О проекте"])
    st.divider()
    st.markdown("### Загрузка данных")
    uploads = st.file_uploader(
        "Загрузите CSV-файлы T001",
        type=["csv"],
        accept_multiple_files=True,
        help="Можно загрузить 2021.csv, baza.csv, baza(1).csv и baza(2).csv. Не загружайте файлы других семейств вместо T001."
    )
    st.caption("Данные обрабатываются в рамках этой сессии приложения.")

EXPECTED = ["DH_POLRESP", "ZAN_RABOTA", "vosr", "DH_OBRAZOV"]

def read_uploaded(files):
    frames, errors = [], []
    for f in files:
        try:
            df = pd.read_csv(f, low_memory=False)
            df["__source_file"] = f.name
            frames.append(df)
        except Exception as e:
            errors.append(f"{f.name}: {e}")
    if frames:
        return pd.concat(frames, ignore_index=True, sort=False), errors
    return None, errors

def normalize_binary(series):
    # Accept numeric 0/1 and common string representations only.
    values = series.astype(str).str.strip().str.lower()
    mapping = {"1": 1, "1.0": 1, "yes": 1, "да": 1, "true": 1,
               "0": 0, "0.0": 0, "no": 0, "нет": 0, "false": 0}
    return values.map(mapping)

def safe_share(frame, group_col=None):
    work = frame.copy()
    work["_worked"] = normalize_binary(work["ZAN_RABOTA"])
    work = work[work["_worked"].isin([0, 1])]
    if work.empty:
        return pd.DataFrame(), "В переменной ZAN_RABOTA не найдены значения 0/1, которые можно безопасно интерпретировать."
    if group_col:
        work["_group"] = work[group_col].astype(str)
        out = work.groupby("_group", dropna=False)["_worked"].agg(["mean", "count"]).reset_index()
        out["Доля занятых, %"] = out["mean"] * 100
        out = out.rename(columns={"_group": "Группа", "count": "Число наблюдений"})
        return out[["Группа", "Доля занятых, %", "Число наблюдений"]], None
    share = work["_worked"].mean() * 100
    return pd.DataFrame([{"Показатель": "Доля занятых", "Значение, %": share,
                          "Число наблюдений": len(work)}]), None

if page == "Анализ данных":
    st.subheader("Запрос к статистическим данным")
    st.write("Выберите вопрос. В этом MVP используется проверяемый расчёт на Python; внешний LLM API не требуется.")
    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.selectbox(
            "Что хотите узнать?",
            [
                "Показать общую долю занятых",
                "Сравнить долю занятых по полу",
                "Сравнить долю занятых по возрастным группам",
                "Сравнить долю занятых по коду образования",
            ],
        )
    with col2:
        st.markdown("#### Data Guard")
        st.success("Расчёт разрешается только при наличии нужных полей.")

    if uploads:
        data, errors = read_uploaded(uploads)
        for err in errors:
            st.error(err)
        if data is not None:
            st.info(f"Загружено наблюдений: {len(data):,} · файлов: {len(uploads)}")
    else:
        data = None
        st.warning("Сначала загрузите CSV-файлы T001 в боковой панели. Без ваших файлов приложение не выдаёт выдуманные статистические результаты.")

    if data is not None:
        missing = [c for c in EXPECTED if c not in data.columns]
        with st.expander("Проверка структуры данных", expanded=bool(missing)):
            st.write("Найденные столбцы:", ", ".join(map(str, data.columns[:80])))
            if missing:
                st.error("Data Guard: отсутствуют ожидаемые поля: " + ", ".join(missing))
            else:
                st.success("Обнаружены ожидаемые поля T001.")

        if "ZAN_RABOTA" not in data.columns:
            st.error("Расчёт заблокирован: нет столбца ZAN_RABOTA.")
        else:
            group_col = None
            if query == "Сравнить долю занятых по полу":
                group_col = "DH_POLRESP"
            elif query == "Сравнить долю занятых по возрастным группам":
                if "vosr" in data.columns:
                    age = pd.to_numeric(data["vosr"], errors="coerce")
                    bins = [0, 19, 24, 34, 44, 54, 64, 120]
                    labels = ["до 19", "20–24", "25–34", "35–44", "45–54", "55–64", "65+"]
                    data = data.copy()
                    data["__age_group"] = pd.cut(age, bins=bins, labels=labels, right=True)
                    group_col = "__age_group"
                else:
                    st.error("Расчёт заблокирован: отсутствует поле vosr.")
            elif query == "Сравнить долю занятых по коду образования":
                group_col = "DH_OBRAZOV"

            if group_col and group_col not in data.columns:
                st.error(f"Расчёт заблокирован: отсутствует поле {group_col}.")
            elif query == "Показать общую долю занятых":
                result, err = safe_share(data)
                if err:
                    st.error(err)
                else:
                    metric = float(result.loc[0, "Значение, %"])
                    a, b, c = st.columns(3)
                    a.metric("Доля занятых", f"{metric:.2f}%")
                    b.metric("Валидных наблюдений", f"{int(result.loc[0, 'Число наблюдений']):,}")
                    c.metric("Столбец показателя", "ZAN_RABOTA")
                    st.dataframe(result, use_container_width=True, hide_index=True)
            elif group_col and group_col in data.columns:
                result, err = safe_share(data, group_col)
                if err:
                    st.error(err)
                elif result.empty:
                    st.warning("Нет данных для построения таблицы.")
                else:
                    result = result.dropna(subset=["Группа"])
                    st.dataframe(result, use_container_width=True, hide_index=True)
                    chart_data = result.set_index("Группа")["Доля занятых, %"]
                    st.bar_chart(chart_data)
                    st.download_button(
                        "Скачать таблицу CSV",
                        result.to_csv(index=False).encode("utf-8-sig"),
                        file_name="statai_result.csv",
                        mime="text/csv",
                    )
            st.divider()
            st.markdown("#### Методика и ограничения")
            st.write(
                "Показатель рассчитывается как среднее значение ZAN_RABOTA после распознавания кодов 0/1. "
                "Перед интерпретацией необходимо подтвердить значения кодов по официальному словарю переменных. "
                "Загруженные синтетические микроданные не являются официальными оценками населения Казахстана."
            )
            st.caption("Демонстрационный MVP. Расчёты выполняет Python; генеративная модель в этой версии не подключена.")

elif page == "Как это работает":
    st.subheader("Архитектура StatAI")
    steps = [
        ("01 · Запрос", "Пользователь выбирает вопрос на естественном языке."),
        ("02 · Planner", "Прототип направляет запрос к одному из поддерживаемых сценариев."),
        ("03 · Data Guard", "Проверяет наличие нужных полей и блокирует расчёт, если данных недостаточно."),
        ("04 · Python", "Pandas считает показатель воспроизводимым способом."),
        ("05 · Результат", "Таблица, график, методика и ограничения."),
    ]
    for title, desc in steps:
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.write(desc)
    st.warning("В текущей версии Planner основан на заранее заданных сценариях. Интеграция с внешней LLM требует отдельного API-доступа и тестирования.")

elif page == "О проекте":
    st.subheader("О проекте")
    st.write("StatAI — прототип безопасного аналитического помощника для официальной статистики.")
    st.markdown("""
**Цель:** сделать статистический анализ доступнее через понятные запросы и воспроизводимые расчёты.

**Принцип:** языковая модель не является источником статистической истины. Расчёты выполняются кодом, а структура данных и документация должны проверяться отдельно.

**Текущий охват:** T001, ограниченный набор сценариев, проверка структуры, таблицы и графики.

**Не реализовано/не подтверждено:** полноценная проверенная интеграция LLM; расчёты по семействам 1T, 2T, D006 и D008 без проверенных словарей переменных.
""")
    st.caption("STAT.DATATHON-2026 · AI for Official Statistics")
