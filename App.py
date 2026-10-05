import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="India Macro Monitor",
    page_icon="🇮🇳",
    layout="wide"
)

# ---------------------------------------------------------
# STYLING
# ---------------------------------------------------------

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
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("🇮🇳 India Macro Monitor")

st.markdown(
    '<div class="subtitle">'
    'A live view of India’s key macroeconomic indicators'
    '</div>',
    unsafe_allow_html=True
)

st.caption(
    "Data source: Reserve Bank of India — Database on Indian Economy (DBIE)"
)

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.header("Monitor")

    st.write(
        "Track inflation, growth, interest rates, "
        "currency and external-sector indicators."
    )

    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    st.write("**Data source**")
    st.write("RBI DBIE")

    st.write("**Cache refresh**")
    st.write("Every 60 minutes")

# ---------------------------------------------------------
# RBI API
# ---------------------------------------------------------

RBI_API = "https://data-api.dbie.rbihub.in"


@st.cache_data(ttl=3600, show_spinner=False)
def get_rbi_tables():

    response = requests.get(
        f"{RBI_API}/api/tables",
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------
# CONNECT TO RBI
# ---------------------------------------------------------

try:

    tables_response = get_rbi_tables()

    if isinstance(tables_response, dict):

        if "data" in tables_response:
            tables = tables_response["data"]

        elif "tables" in tables_response:
            tables = tables_response["tables"]

        else:
            tables = tables_response

    else:
        tables = tables_response

    tables_df = pd.DataFrame(tables)

except Exception as e:

    st.error("Unable to connect to the RBI DBIE API.")

    st.code(str(e))

    st.stop()


# ---------------------------------------------------------
# SEARCH RBI TABLE CATALOGUE
# ---------------------------------------------------------

def find_table(keyword):

    if tables_df.empty:
        return None

    text_columns = []

    for column in tables_df.columns:

        if tables_df[column].dtype == "object":

            text_columns.append(
                tables_df[column]
                .fillna("")
                .astype(str)
                .str.lower()
            )

    if not text_columns:
        return None

    combined = text_columns[0]

    for column_values in text_columns[1:]:
        combined = combined + " " + column_values

    matches = tables_df[
        combined.str.contains(
            keyword.lower(),
            na=False
        )
    ]

    if len(matches) == 0:
        return None

    return matches.iloc[0]


# ---------------------------------------------------------
# INDICATORS
# ---------------------------------------------------------

keywords = {
    "CPI Inflation": "consumer price",
    "GDP": "gross domestic product",
    "Repo Rate": "repo rate",
    "Exchange Rate": "usd inr",
    "Foreign Exchange Reserves": "foreign exchange reserves",
    "10Y Government Bond": "10 year government",
    "IIP": "industrial production"
}


discovered_tables = {}

for name, keyword in keywords.items():

    result = find_table(keyword)

    if result is not None:
        discovered_tables[name] = result


# ---------------------------------------------------------
# DASHBOARD STATUS
# ---------------------------------------------------------

st.subheader("Dashboard status")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "RBI connection",
        "Connected"
    )

with col2:

    st.metric(
        "Indicators discovered",
        len(discovered_tables)
    )

with col3:

    st.metric(
        "Last checked",
        datetime.now().strftime("%d %b %Y, %H:%M")
    )


# ---------------------------------------------------------
# RBI TABLES
# ---------------------------------------------------------

st.divider()

st.subheader("RBI data catalogue")

if discovered_tables:

    display_rows = []

    for name, row in discovered_tables.items():

        row_dict = row.to_dict()

        display_rows.append({
            "Indicator": name,
            "RBI table": row_dict.get(
                "title",
                row_dict.get("name", "Found")
            )
        })

    display_df = pd.DataFrame(display_rows)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "The RBI API is reachable, but the desired "
        "indicator tables could not be identified."
    )


# ---------------------------------------------------------
# PROJECT STATUS
# ---------------------------------------------------------

st.divider()

st.subheader("What this project does")

features = [
    "Connects directly to the RBI DBIE public API",
    "Discovers relevant macroeconomic datasets",
    "Caches API responses for one hour",
    "Allows manual data refresh",
    "Shows the current RBI data connection status"
]

for feature in features:

    st.write("✓ " + feature)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "India Macro Monitor — an independent data project "
    "for tracking Indian macroeconomic trends."
)
