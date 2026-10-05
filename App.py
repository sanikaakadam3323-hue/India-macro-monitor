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


# ---------------------------------------------------------
# SEARCH RBI DATABASE
# ---------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def search_rbi(query):

    response = requests.get(
        f"{RBI_API}/api/search",
        params={"q": query},
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------
# INDICATORS
# ---------------------------------------------------------

searches = {
    "GDP": "gross domestic product",
    "CPI Inflation": "consumer price",
    "Repo Rate": "repo rate",
    "Exchange Rate": "exchange rate",
    "Foreign Exchange Reserves": "foreign exchange reserves",
    "Industrial Production": "industrial production"
}


discovered_tables = {}


# ---------------------------------------------------------
# SEARCH FOR EACH INDICATOR
# ---------------------------------------------------------

for indicator, query in searches.items():

    try:

        result = search_rbi(query)

        # Handle different possible API response structures
        if isinstance(result, dict):

            if "data" in result:
                matches = result["data"]

            elif "results" in result:
                matches = result["results"]

            elif "tables" in result:
                matches = result["tables"]

            else:
                matches = result

        else:
            matches = result

        if isinstance(matches, list) and len(matches) > 0:

            # Keep the first useful result
            discovered_tables[indicator] = matches[0]

    except Exception:
        pass


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
# RBI DATA CATALOGUE
# ---------------------------------------------------------

st.divider()

st.subheader("RBI data catalogue")

if discovered_tables:

    display_rows = []

    for indicator, result in discovered_tables.items():

        if isinstance(result, dict):

            title = (
                result.get("title")
                or result.get("name")
                or result.get("label")
                or "RBI dataset"
            )

            schema = result.get("schema", "")
            table = result.get("table", "")

            if schema and table:
                table_name = f"{schema}/{table}"
            else:
                table_name = result.get(
                    "path",
                    table or "Available dataset"
                )

        else:

            title = str(result)
            table_name = "Available dataset"

        display_rows.append({
            "Indicator": indicator,
            "RBI dataset": title,
            "Table": table_name
        })

    display_df = pd.DataFrame(display_rows)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "The RBI API is reachable, but no matching datasets "
        "were returned."
    )


# ---------------------------------------------------------
# WHAT THIS PROJECT DOES
# ---------------------------------------------------------

st.divider()

st.subheader("What this project does")

features = [
    "Connects directly to the RBI DBIE public API",
    "Searches the RBI catalogue for major macroeconomic indicators",
    "Identifies relevant RBI datasets",
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
