import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

# =========================================================
# PAGE
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
    color: #777;
    font-size: 17px;
    margin-bottom: 25px;
}

.metric-card {
    padding: 20px;
    border: 1px solid #e5e5e5;
    border-radius: 12px;
    background: white;
    min-height: 145px;
}

.metric-title {
    font-size: 14px;
    color: #666;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 30px;
    font-weight: 700;
}

.metric-change {
    font-size: 14px;
    margin-top: 7px;
}

.section {
    margin-top: 30px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HEADER
# =========================================================

st.title("🇮🇳 India Macro Monitor")

st.markdown(
    '<div class="subtitle">'
    "India's economic pulse — growth, inflation, rates, "
    "currency and external stability"
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
        "A simple macroeconomic dashboard tracking "
        "India's key economic indicators."
    )

    if st.button(
        "🔄 Refresh data",
        use_container_width=True
    ):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    st.write("**Data source**")
    st.write("RBI DBIE")

    st.write("**Refresh**")
    st.write("Every 15 minutes")


# =========================================================
# RBI HOME PAGE
# =========================================================

RBI_URL = "https://dbie.rbihub.in/"


@st.cache_data(ttl=900)
def get_rbi_page():

    response = requests.get(
        RBI_URL,
        timeout=30,
        headers={
            "User-Agent":
            "Mozilla/5.0 "
            "(Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140 Safari/537.36"
        }
    )

    response.raise_for_status()

    return response.text


# =========================================================
# EXTRACT TEXT
# =========================================================

try:

    html = get_rbi_page()

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    page_text = soup.get_text(
        " ",
        strip=True
    )

except Exception as e:

    st.error(
        "Unable to connect to the RBI DBIE website."
    )

    st.code(str(e))

    st.stop()


# =========================================================
# EXTRACT INDICATORS
# =========================================================

def extract(pattern, text):

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:
        return match.groups()

    return None


indicators = {}


# ---------------------------------------------------------
# POLICY REPO RATE
# ---------------------------------------------------------

repo = extract(
    r"Policy repo rate\s+([A-Za-z]+ \d{4})\s+"
    r"([0-9.]+%)\s+"
    r"(.{0,80}?)(?=CPI inflation)",
    page_text
)

if repo:

    indicators["Repo Rate"] = {
        "value": repo[1],
        "period": repo[0],
        "change": repo[2]
    }


# ---------------------------------------------------------
# CPI
# ---------------------------------------------------------

cpi = extract(
    r"CPI inflation\s+([A-Za-z]+ \d{4})\s+"
    r"([0-9.]+%\s*YoY)\s+"
    r"([+-]?[0-9.]+\s*pp)",
    page_text
)

if cpi:

    indicators["CPI Inflation"] = {
        "value": cpi[1],
        "period": cpi[0],
        "change": cpi[2]
    }


# ---------------------------------------------------------
# GDP
# ---------------------------------------------------------

gdp = extract(
    r"Real GDP growth\s+"
    r"(Q[1-4]\s+\d{4}-\d{2})\s+"
    r"([0-9.]+%\s*YoY)\s+"
    r"([+-]?[0-9.]+\s*pp)",
    page_text
)

if gdp:

    indicators["Real GDP Growth"] = {
        "value": gdp[1],
        "period": gdp[0],
        "change": gdp[2]
    }


# ---------------------------------------------------------
# 10 YEAR G-SEC
# ---------------------------------------------------------

gsec = extract(
    r"10-year G-sec yield\s+"
    r"([A-Za-z]+ \d{4})\s+"
    r"([0-9.]+%)\s+"
    r"([+-]?[0-9.]+\s*pp)",
    page_text
)

if gsec:

    indicators["10Y G-Sec Yield"] = {
        "value": gsec[1],
        "period": gsec[0],
        "change": gsec[2]
    }


# ---------------------------------------------------------
# BANK CREDIT
# ---------------------------------------------------------

credit = extract(
    r"Bank credit growth\s+"
    r"([A-Za-z]+ \d{4})\s+"
    r"([0-9.]+%\s*YoY)\s+"
    r"([+-]?[0-9.]+\s*pp)",
    page_text
)

if credit:

    indicators["Bank Credit Growth"] = {
        "value": credit[1],
        "period": credit[0],
        "change": credit[2]
    }


# ---------------------------------------------------------
# USD / INR
# ---------------------------------------------------------

usd = extract(
    r"USD/INR\s+"
    r"(\d{1,2}-[A-Za-z]+-\d{4})\s+"
    r"([0-9.]+)₹/US\$\s+"
    r"([+-]?[0-9.]+)",
    page_text
)

if usd:

    indicators["USD / INR"] = {
        "value": "₹" + usd[1],
        "period": usd[0],
        "change": usd[2]
    }


# ---------------------------------------------------------
# FOREIGN EXCHANGE RESERVES
# ---------------------------------------------------------

fx = extract(
    r"Foreign exchange reserves\s+"
    r"(\d{1,2}-[A-Za-z]+-\d{4})\s+"
    r"([0-9.]+)\s+US\$ bn\s+"
    r"([+-]?[0-9.]+)",
    page_text
)

if fx:

    indicators["FX Reserves"] = {
        "value": "$" + fx[1] + "B",
        "period": fx[0],
        "change": fx[2]
    }


# ---------------------------------------------------------
# IMPORT COVER
# ---------------------------------------------------------

cover = extract(
    r"Import cover\s+"
    r"(\d{1,2}-[A-Za-z]+-\d{4})\s+"
    r"([0-9.]+)\s+months\s+"
    r"([+-]?[0-9.]+)",
    page_text
)

if cover:

    indicators["Import Cover"] = {
        "value": cover[1] + " months",
        "period": cover[0],
        "change": cover[2]
    }


# =========================================================
# CONNECTION STATUS
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
        "Indicators available",
        len(indicators)
    )

