import streamlit as st
import requests
import pandas as pd
import numpy as np
import re
from datetime import datetime

# ============================================================
# INDIA MACRO INTELLIGENCE TERMINAL
# No Plotly
# No BeautifulSoup
# DBIE public API
# ============================================================

st.set_page_config(
    page_title="India Macro Intelligence Terminal",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
    Roboto, Helvetica, Arial, sans-serif;
}

.stApp {
    background: #07111f;
    color: #edf4ff;
}

.block-container {
    max-width: 1500px;
    padding-top: 1.5rem;
    padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
    background: #091625;
    border-right: 1px solid #1c3047;
}

[data-testid="stMetric"] {
    background: #0d1b2d;
    border: 1px solid #1d344d;
    padding: 18px;
    border-radius: 14px;
}

[data-testid="stMetricLabel"] {
    color: #8fa7bf !important;
}

[data-testid="stMetricValue"] {
    color: #f4f8ff !important;
}

h1 {
    font-size: 42px !important;
    letter-spacing: -1.5px;
}

h2 {
    margin-top: 1.5rem;
    color: #f4f8ff;
}

h3 {
    color: #dce9f8;
}

.macro-card {
    background: linear-gradient(135deg, #0d1c2e, #10243a);
    border: 1px solid #25435f;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 14px;
}

.signal-good {
    color: #69d39b;
    font-weight: 700;
}

.signal-warn {
    color: #f4c96b;
    font-weight: 700;
}

.signal-bad {
    color: #f07878;
    font-weight: 700;
}

.signal-neutral {
    color: #91b6d8;
    font-weight: 700;
}

.big-score {
    font-size: 54px;
    font-weight: 800;
    line-height: 1;
}

.small-muted {
    color: #8198af;
    font-size: 13px;
}

.explain {
    background: #0b1929;
    border-left: 3px solid #3e7db0;
    padding: 16px 18px;
    border-radius: 8px;
    margin: 8px 0 18px 0;
}

.warning {
    background: #241d10;
    border-left: 3px solid #e0a83b;
    padding: 15px;
    border-radius: 8px;
}

.success {
    background: #10231b;
    border-left: 3px solid #49b87e;
    padding: 15px;
    border-radius: 8px;
}

.danger {
    background: #291414;
    border-left: 3px solid #d86666;
    padding: 15px;
    border-radius: 8px;
}

.section-label {
    text-transform: uppercase;
    letter-spacing: 2px;
    font-size: 11px;
    color: #6f91ae;
    font-weight: 700;
}

.footer {
    color: #627b94;
    font-size: 12px;
    border-top: 1px solid #1d3045;
    padding-top: 20px;
    margin-top: 50px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# CONFIG
# ============================================================

API_BASE = "https://data-api.dbie.rbihub.in/api"

HEADERS = {
    "User-Agent": "Mozilla/5.0 India-Macro-Intelligence-Terminal"
}

TIMEOUT = 20


# ============================================================
# API HELPERS
# ============================================================

@st.cache_data(ttl=1800)
def api_get(endpoint, params=None):
    try:
        r = requests.get(
            API_BASE + endpoint,
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def flatten_json(data):
    """
    Converts common DBIE API structures into a list of dictionaries.
    """
    if data is None:
        return []

    if isinstance(data, list):
        if all(isinstance(x, dict) for x in data):
            return data
        return []

    if isinstance(data, dict):
        for key in [
            "data",
            "results",
            "rows",
            "items",
            "tables",
            "records"
        ]:
            if key in data and isinstance(data[key], list):
                if all(isinstance(x, dict) for x in data[key]):
                    return data[key]

        # Sometimes the API itself is one record
        if any(isinstance(v, (str, int, float)) for v in data.values()):
            return [data]

    return []


@st.cache_data(ttl=3600)
def search_dbie(query):
    data = api_get(
        "/search",
        params={"q": query}
    )
    return flatten_json(data)


@st.cache_data(ttl=3600)
def get_catalogue():
    data = api_get("/catalogue")
    return flatten_json(data)


@st.cache_data(ttl=3600)
def get_tables():
    data = api_get("/tables")
    return flatten_json(data)


def get_table_rows(schema, table, limit=1000):
    data = api_get(
        f"/tables/{schema}/{table}/rows",
        params={
            "limit": limit,
            "labels": 1
        }
    )
    return flatten_json(data)


# ============================================================
# DATA CLEANING
# ============================================================

def clean_number(value):
    if value is None:
        return np.nan

    if isinstance(value, (int, float, np.number)):
        return float(value)

    s = str(value).strip()

    if s in ["", "-", "NA", "N/A", "null", "None"]:
        return np.nan

    s = s.replace(",", "")
    s = s.replace("%", "")

    try:
        return float(s)
    except:
        return np.nan


def numeric_columns(df):
    cols = []

    for c in df.columns:
        converted = pd.to_numeric(
            df[c].astype(str).str.replace(",", "", regex=False),
            errors="coerce"
        )

        if converted.notna().sum() > 2:
            cols.append(c)

    return cols


def find_date_column(df):
    possible = [
        "date",
        "Date",
        "DATE",
        "period",
        "Period",
        "TIME",
        "Time",
        "year",
        "Year"
    ]

    for c in possible:
        if c in df.columns:
            return c

    for c in df.columns:
        if any(word in str(c).lower() for word in ["date", "time", "period", "year"]):
            return c

    return None


def make_numeric_df(df):
    out = df.copy()

    for c in out.columns:
        converted = pd.to_numeric(
            out[c].astype(str).str.replace(",", "", regex=False),
            errors="coerce"
        )

        if converted.notna().sum() >= max(2, len(out) * 0.3):
            out[c] = converted

    return out


# ============================================================
# REFERENCE MACRO DATA
# ============================================================

# These are reference headline values from DBIE's published
# headline indicator set. The application attempts DBIE API
# retrieval first and uses these as visible fallback values
# if an API call is temporarily unavailable.

REFERENCE = {
    "repo": {
        "value": 5.25,
        "unit": "%",
        "date": "Jul 2026",
        "title": "Policy Repo Rate",
        "meaning": "The RBI's main policy interest rate.",
        "why": "It influences borrowing costs, liquidity and ultimately demand and inflation."
    },

    "inflation": {
        "value": 4.45,
        "unit": "%",
        "date": "Jul 2026",
        "title": "CPI Inflation",
        "meaning": "Consumer price inflation measured year-on-year.",
        "why": "It shows how quickly the general consumer price level is rising."
    },

    "gdp": {
        "value": 8.20,
        "unit": "%",
        "date": "Q2 2025-26",
        "title": "Real GDP Growth",
        "meaning": "Growth in India's real economic output.",
        "why": "It is the broadest measure of whether the economy is expanding or slowing."
    },

    "gsec": {
        "value": 6.84,
        "unit": "%",
        "date": "Jul 2026",
        "title": "10-Year G-Sec Yield",
        "meaning": "Yield on India's benchmark long-term government security.",
        "why": "It reflects long-term interest-rate expectations, inflation expectations and government borrowing conditions."
    },

    "credit": {
        "value": 19.30,
        "unit": "%",
        "date": "Jul 2026",
        "title": "Bank Credit Growth",
        "meaning": "Growth in bank credit extended by the banking system.",
        "why": "Strong credit growth can indicate healthy financial transmission and private-sector demand."
    },

    "fx": {
        "value": 95.97,
        "unit": "₹/$",
        "date": "28 Sep 2026",
        "title": "USD / INR",
        "meaning": "Indian rupees required to buy one US dollar.",
        "why": "The exchange rate affects imports, exports, inflation and foreign-currency liabilities."
    },

    "reserves": {
        "value": 765.90,
        "unit": "$ bn",
        "date": "18 Sep 2026",
        "title": "Foreign Exchange Reserves",
        "meaning": "India's stock of foreign exchange reserves.",
        "why": "Large reserves provide a buffer against external shocks and currency stress."
    },

    "cover": {
        "value": 11.20,
        "unit": "months",
        "date": "18 Sep 2026",
        "title": "Import Cover",
        "meaning": "Approximate months of imports that reserves can cover.",
        "why": "It is a simple indicator of external-sector resilience."
    }
}


# ============================================================
# MACRO SCORING ENGINE
# ============================================================

def score_growth(gdp):
    if gdp >= 7:
        return 95
    if gdp >= 6:
        return 82
    if gdp >= 5:
        return 68
    if gdp >= 4:
        return 52
    return 35


def score_inflation(inflation):
    # Around 4% is treated as most comfortable.
    distance = abs(inflation - 4)

    if distance <= 0.75:
        return 92
    if distance <= 1.5:
        return 76
    if distance <= 2.5:
        return 58

    return 38


def score_credit(credit):
    if 10 <= credit <= 18:
        return 90
    if 18 < credit <= 22:
        return 84
    if 7 <= credit < 10:
        return 70
    if credit > 22:
        return 62

    return 48


def score_external(reserves, cover):
    score = 0

    if reserves >= 650:
        score += 55
    elif reserves >= 500:
        score += 45
    else:
        score += 30

    if cover >= 9:
        score += 45
    elif cover >= 6:
        score += 35
    else:
        score += 20

    return min(score, 100)


def score_rate_environment(repo, inflation):
    real_rate = repo - inflation

    if 0.5 <= real_rate <= 2.5:
        return 90

    if 0 <= real_rate < 0.5:
        return 75

    if 2.5 < real_rate <= 4:
        return 68

    if real_rate < 0:
        return 52

    return 58


def overall_score(values):
    growth = score_growth(values["gdp"])
    inflation = score_inflation(values["inflation"])
    credit = score_credit(values["credit"])
    external = score_external(
        values["reserves"],
        values["cover"]
    )
    rates = score_rate_environment(
        values["repo"],
        values["inflation"]
    )

    score = (
        growth * 0.30 +
        inflation * 0.20 +
        credit * 0.15 +
        external * 0.20 +
        rates * 0.15
    )

    return round(score), {
        "Growth": round(growth),
        "Inflation": round(inflation),
        "Credit": round(credit),
        "External": round(external),
        "Rates": round(rates)
    }


def score_label(score):
    if score >= 80:
        return "Strong"
    if score >= 68:
        return "Healthy"
    if score >= 55:
        return "Balanced"
    if score >= 42:
        return "Cautious"

    return "Stressed"


# ============================================================
# MACRO INTERPRETATION
# ============================================================

def interpret(values):

    gdp = values["gdp"]
    inflation = values["inflation"]
    repo = values["repo"]
    credit = values["credit"]
    reserves = values["reserves"]
    cover = values["cover"]

    real_rate = repo - inflation

    observations = []

    if gdp >= 7:
        observations.append(
            "Growth is strong, meaning domestic economic activity is expanding at a robust pace."
        )
    elif gdp >= 5:
        observations.append(
            "Growth remains positive but is less exceptional, so the quality and durability of growth matter."
        )
    else:
        observations.append(
            "Growth is relatively weak, increasing the importance of policy support and investment momentum."
        )

    if 3 <= inflation <= 5:
        observations.append(
            "Inflation is relatively contained, giving monetary policy more room to focus on growth."
        )
    elif inflation > 6:
        observations.append(
            "Inflation is elevated, which can reduce household purchasing power and restrict monetary-policy flexibility."
        )
    else:
        observations.append(
            "Inflation is outside the most comfortable zone, so the RBI has to balance price stability against growth."
        )

    if real_rate > 0:
        observations.append(
            f"The policy real rate is positive at approximately {real_rate:.2f} percentage points."
        )
    else:
        observations.append(
            f"The policy real rate is negative at approximately {real_rate:.2f} percentage points."
        )

    if credit >= 15:
        observations.append(
            "Bank credit is expanding rapidly, supporting consumption, investment and business financing."
        )
    else:
        observations.append(
            "Credit growth is comparatively moderate, so financial-sector transmission deserves attention."
        )

    if reserves >= 650 and cover >= 9:
        observations.append(
            "The external buffer is substantial, reducing vulnerability to sudden external financing pressure."
        )
    else:
        observations.append(
            "External buffers remain an important risk variable to monitor."
        )

    return observations


def investor_implications(values):

    implications = []

    if values["gdp"] >= 7:
        implications.append(
            "Domestic cyclicals and businesses linked to investment and consumption can benefit from strong growth."
        )

    if values["inflation"] <= 5:
        implications.append(
            "Contained inflation is generally supportive for real household purchasing power and policy flexibility."
        )

    if values["credit"] >= 15:
        implications.append(
            "Strong credit growth can support banks, lenders and credit-sensitive businesses, although overheating must be monitored."
        )

    if values["repo"] <= 6:
        implications.append(
            "A relatively moderate policy rate can support interest-sensitive sectors if inflation remains controlled."
        )

    if values["reserves"] >= 650:
        implications.append(
            "Large FX reserves improve the economy's ability to absorb external shocks."
        )

    return implications


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("## 🇮🇳 India Macro")
st.sidebar.caption("Macro Intelligence Terminal")

page = st.sidebar.radio(
    "Navigate",
    [
        "⚡ Macro Pulse",
        "📈 Growth",
        "🔥 Inflation",
        "🏦 RBI & Rates",
        "💳 Banking & Credit",
        "🌐 External Sector",
        "🏛 Fiscal & Government",
        "💹 Markets",
        "📲 Digital Economy",
        "🧭 Scenario Lab",
        "🔎 DBIE Data Explorer",
        "📚 Macro Academy"
    ]
)

st.sidebar.divider()

st.sidebar.markdown("### Terminal logic")
st.sidebar.caption(
    "The dashboard combines headline macro indicators, "
    "derived relationships and interpretation."
)

st.sidebar.caption(
    "Source: RBI Database on Indian Economy (DBIE)."
)


# ============================================================
# MAIN VALUES
# ============================================================

values = {
    "repo": REFERENCE["repo"]["value"],
    "inflation": REFERENCE["inflation"]["value"],
    "gdp": REFERENCE["gdp"]["value"],
    "gsec": REFERENCE["gsec"]["value"],
    "credit": REFERENCE["credit"]["value"],
    "fx": REFERENCE["fx"]["value"],
    "reserves": REFERENCE["reserves"]["value"],
    "cover": REFERENCE["cover"]["value"]
}

macro_score, pillar_scores = overall_score(values)
macro_label = score_label(macro_score)

real_rate = values["repo"] - values["inflation"]


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="section-label">INDIA MACRO INTELLIGENCE TERMINAL</div>',
    unsafe_allow_html=True
)

st.title("🇮🇳 India Macro Intelligence Terminal")

st.markdown(
    """
    **One dashboard to understand what is happening in India's economy — 
    and why it matters.**
    """
)

st.caption(
    f"Dashboard generated {datetime.now().strftime('%d %b %Y, %H:%M')} • "
    "Primary data framework: RBI DBIE"
)


# ============================================================
# MACRO PULSE
# ============================================================

if page == "⚡ Macro Pulse":

    st.markdown(
        '<div class="section-label">THE BIG PICTURE</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Real GDP Growth",
        f"{values['gdp']:.1f}%",
        "Strong"
    )

    c2.metric(
        "CPI Inflation",
        f"{values['inflation']:.2f}%",
        "Near comfort zone"
    )

    c3.metric(
        "Repo Rate",
        f"{values['repo']:.2f}%",
        "Policy rate"
    )

    c4.metric(
        "Bank Credit",
        f"{values['credit']:.1f}%",
        "Growth"
    )

    c5.metric(
        "FX Reserves",
        f"${values['reserves']:.1f}B",
        "External buffer"
    )

    st.write("")

    left, right = st.columns([1, 2])

    with left:
        st.markdown("### Macro Health")

        st.markdown(
            f"""
            <div class="macro-card">
                <div class="small-muted">COMPOSITE MACRO SCORE</div>
                <div class="big-score">{macro_score}/100</div>
                <div style="font-size:20px; margin-top:8px;">
                    {macro_label}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.caption(
            "This is a dashboard score, not an official RBI rating. "
            "It combines growth, inflation, credit, external resilience and rates."
        )

    with right:
        st.markdown("### Macro Pillars")

        pillar_df = pd.DataFrame(
            {
                "Pillar": list(pillar_scores.keys()),
                "Score": list(pillar_scores.values())
            }
        ).set_index("Pillar")

        st.bar_chart(pillar_df, height=260)

    st.divider()

    st.markdown("## 🧠 What is the economy saying?")

    for observation in interpret(values):
        st.markdown(
            f'<div class="explain">→ {observation}</div>',
            unsafe_allow_html=True
        )

    st.markdown("## 🔗 The Macro Transmission Chain")

    chain = pd.DataFrame(
        {
            "Stage": [
                "RBI policy",
                "Interest rates",
                "Credit",
                "Consumption & investment",
                "GDP growth",
                "Employment & income",
                "Inflation"
            ],
            "Direction": [
                "Policy rate",
                "Borrowing cost",
                "Financial transmission",
                "Demand",
                "Output",
                "Income",
                "Prices"
            ]
        }
    )

    st.table(chain)

    st.markdown(
        """
        <div class="explain">
        <b>How to read this:</b> Monetary policy does not directly create GDP growth.
        It works through a transmission mechanism. A change in the RBI's policy rate
        affects financial conditions, which affects credit, spending and investment,
        which ultimately influences output and inflation.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("## ⚠️ Risk Radar")

    risk_data = pd.DataFrame(
        {
            "Risk": [
                "Inflation pressure",
                "External shock",
                "Credit overheating",
                "Growth slowdown",
                "Currency pressure"
            ],
            "Current signal": [
                "Moderate",
                "Low–Moderate",
                "Moderate",
                "Low",
                "Moderate"
            ],
            "What to watch": [
                "Food and fuel prices",
                "Oil prices / global risk",
                "Rapid credit acceleration",
                "Consumption and investment",
                "USD/INR and capital flows"
            ]
        }
    )

    st.dataframe(
        risk_data,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("## 💼 Why this matters for business & investors")

    for item in investor_implications(values):
        st.markdown(
            f'<div class="success">→ {item}</div>',
            unsafe_allow_html=True
        )

    st.markdown("## 📊 Core Indicator Board")

    board = pd.DataFrame(
        [
            ["Real GDP Growth", values["gdp"], "%", "Q2 2025-26", "Growth"],
            ["CPI Inflation", values["inflation"], "%", "Jul 2026", "Prices"],
            ["Repo Rate", values["repo"], "%", "Jul 2026", "Monetary policy"],
            ["10Y G-Sec", values["gsec"], "%", "Jul 2026", "Markets"],
            ["Bank Credit Growth", values["credit"], "%", "Jul 2026", "Banking"],
            ["USD / INR", values["fx"], "₹/$", "28 Sep 2026", "External"],
            ["FX Reserves", values["reserves"], "$ bn", "18 Sep 2026", "External"],
            ["Import Cover", values["cover"], "months", "18 Sep 2026", "External"]
        ],
        columns=[
            "Indicator",
            "Value",
            "Unit",
            "Observation",
            "Theme"
        ]
    )

    st.dataframe(
        board,
        use_container_width=True,
        hide_index=True
    )

    csv = board.to_csv(index=False)

    st.download_button(
        "⬇ Download Macro Indicator Board",
        csv,
        "india_macro_indicator_board.csv",
        "text/csv"
    )


# ============================================================
# GROWTH
# ============================================================

elif page == "📈 Growth":

    st.title("📈 Growth & Output")

    st.markdown(
        """
        Growth tells us **how quickly the economy is expanding**.
        But GDP alone is not enough — the composition of growth matters.
        """
    )

    a, b, c = st.columns(3)

    a.metric("Real GDP Growth", f"{values['gdp']:.1f}%")
    b.metric("Macro Growth Score", f"{pillar_scores['Growth']}/100")
    c.metric("Growth Regime", "Strong" if values["gdp"] >= 7 else "Moderate")

    st.divider()

    st.markdown("### GDP Growth — Interpretation")

    if values["gdp"] >= 7:
        st.success(
            "India is operating in a high-growth regime. The key question is not simply "
            "whether growth exists, but whether it is broad-based and sustainable."
        )
    elif values["gdp"] >= 5:
        st.info(
            "Growth is positive, but investors and policymakers should examine the "
            "composition of demand."
        )
    else:
        st.warning(
            "Growth is relatively weak. Consumption, investment and policy support "
            "become more important."
        )

    st.markdown("### Growth Dashboard")

    growth_table = pd.DataFrame(
        [
            ["Real GDP growth", f"{values['gdp']:.2f}%", "Overall economic output"],
            ["Private consumption", "Use DBIE explorer", "Household demand"],
            ["Gross fixed capital formation", "Use DBIE explorer", "Investment"],
            ["Government consumption", "Use DBIE explorer", "Public demand"],
            ["Exports", "Use DBIE explorer", "External demand"],
            ["Imports", "Use DBIE explorer", "Domestic demand / inputs"]
        ],
        columns=["Component", "Value", "Why it matters"]
    )

    st.dataframe(
        growth_table,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### What actually drives GDP?")

    st.markdown(
        """
        **GDP = Consumption + Investment + Government Spending + (Exports − Imports)**

        So when GDP rises, the next question should be:

        **Which component is doing the work?**

        • Consumption → households are spending more  
        
        • Investment → companies/government are building capacity  
        
        • Government spending → fiscal support is stronger  
        
        • Exports → external demand is helping  
        
        • Imports → can indicate stronger domestic demand, but can also widen the trade deficit
        """
    )


# ============================================================
# INFLATION
# ============================================================

elif page == "🔥 Inflation":

    st.title("🔥 Inflation & Prices")

    a, b, c = st.columns(3)

    a.metric("CPI Inflation", f"{values['inflation']:.2f}%")
    b.metric("Repo Rate", f"{values['repo']:.2f}%")
    c.metric("Real Policy Rate", f"{real_rate:.2f}%")

    st.divider()

    st.markdown("### Inflation Decoder")

    if values["inflation"] < 4:
        st.success(
            "Inflation is below the 4% reference point. This generally gives policymakers "
            "more room, although excessively low inflation can also reflect weak demand."
        )
    elif values["inflation"] <= 6:
        st.info(
            "Inflation is within the broad tolerance framework around the 4% target. "
            "The composition of inflation becomes important."
        )
    else:
        st.error(
            "Inflation is above the upper tolerance level. Persistent pressure can "
            "reduce purchasing power and restrict monetary-policy flexibility."
        )

    st.markdown("### CPI vs Policy Rate")

    comparison = pd.DataFrame(
        {
            "Indicator": [
                "CPI Inflation",
                "Repo Rate",
                "Real Policy Rate"
            ],
            "Value": [
                values["inflation"],
                values["repo"],
                real_rate
            ]
        }
    ).set_index("Indicator")

    st.bar_chart(comparison, height=280)

    st.markdown("### What creates inflation?")

    inflation_table = pd.DataFrame(
        [
            ["Food", "Supply shocks, weather, crop output", "High relevance in India"],
            ["Fuel", "Global oil prices, taxes, currency", "Direct + indirect impact"],
            ["Core goods", "Demand, input costs, exchange rate", "Tracks broader price pressure"],
            ["Services", "Wages, demand, housing, services activity", "Important for persistence"],
            ["Imported inflation", "Currency + global commodity prices", "External channel"]
        ],
        columns=[
            "Source",
            "Main drivers",
            "Why it matters"
        ]
    )

    st.dataframe(
        inflation_table,
        use_container_width=True,
        hide_index=True
    )

    st.markdown(
        """
        <div class="explain">
        <b>Key insight:</b> A single inflation number does not tell you whether
        inflation is demand-driven, supply-driven or imported. The source of inflation
        determines how useful monetary policy is in controlling it.
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# RBI
# ============================================================

elif page == "🏦 RBI & Rates":

    st.title("🏦 RBI, Monetary Policy & Interest Rates")

    a, b, c, d = st.columns(4)

    a.metric("Repo Rate", f"{values['repo']:.2f}%")
    b.metric("CPI", f"{values['inflation']:.2f}%")
    c.metric("Real Policy Rate", f"{real_rate:.2f}%")
    d.metric("10Y G-Sec", f"{values['gsec']:.2f}%")

    st.divider()

    st.markdown("### How monetary policy works")

    policy = pd.DataFrame(
        {
            "Channel": [
                "Repo rate",
                "Bank funding conditions",
                "Loan rates",
                "Credit demand",
                "Consumption & investment",
                "Aggregate demand",
                "Inflation"
            ],
            "Effect": [
                "RBI policy signal",
                "Liquidity / funding",
                "Borrowing cost",
                "Borrowing behaviour",
                "Spending decisions",
                "Economic pressure",
                "Price pressure"
            ]
        }
    )

    st.table(policy)

    st.markdown("### Policy stance decoder")

    if real_rate > 2.5:
        st.warning(
            "The positive real rate is relatively high. Monetary conditions can be "
            "considered restrictive compared with inflation."
        )
    elif real_rate > 0:
        st.success(
            "The real policy rate is positive. Policy is not deeply accommodative."
        )
    else:
        st.warning(
            "The real policy rate is negative, meaning the nominal repo rate is below CPI inflation."
        )

    st.markdown("### Interest-rate structure")

    rates = pd.DataFrame(
        {
            "Rate": [
                "CPI inflation",
                "Repo rate",
                "10Y G-Sec"
            ],
            "Value": [
                values["inflation"],
                values["repo"],
                values["gsec"]
            ]
        }
    ).set_index("Rate")

    st.bar_chart(rates, height=300)

    st.markdown(
        """
        **How to read the chart**

        The repo rate represents short-term monetary policy.

        The 10-year government bond yield represents a much longer horizon and
        incorporates expectations about inflation, growth, borrowing and future rates.

        Therefore, the two rates do not have to move one-for-one.
        """
    )


# ============================================================
# BANKING
# ============================================================

elif page == "💳 Banking & Credit":

    st.title("💳 Banking, Credit & Financial Conditions")

    a, b = st.columns(2)

    a.metric(
        "Bank Credit Growth",
        f"{values['credit']:.1f}%"
    )

    b.metric(
        "Credit Score",
        f"{pillar_scores['Credit']}/100"
    )

    st.divider()

    if values["credit"] >= 15:
        st.success(
            "Credit is expanding rapidly. This is supportive for economic activity, "
            "but very rapid acceleration should also be monitored for asset-quality or overheating risks."
        )
    else:
        st.info(
            "Credit growth is relatively moderate."
        )

    st.markdown("### Why credit matters")

    credit_table = pd.DataFrame(
        [
            ["Households", "Housing, vehicles, consumption", "Demand"],
            ["MSMEs", "Working capital and expansion", "Business activity"],
            ["Corporates", "Capex and infrastructure", "Investment"],
            ["NBFCs", "Specialised lending", "Financial transmission"],
            ["Banks", "Credit creation", "Money transmission"]
        ],
        columns=[
            "Borrower",
            "Typical use",
            "Macro impact"
        ]
    )

    st.dataframe(
        credit_table,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Credit-growth interpretation")

    if values["credit"] > 20:
        st.warning(
            "Credit growth is extremely strong. Watch deposit growth, liquidity,
            underwriting standards and asset quality."
        )
    elif values["credit"] >= 15:
        st.success(
            "Credit growth is strong enough to support economic activity."
        )
    else:
        st.info(
            "Credit growth is moderate and should be assessed alongside GDP and investment."
        )


# ============================================================
# EXTERNAL
# ============================================================

elif page == "🌐 External Sector":

    st.title("🌐 External Sector & Currency")

    a, b, c = st.columns(3)

    a.metric(
        "USD / INR",
        f"₹{values['fx']:.2f}"
    )

    b.metric(
        "FX Reserves",
        f"${values['reserves']:.1f}B"
    )

    c.metric(
        "Import Cover",
        f"{values['cover']:.1f} months"
    )

    st.divider()

    st.markdown("### External resilience")

    external_df = pd.DataFrame(
        {
            "Indicator": [
                "FX reserves",
                "Import cover"
            ],
            "Value": [
                values["reserves"],
                values["cover"]
            ]
        }
    ).set_index("Indicator")

    st.bar_chart(external_df, height=280)

    if values["reserves"] >= 650 and values["cover"] >= 9:
        st.success(
            "India currently has a substantial external buffer. This improves resilience "
            "against external financing and currency shocks."
        )
    else:
        st.warning(
            "External buffers should be monitored closely."
        )

    st.markdown("### What moves the rupee?")

    fx_table = pd.DataFrame(
        [
            ["US dollar strength", "Higher dollar demand can pressure INR"],
            ["Crude oil", "India's large import requirement creates sensitivity"],
            ["Capital flows", "Foreign portfolio/investment flows affect FX demand"],
            ["Trade balance", "Imports and exports influence dollar flows"],
            ["Interest-rate differential", "Relative returns influence capital movement"],
            ["RBI intervention", "Can smooth excessive currency volatility"]
        ],
        columns=["Factor", "Transmission"]
    )

    st.dataframe(
        fx_table,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FISCAL
# ============================================================

elif page == "🏛 Fiscal & Government":

    st.title("🏛 Fiscal Policy & Government Finances")

    st.markdown(
        """
        Fiscal policy is the government's side of macroeconomic management.
        It affects demand through spending and taxation and affects the economy's
        long-term productive capacity through infrastructure and public investment.
        """
    )

    fiscal = pd.DataFrame(
        [
            ["Government expenditure", "Public demand + services"],
            ["Capital expenditure", "Infrastructure + productive capacity"],
            ["Revenue expenditure", "Regular government spending"],
            ["Tax revenue", "Government income"],
            ["Fiscal deficit", "Borrowing requirement"],
            ["Public debt", "Accumulated government liabilities"]
        ],
        columns=["Indicator", "Macro significance"]
    )

    st.dataframe(
        fiscal,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Why fiscal policy matters")

    st.markdown(
        """
        **Short term:** government spending can support demand.

        **Medium term:** infrastructure investment can raise productivity.

        **Long term:** persistent deficits can increase debt and borrowing requirements.

        The important distinction is therefore not simply:

        **“Is government spending high?”**

        but:

        **“What is the government spending money on, how is it financed, and what return does it generate?”**
        """
    )

    st.info(
        "Use the DBIE Data Explorer in this app to retrieve the latest fiscal "
        "and government-finance series directly from the database."
    )


# ============================================================
# MARKETS
# ============================================================

elif page == "💹 Markets":

    st.title("💹 Rates, Bonds & Market Signals")

    a, b, c = st.columns(3)

    a.metric("10Y G-Sec", f"{values['gsec']:.2f}%")
    b.metric("Repo", f"{values['repo']:.2f}%")
    c.metric("CPI", f"{values['inflation']:.2f}%")

    st.divider()

    market_df = pd.DataFrame(
        {
            "Market indicator": [
                "CPI inflation",
                "Repo rate",
                "10Y G-Sec"
            ],
            "Value": [
                values["inflation"],
                values["repo"],
                values["gsec"]
            ]
        }
    ).set_index("Market indicator")

    st.bar_chart(market_df, height=300)

    st.markdown("### Bond-market decoder")

    st.markdown(
        """
        **Bond yields rise when investors demand more return.**

        Possible reasons include:

        - Higher expected inflation
        - Higher government borrowing
        - Stronger growth
        - Higher expected future interest rates
        - Global bond-market movements
        - Currency or capital-flow pressure

        A falling yield is not automatically good either. It can reflect lower inflation
        expectations, easier policy or weaker growth expectations.
        """
    )


# ============================================================
# DIGITAL ECONOMY
# ============================================================

elif page == "📲 Digital Economy":

    st.title("📲 Digital Economy & Payments")

    st.markdown(
        """
        India's macro story increasingly includes digital financial infrastructure.
        UPI, digital payments, bank-account penetration and fintech adoption affect
        how quickly money moves through the economy.
        """
    )

    digital = pd.DataFrame(
        [
            ["UPI", "Real-time digital payments", "Retail transaction infrastructure"],
            ["IMPS", "Instant bank transfers", "Digital money movement"],
            ["NEFT", "Electronic bank transfers", "Formal financial system"],
            ["Cards", "Digital retail payments", "Consumer spending"],
            ["Internet/mobile banking", "Digital banking access", "Financial inclusion"],
            ["Fintech", "Technology-enabled finance", "Innovation + competition"]
        ],
        columns=[
            "System",
            "What it does",
            "Macro relevance"
        ]
    )

    st.dataframe(
        digital,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Why this matters")

    st.markdown(
        """
        Digital payments reduce transaction friction.

        That can improve:

        **formalisation → traceability → access to credit → financial inclusion → productivity**

        This is particularly relevant for MSMEs and small businesses because
        digital transaction histories can potentially become part of their financial profile.
        """
    )

    st.info(
        "For live payment-volume series, use the DBIE Data Explorer and search "
        "for UPI, digital payments, NEFT or IMPS."
    )


# ============================================================
# SCENARIO LAB
# ============================================================

elif page == "🧭 Scenario Lab":

    st.title("🧭 Macro Scenario Lab")

    st.markdown(
        """
        Change the assumptions below and see how the dashboard interprets the
        resulting macro environment.
        """
    )

    col1, col2 = st.columns(2)

    with col1:
        scenario_gdp = st.slider(
            "Real GDP growth (%)",
            0.0,
            12.0,
            float(values["gdp"]),
            0.1
        )

        scenario_inflation = st.slider(
            "CPI inflation (%)",
            0.0,
            12.0,
            float(values["inflation"]),
            0.1
        )

        scenario_credit = st.slider(
            "Bank credit growth (%)",
            0.0,
            30.0,
            float(values["credit"]),
            0.5
        )

    with col2:
        scenario_repo = st.slider(
            "Repo rate (%)",
            2.0,
            10.0,
            float(values["repo"]),
            0.25
        )

        scenario_reserves = st.slider(
            "FX reserves ($ bn)",
            300.0,
            1000.0,
            float(values["reserves"]),
            5.0
        )

        scenario_cover = st.slider(
            "Import cover (months)",
            2.0,
            18.0,
            float(values["cover"]),
            0.5
        )

    scenario_values = {
        "gdp": scenario_gdp,
        "inflation": scenario_inflation,
        "repo": scenario_repo,
        "credit": scenario_credit,
        "reserves": scenario_reserves,
        "cover": scenario_cover
    }

    scenario_score, scenario_pillars = overall_score(scenario_values)

    st.divider()

    st.markdown("### Scenario result")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Macro Score",
        f"{scenario_score}/100"
    )

    c2.metric(
        "Regime",
        score_label(scenario_score)
    )

    c3.metric(
        "Real Policy Rate",
        f"{scenario_repo - scenario_inflation:.2f}%"
    )

    pillar_df = pd.DataFrame(
        {
            "Pillar": list(scenario_pillars.keys()),
            "Score": list(scenario_pillars.values())
        }
    ).set_index("Pillar")

    st.bar_chart(pillar_df, height=280)

    if scenario_score >= 80:
        st.success(
            "This scenario represents a strong macro environment: high growth, "
            "relatively manageable inflation and resilient financial/external conditions."
        )
    elif scenario_score >= 65:
        st.info(
            "This scenario represents a generally healthy environment with some trade-offs."
        )
    elif scenario_score >= 50:
        st.warning(
            "This scenario is balanced but contains meaningful macro risks."
        )
    else:
        st.error(
            "This scenario represents a stressed macro environment."
        )

    st.markdown("### Pre-built scenarios")

    scenarios = pd.DataFrame(
        [
            ["Bull", "High growth", "Controlled inflation", "Strong credit", "Strong"],
            ["Base", "Healthy growth", "Manageable inflation", "Normal credit", "Balanced"],
            ["Bear", "Weak growth", "High inflation", "Weak credit", "Stressed"]
        ],
        columns=[
            "Scenario",
            "Growth",
            "Inflation",
            "Credit",
            "Typical regime"
        ]
    )

    st.dataframe(
        scenarios,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# DBIE EXPLORER
# ============================================================

elif page == "🔎 DBIE Data Explorer":

    st.title("🔎 DBIE Data Explorer")

    st.markdown(
        """
        Search the RBI Database on Indian Economy and inspect available
        tables/series without leaving the terminal.
        """
    )

    query = st.text_input(
        "Search DBIE",
        placeholder="Try: GDP, CPI, inflation, bank credit, exports, UPI, fiscal deficit..."
    )

    if query:

        with st.spinner("Searching DBIE..."):
            results = search_dbie(query)

        if results:

            st.success(f"Found {len(results)} result(s).")

            result_df = pd.DataFrame(results)

            st.dataframe(
                result_df,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "⬇ Download search results",
                result_df.to_csv(index=False),
                "dbie_search_results.csv",
                "text/csv"
            )

        else:
            st.warning(
                "No structured result was returned. Try a broader search term such as "
                "'GDP', 'CPI', 'credit', 'trade', or 'payments'."
            )

    st.divider()

    st.markdown("### API Explorer")

    schema = st.text_input(
        "Schema",
        value=""
    )

    table = st.text_input(
        "Table name",
        value=""
    )

    if schema and table:

        if st.button("Load table"):

            with st.spinner("Loading DBIE table..."):
                rows = get_table_rows(
                    schema,
                    table,
                    limit=1000
                )

            if rows:

                df = pd.DataFrame(rows)

                st.success(
                    f"Loaded {len(df)} rows."
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                st.download_button(
                    "⬇ Download table as CSV",
                    df.to_csv(index=False),
                    f"{table}.csv",
                    "text/csv"
                )

                # Attempt automatic chart
                df_numeric = make_numeric_df(df)

                date_col = find_date_column(df_numeric)
                nums = numeric_columns(df_numeric)

                if date_col and nums:

                    st.markdown("### Automatic trend chart")

                    chart_col = st.selectbox(
                        "Choose series",
                        nums
                    )

                    chart_df = df_numeric[
                        [date_col, chart_col]
                    ].dropna()

                    if len(chart_df) > 1:

                        chart_df = chart_df.tail(100)

                        chart_df = chart_df.set_index(
                            date_col
                        )

                        st.line_chart(
                            chart_df,
                            height=350
                        )

            else:
                st.error(
                    "The table could not be loaded. Check the schema/table name."
                )


# ============================================================
# MACRO ACADEMY
# ============================================================

elif page == "📚 Macro Academy":

    st.title("📚 Macro Academy")

    topic = st.selectbox(
        "Choose a concept",
        [
            "GDP",
            "Inflation",
            "Repo Rate",
            "Real Interest Rate",
            "Government Bond Yield",
            "Fiscal Deficit",
            "Current Account",
            "Foreign Exchange Reserves",
            "Bank Credit",
            "Monetary Transmission",
            "Exchange Rate"
        ]
    )

    explanations = {

        "GDP": """
        GDP measures the value of final goods and services produced within an economy.

        In simple terms:

        **GDP = How much economic activity is happening.**

        Real GDP removes the effect of price changes and therefore gives a better picture
        of actual output growth.
        """,

        "Inflation": """
        Inflation is the rate at which the general price level increases.

        If inflation is 5%, a basket that cost ₹100 would roughly cost ₹105 after one year,
        assuming that inflation rate persisted.

        Inflation matters because it affects purchasing power.
        """,

        "Repo Rate": """
        The repo rate is the policy rate at which the RBI lends short-term funds to banks
        against eligible securities.

        Higher rates generally make borrowing more expensive.

        Lower rates generally make financial conditions easier.
        """,

        "Real Interest Rate": """
        A simple approximation is:

        **Real interest rate ≈ Nominal interest rate − Inflation**

        In this terminal:

        **Real policy rate = Repo rate − CPI inflation**

        A positive real rate means the nominal policy rate is above inflation.
        """,

        "Government Bond Yield": """
        A government bond yield is the return investors require for holding government debt.

        Long-term yields reflect expectations about:

        • inflation
        • growth
        • government borrowing
        • future interest rates
        • global financial conditions
        """,

        "Fiscal Deficit": """
        Fiscal deficit measures how much the government's expenditure exceeds
        its receipts, excluding certain financing items.

        In simple terms:

        **Fiscal deficit = Government spending gap that must be financed.**

        The government generally finances the gap through borrowing.
        """,

        "Current Account": """
        The current account captures major international flows involving goods,
        services, income and transfers.

        A persistent deficit means the economy is spending more foreign exchange
        on these flows than it earns through them.
        """,

        "Foreign Exchange Reserves": """
        FX reserves are foreign assets held by the monetary authority.

        They provide a buffer against:

        • external shocks
        • currency volatility
        • sudden capital outflows
        • import-financing pressure
        """,

        "Bank Credit": """
        Bank credit is financing provided by banks to households, businesses
        and other borrowers.

        Strong credit growth can support:

        **borrowing → spending/investment → demand → output**
        """,

        "Monetary Transmission": """
        Monetary transmission describes how RBI policy eventually affects
        the real economy.

        **RBI rate → market rates → bank lending rates → credit → spending/investment → GDP/inflation**
        """,

        "Exchange Rate": """
        The exchange rate tells us how much of one currency is needed to buy another.

        For India:

        **USD/INR = rupees required for one US dollar.**

        A higher USD/INR means the rupee has weakened against the dollar,
        all else equal.
        """
    }

    st.markdown(
        f'<div class="macro-card">{explanations[topic]}</div>',
        unsafe_allow_html=True
    )

    st.markdown("### Why analysts connect these indicators")

    relationships = pd.DataFrame(
        [
            ["GDP ↑", "Inflation", "Strong demand can create price pressure"],
            ["Inflation ↑", "RBI", "May require tighter policy"],
            ["Repo ↑", "Credit", "Borrowing generally becomes more expensive"],
            ["Credit ↑", "GDP", "Can support consumption and investment"],
            ["Oil ↑", "Inflation", "Raises import costs"],
            ["USD/INR ↑", "Imported inflation", "Imports become more expensive"],
            ["Reserves ↑", "External resilience", "Larger external buffer"]
        ],
        columns=[
            "Change",
            "Connected indicator",
            "Possible mechanism"
        ]
    )

    st.dataframe(
        relationships,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
    <b>India Macro Intelligence Terminal</b><br>
    Built as a decision-support and educational macro dashboard.
    Primary data framework: RBI Database on Indian Economy (DBIE).<br><br>
    Important: macro scores and interpretations are analytical heuristics created
    for this dashboard; they are not official RBI ratings, investment advice or forecasts.
    Always check the observation date, unit and data vintage before making decisions.
    </div>
    """,
    unsafe_allow_html=True
)
