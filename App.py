import streamlit as st
import requests
import re
from datetime import datetime

st.set_page_config(
    page_title="India Macro Monitor",
    page_icon="🇮🇳",
    layout="wide"
)

st.title("🇮🇳 India Macro Monitor")
st.caption("Indian macroeconomic indicators | RBI DBIE")

# ---------------------------------------------------
# GET RBI DBIE WEBSITE
# ---------------------------------------------------

URL = "https://dbie.rbihub.in/"

try:
    response = requests.get(
        URL,
        timeout=20,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    # Remove HTML tags without using BeautifulSoup
    text = re.sub(r"<[^>]+>", " ", response.text)
    text = re.sub(r"\s+", " ", text).strip()

    connected = True

except Exception as e:
    connected = False
    text = ""

# ---------------------------------------------------
# EXTRACT INDICATORS
# ---------------------------------------------------

def find_value(pattern):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Not available"


indicators = {
    "Policy Repo Rate": find_value(
        r"Policy\s+Repo\s+Rate.*?(\d+(?:\.\d+)?)\s*%"
    ),

    "CPI Inflation": find_value(
        r"CPI.*?Inflation.*?(\d+(?:\.\d+)?)\s*%"
    ),

    "Real GDP Growth": find_value(
        r"(?:Real\s+)?GDP.*?(?:Growth).*?(\d+(?:\.\d+)?)\s*%"
    ),

    "10Y G-Sec Yield": find_value(
        r"(?:10[- ]?Year|10Y).*?(?:G[- ]?Sec).*?(\d+(?:\.\d+)?)\s*%"
    ),

    "Bank Credit Growth": find_value(
        r"Bank\s+Credit.*?(\d+(?:\.\d+)?)\s*%"
    ),

    "USD / INR": find_value(
        r"(?:USD|US\s*Dollar).*?(?:INR|Rupee).*?(\d+(?:\.\d+)?)"
    ),

    "Foreign Exchange Reserves": find_value(
        r"(?:Foreign\s+Exchange\s+Reserves|Forex\s+Reserves).*?([\d,]+(?:\.\d+)?)"
    ),

    "Import Cover": find_value(
        r"Import\s+Cover.*?(\d+(?:\.\d+)?)"
    )
}

# ---------------------------------------------------
# CONNECTION STATUS
# ---------------------------------------------------

if connected:
    st.success("🟢 Connected to RBI DBIE")
else:
    st.error("🔴 Could not connect to RBI DBIE")

st.divider()

# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------

st.subheader("Key Economic Indicators")

cols = st.columns(4)

items = list(indicators.items())

for i, (name, value) in enumerate(items):
    with cols[i % 4]:
        st.metric(
            label=name,
            value=value
        )

st.divider()

# ---------------------------------------------------
# INTERPRETATION
# ---------------------------------------------------

st.subheader("What these indicators mean")

explanations = {
    "Policy Repo Rate":
        "The interest rate at which the RBI lends money to commercial banks.",

    "CPI Inflation":
        "Measures the change in prices paid by consumers for goods and services.",

    "Real GDP Growth":
        "Shows how fast India's economy is growing after adjusting for inflation.",

    "10Y G-Sec Yield":
        "The yield on India's 10-year government security and an important benchmark for interest rates.",

    "Bank Credit Growth":
        "Shows the growth in loans and advances provided by banks.",

    "USD / INR":
        "Shows how many Indian rupees are required to buy one US dollar.",

    "Foreign Exchange Reserves":
        "Foreign currency assets held by the RBI to support India's external financial stability.",

    "Import Cover":
        "Indicates how many months of imports can be covered by India's foreign exchange reserves."
}

for name, explanation in explanations.items():
    st.write(f"**{name}:** {explanation}")

st.divider()

st.caption(
    "Source: Reserve Bank of India – Database on Indian Economy (DBIE)"
)

st.caption(
    f"Dashboard checked: {datetime.now().strftime('%d %B %Y, %H:%M')}"
)