with c3:

    st.metric(
        "Last checked",
        datetime.now().strftime(
            "%d %b %Y, %H:%M"
        )
    )


# =========================================================
# MAIN DASHBOARD
# =========================================================

st.divider()

st.subheader("🇮🇳 India Macro Snapshot")


# =========================================================
# CARD DISPLAY
# =========================================================

names = list(indicators.keys())

for start in range(
    0,
    len(names),
    4
):

    cols = st.columns(4)

    for i, name in enumerate(
        names[start:start + 4]
    ):

        data = indicators[name]

        with cols[i]:

            st.markdown(
                f"""
                <div class="metric-card">

                <div class="metric-title">
                {name}
                </div>

                <div class="metric-value">
                {data["value"]}
                </div>

                <div class="metric-change">
                {data["change"]}
                </div>

                <div style="font-size:12px;color:#888;margin-top:8px;">
                {data["period"]}
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# INTERPRETATION
# =========================================================

st.divider()

st.subheader("What the indicators tell you")


interpretations = {

    "Repo Rate":
        "The RBI's policy interest rate. It is a key signal of the monetary-policy stance.",

    "CPI Inflation":
        "Tracks consumer-price inflation and is central to the RBI's inflation-targeting framework.",

    "Real GDP Growth":
        "Shows the pace at which India's real economic output is expanding.",

    "10Y G-Sec Yield":
        "Reflects the market yield on a long-term Indian government security and is an important benchmark for borrowing costs.",

    "Bank Credit Growth":
        "Shows how quickly bank lending is expanding across the economy.",

    "USD / INR":
        "Shows the rupee's value against the US dollar. A higher number means a weaker rupee.",

    "FX Reserves":
        "Shows the foreign-exchange assets held by the country and provides a buffer against external shocks.",

    "Import Cover":
        "Shows approximately how many months of imports can be covered by India's foreign-exchange reserves."
}


for name, data in indicators.items():

    if name in interpretations:

        st.markdown(
            f"**{name}** — {interpretations[name]}"
        )


# =========================================================
# DATA SOURCE
# =========================================================

st.divider()

st.subheader("Data source")

st.write(
    """
    The dashboard reads the headline macroeconomic indicators
    published by the Reserve Bank of India's Database on Indian
    Economy (DBIE).

    Values are shown with the observation period supplied by DBIE.
    The data is therefore not assumed to be real-time market data.
    """
)

st.caption(
    "India Macro Monitor • RBI DBIE • Independent data project"
)
