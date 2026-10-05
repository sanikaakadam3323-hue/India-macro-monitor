import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="India Macro Monitor",
    page_icon="🇮🇳",
    layout="wide"
)

# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>

.block-container {
    padding-top: 2rem;
    max-width: 1400px;
}

h1 {
    font-size: 42px !important;
    font-weight: 750 !important;
}

.subtitle {
    color: #666;
    font-size: 17px;
    margin-bottom: 25px;
}

[data-testid="stMetricValue"] {
    font-size: 28px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================

st.title("🇮🇳 India Macro Monitor")

st.markdown(
    '<div class="subtitle">'
    "India's economic pulse — inflation, growth, rates, currency "
    "and external stability"
    "</div>",
    unsafe_allow_html=True
)

st.caption(
    "Source: Reserve Bank of India — Database on Indian Economy (DBIE)"
)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("Monitor")

    st.write(
        "Track India's major macroeconomic indicators "
        "from RBI's Database on Indian Economy."
    )

    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    st.write("**Source**")
    st.write("RBI DBIE")

    st.write("**Data refresh**")
    st.write("Every 60 minutes")

# =========================================================
# API
# =========================================================

API = "https://data-api.dbie.rbihub.in"


# =========================================================
# GENERIC API FUNCTIONS
# =========================================================

@st.cache_data(ttl=3600, show_spinner=False)
def search_tables(query):

    r = requests.get(
        f"{API}/api/tables",
        params={"q": query},
        timeout=30
    )

    r.raise_for_status()

    data = r.json()

    if isinstance(data, dict):

        if "data" in data:
            return data["data"]

        if "tables" in data:
            return data["tables"]

        if "results" in data:
            return data["results"]

    if isinstance(data, list):
        return data

    return []


@st.cache_data(ttl=3600, show_spinner=False)
def get_table(schema, table):

    r = requests.get(
        f"{API}/api/tables/{schema}/{table}",
        timeout=30
    )

    r.raise_for_status()

    return r.json()


@st.cache_data(ttl=3600, show_spinner=False)
def get_rows(schema, table):

    r = requests.get(
        f"{API}/api/tables/{schema}/{table}/rows",
        params={
            "limit": 500,
            "order": "period desc",
            "labels": 1
        },
        timeout=30
    )

    r.raise_for_status()

    data = r.json()

    if isinstance(data, dict):

        if "data" in data:
            return data["data"]

        if "rows" in data:
            return data["rows"]

    if isinstance(data, list):
        return data

    return []


# =========================================================
# HELPERS
# =========================================================

def clean_name(value):

    if value is None:
        return ""

    return str(value).lower()


def find_best_table(search_terms):

    candidates = []

    for term in search_terms:

        try:
            results = search_tables(term)

            for result in results:

                if not isinstance(result, dict):
                    continue

                title = clean_name(
                    result.get("title")
                    or result.get("name")
                    or ""
                )

                score = 0

                for keyword in search_terms:

                    if keyword.lower() in title:
                        score += 1

                candidates.append(
                    (score, result)
                )

        except Exception:
            continue

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidates[0][1]


def get_schema_table(result):

    if not isinstance(result, dict):
        return None, None

    schema = (
        result.get("schema")
        or result.get("schema_name")
    )

    table = (
        result.get("table")
        or result.get("table_name")
    )

    return schema, table


def find_period_column(df):

    possible = [
        "period",
        "date",
        "month",
        "year",
        "quarter",
        "time"
    ]

    for col in df.columns:

        name = clean_name(col)

        if name in possible:
            return col

        if "period" in name:
            return col

        if "date" in name:
            return col

    return None


def find_numeric_column(df):

    excluded = [
        "id",
        "code",
        "year",
        "month",
        "quarter",
        "period"
    ]

    candidates = []

    for col in df.columns:

        name = clean_name(col)

        if any(x in name for x in excluded):
            continue

        numeric = pd.to_numeric(
            df[col],
            errors="coerce"
        )

        count = numeric.notna().sum()

        if count > 0:
            candidates.append(
                (count, col)
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidates[0][1]


def prepare_dataframe(rows):

    if not rows:
        return None

    df = pd.DataFrame(rows)

    if df.empty:
        return None

    period_col = find_period_column(df)

    if period_col is None:
        return None

    value_col = find_numeric_column(df)

    if value_col is None:
        return None

    df["_period"] = pd.to_datetime(
        df[period_col],
        errors="coerce"
    )

    df["_value"] = pd.to_numeric(
        df[value_col],
        errors="coerce"
    )

    df = df.dropna(
        subset=["_period", "_value"]
    )

    df = df.sort_values("_period")

    return df


# =========================================================
# INDICATOR DEFINITIONS
# =========================================================

INDICATORS = {

    "CPI Inflation": {
        "search": [
            "consumer price inflation",
            "CPI inflation"
        ],
        "unit": "%",
        "description": "Consumer price inflation, year-on-year"
    },

    "GDP Growth": {
        "search": [
            "gross domestic product growth",
            "GDP growth"
        ],
        "unit": "%",
        "description": "Real GDP growth"
    },

    "Repo Rate": {
        "search": [
            "policy repo rate",
            "repo rate"
        ],
        "unit": "%",
        "description": "RBI policy repo rate"
    },

    "10Y G-Sec": {
        "search": [
            "10 year government securities yield",
            "10 year G-sec"
        ],
        "unit": "%",
        "description": "10-year government security yield"
    },

    "USD/INR": {
        "search": [
            "US dollar Indian rupee exchange rate",
            "USD INR exchange rate"
        ],
        "unit": "₹/$",
        "description": "Indian rupee against US dollar"
    },

    "FX Reserves": {
        "search": [
            "foreign exchange reserves",
            "foreign exchange reserve"
        ],
        "unit": "US$ bn",
        "description": "India's foreign exchange reserves"
    },

    "Bank Credit Growth": {
        "search": [
            "bank credit growth",
            "credit growth"
        ],
        "unit": "%",
        "description": "Bank credit growth"
    },

    "IIP": {
        "search": [
            "index of industrial production",
            "industrial production"
        ],
        "unit": "Index",
        "description": "Index of Industrial Production"
    }
}


# =========================================================
# LOAD DATA
# =========================================================

loaded = {}

progress = st.progress(
    0,
    text="Loading RBI macroeconomic data..."
)

total = len(INDICATORS)

for i, (name, config) in enumerate(
    INDICATORS.items()
):

    result = find_best_table(
        config["search"]
    )

    if result is None:
        progress.progress(
            (i + 1) / total
        )
        continue

    schema, table = get_schema_table(
        result
    )

    if not schema or not table:
        progress.progress(
            (i + 1) / total
        )
        continue

    try:

        rows = get_rows(
            schema,
            table
        )

        df = prepare_dataframe(
            rows
        )

        if df is not None and not df.empty:

            loaded[name] = {
                "df": df,
                "unit": config["unit"],
                "description": config["description"],
                "title": (
                    result.get("title")
                    or result.get("name")
                    or name
                ),
                "schema": schema,
                "table": table
            }

    except Exception:
        pass

    progress.progress(
        (i + 1) / total
    )

progress.empty()


# =========================================================
# STATUS
# =========================================================

st.subheader("Dashboard status")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "RBI connection",
        "Connected"
    )

with c2:
    st.metric(
        "Indicators loaded",
        len(loaded)
    )

with c3:
    st.metric(
        "Last checked",
        datetime.now().strftime(
            "%d %b %Y, %H:%M"
        )
    )


# =========================================================
# MACRO SNAPSHOT
# =========================================================

st.divider()

st.subheader("🇮🇳 Macro snapshot")

if loaded:

    names = list(loaded.keys())

    # Four cards per row
    for start in range(
        0,
        len(names),
        4
    ):

        cols = st.columns(4)

        for j, name in enumerate(
            names[start:start + 4]
        ):

            item = loaded[name]

            df = item["df"]

            latest = df.iloc[-1]

            value = latest["_value"]

            if len(df) >= 2:
                previous = df.iloc[-2]["_value"]
                change = value - previous
            else:
                previous = None
                change = None

            unit = item["unit"]

            if name == "USD/INR":
                display = f"₹{value:,.2f}"
            elif name == "FX Reserves":
                display = f"${value:,.1f}B"
            elif unit == "%":
                display = f"{value:.2f}%"
            else:
                display = f"{value:,.2f}"

            with cols[j]:

                if change is not None:

                    if unit == "%":
                        delta = f"{change:+.2f} pp"
                    else:
                        delta = f"{change:+.2f}"

                else:
                    delta = None

                st.metric(
                    name,
                    display,
                    delta
                )

                st.caption(
                    pd.to_datetime(
                        latest["_period"]
                    ).strftime("%d %b %Y")
                )


# =========================================================
# CHARTS
# =========================================================

st.divider()

st.subheader("📈 Economic trends")

if loaded:

    for name, item in loaded.items():

        df = item["df"].copy()

        chart_df = df[
            ["_period", "_value"]
        ].copy()

        chart_df = chart_df.set_index(
            "_period"
        )

        chart_df.columns = [name]

        st.markdown(
            f"### {name}"
        )

        st.caption(
            item["description"]
        )

        st.line_chart(
            chart_df,
            use_container_width=True
        )


# =========================================================
# DATA TABLE
# =========================================================

st.divider()

st.subheader("📊 Latest observations")

summary = []

for name, item in loaded.items():

    df = item["df"]

    latest = df.iloc[-1]

    previous = (
        df.iloc[-2]["_value"]
        if len(df) >= 2
        else None
    )

    change = (
        latest["_value"] - previous
        if previous is not None
        else None
    )

    summary.append({
        "Indicator": name,
        "Latest": round(
            latest["_value"],
            4
        ),
        "Previous": (
            round(previous, 4)
            if previous is not None
            else None
        ),
        "Change": (
            round(change, 4)
            if change is not None
            else None
        ),
        "Period": latest["_period"].strftime(
            "%d %b %Y"
        ),
        "Unit": item["unit"]
    })

if summary:

    st.dataframe(
        pd.DataFrame(summary),
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "No indicator observations could be loaded."
    )


# =========================================================
# SOURCE INFORMATION
# =========================================================

st.divider()

st.subheader("About the data")

st.write(
    """
    India Macro Monitor uses the Reserve Bank of India's
    Database on Indian Economy (DBIE) as its primary source.

    The dashboard automatically searches the RBI catalogue,
    identifies relevant datasets, retrieves their observations,
    and converts them into a simple macroeconomic dashboard.
    """
)

st.caption(
    "India Macro Monitor • Independent data project • "
    "Source: Reserve Bank of India DBIE"
)
