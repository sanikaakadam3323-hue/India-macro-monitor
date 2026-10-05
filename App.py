import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="India Macro Intelligence Terminal",
    page_icon="🇮🇳",
    layout="wide"
)

# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>
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

.macro-card {
    background: #0d1c2e;
    border: 1px solid #25435f;
    border-radius: 18px;
    padding: 22px;
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
    margin: 8px 0 18px;
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
# DBIE API
# ============================================================

API_BASE = "https://data-api.dbie.rbihub.in/api"

HEADERS = {
    "User-Agent": "Mozilla/5.0 India-Macro-Intelligence-Terminal"
}


@st.cache_data(ttl=1800)
def api_get(endpoint, params=None):
    try:
        response = requests.get(
            API_BASE + endpoint,
            params=params,
            headers=HEADERS,
            timeout=20
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def flatten(data):
    if data is None:
        return []

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in [
            "data",
            "results",
            "rows",
            "items",
            "tables",
            "records"
        ]:
            if isinstance(data.get(key), list):
                return data[key]

        return [data]

    return []


@st.cache_data(ttl=3600)
def dbie_search(query):
    data = api_get(
        "/search",
        {"q": query}
    )
    return flatten(data)


@st.cache_data(ttl=3600)
def dbie_rows(schema, table):
    data = api_get(
        f"/tables/{schema}/{table}/rows",
        {
            "limit": 1000,
            "labels": 1
        }
    )
    return flatten(data)


# ============================================================
# REFERENCE DATA
# ============================================================

REFERENCE = {
    "GDP growth": (
        8.20,
        "%",
        "Q2 2025-26"
    ),

    "CPI inflation": (
        4.45,
        "%",
        "Jul 2026"
    ),

    "Repo rate": (
        5.25,
        "%",
        "Jul 2026"
    ),

    "10Y G-Sec": (
        6.84,
        "%",
        "Jul 2026"
    ),

    "Bank credit growth": (
        19.30,
        "%",
        "Jul 2026"
    ),

    "USD/INR": (
        95.97,
        "₹/$",
        "28 Sep 2026"
    ),

    "FX reserves": (
        765.90,
        "$ bn",
        "18 Sep 2026"
    ),

    "Import cover": (
        11.20,
        "months",
        "18 Sep 2026"
    )
}


values = {
    key: item[0]
    for key, item in REFERENCE.items()
}


# ============================================================
# SCORING
# ============================================================

def growth_score(value):
    if value >= 7:
        return 95

    if value >= 6:
        return 82

    if value >= 5:
        return 68

    if value >= 4:
        return 52

    return 35


def inflation_score(value):
    distance = abs(value - 4)

    if distance <= 0.75:
        return 92

    if distance <= 1.5:
        return 76

    if distance <= 2.5:
        return 58

    return 38


def credit_score(value):
    if 10 <= value <= 18:
        return 90

    if 18 < value <= 22:
        return 84

    if 7 <= value < 10:
        return 70

    if value > 22:
        return 62

    return 48


def external_score(reserves, cover):
    reserve_score = (
        55 if reserves >= 650
        else 45 if reserves >= 500
        else 30
    )

    cover_score = (
        45 if cover >= 9
        else 35 if cover >= 6
        else 20
    )

    return min(
        reserve_score + cover_score,
        100
    )


def rates_score(repo, inflation):
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


def calculate_macro_score(
    gdp,
    inflation,
    repo,
    credit,
    reserves,
    cover
):
    pillars = {
        "Growth": growth_score(gdp),
        "Inflation": inflation_score(inflation),
        "Credit": credit_score(credit),
        "External": external_score(
            reserves,
            cover
        ),
        "Rates": rates_score(
            repo,
            inflation
        )
    }

    total = round(
        pillars["Growth"] * 0.30
        + pillars["Inflation"] * 0.20
        + pillars["Credit"] * 0.15
        + pillars["External"] * 0.20
        + pillars["Rates"] * 0.15
    )

    return total, pillars


macro_score, pillars = calculate_macro_score(
    values["GDP growth"],
    values["CPI inflation"],
    values["Repo rate"],
    values["Bank credit growth"],
    values["FX reserves"],
    values["Import cover"]
)


def regime(score):
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
# SIDEBAR
# ============================================================

st.sidebar.title("🇮🇳 India Macro")

st.sidebar.caption(
    "Macro Intelligence Terminal"
)

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

st.sidebar.markdown(
    "### Data source"
)

st.sidebar.caption(
    "RBI Database on Indian Economy (DBIE)"
)

st.sidebar.caption(
    "Headline values are published reference observations. "
    "Check observation dates and data vintage before using them."
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="section-label">'
    'INDIA MACRO INTELLIGENCE TERMINAL'
    '</div>',
    unsafe_allow_html=True
)

st.title(
    "🇮🇳 India Macro Intelligence Terminal"
)

st.markdown(
    "A single dashboard to track India's economy "
    "and translate macroeconomic data into decisions."
)

st.caption(
    "Dashboard refresh: "
    + datetime.now().strftime("%d %b %Y, %H:%M")
)


# ============================================================
# MACRO PULSE
# ============================================================

if page == "⚡ Macro Pulse":

    st.subheader("The Big Picture")

    cols = st.columns(5)

    metrics = [
        (
            "Real GDP Growth",
            f"{values['GDP growth']:.1f}%"
        ),
        (
            "CPI Inflation",
            f"{values['CPI inflation']:.2f}%"
        ),
        (
            "Repo Rate",
            f"{values['Repo rate']:.2f}%"
        ),
        (
            "Bank Credit Growth",
            f"{values['Bank credit growth']:.1f}%"
        ),
        (
            "FX Reserves",
            f"${values['FX reserves']:.1f}B"
        )
    ]

    for column, item in zip(cols, metrics):
        column.metric(
            item[0],
            item[1]
        )

    left, right = st.columns([1, 2])

    with left:

        st.markdown(
            f"""
            <div class="macro-card">
                <div class="small-muted">
                    COMPOSITE MACRO SCORE
                </div>
                <h1>{macro_score}/100</h1>
                <h3>{regime(macro_score)}</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.caption(
            "Analytical score created by this application; "
            "not an official RBI rating."
        )

    with right:

        st.subheader("Macro Pillars")

        pillar_df = pd.DataFrame(
            {
                "Score": pillars
            }
        )

        st.bar_chart(
            pillar_df
        )

    st.divider()

    st.header(
        "🧠 One-click India Decoder"
    )

    observations = []

    if values["GDP growth"] >= 7:
        observations.append(
            "Growth is strong."
        )
    else:
        observations.append(
            "Growth needs closer monitoring."
        )

    if 3 <= values["CPI inflation"] <= 6:
        observations.append(
            "Inflation is broadly manageable."
        )
    else:
        observations.append(
            "Inflation needs attention."
        )

    if values["Bank credit growth"] >= 15:
        observations.append(
            "Credit expansion is strong."
        )
    else:
        observations.append(
            "Credit growth is moderate."
        )

    if values["FX reserves"] >= 650:
        observations.append(
            "External buffers are substantial."
        )
    else:
        observations.append(
            "External buffers need monitoring."
        )

    observations.append(
        "The approximate real policy rate is "
        f"{values['Repo rate'] - values['CPI inflation']:.2f} "
        "percentage points."
    )

    for observation in observations:
        st.markdown(
            f"- {observation}"
        )

    st.header(
        "🔗 Macro Transmission"
    )

    transmission = pd.DataFrame(
        [
            [
                "RBI policy",
                "Interest rates",
                "Changes financial conditions"
            ],
            [
                "Interest rates",
                "Credit",
                "Changes borrowing costs"
            ],
            [
                "Credit",
                "Consumption / investment",
                "Changes spending"
            ],
            [
                "Spending",
                "GDP",
                "Changes output"
            ],
            [
                "Demand",
                "Inflation",
                "Can create price pressure"
            ],
            [
                "Exchange rate",
                "Import prices",
                "Can affect inflation"
            ]
        ],
        columns=[
            "Starting point",
            "Next channel",
            "Economic effect"
        ]
    )

    st.dataframe(
        transmission,
        use_container_width=True,
        hide_index=True
    )

    st.header(
        "⚠️ Risk Radar"
    )

    risks = pd.DataFrame(
        [
            [
                "Inflation",
                "Moderate",
                "Food, fuel and core prices"
            ],
            [
                "Currency",
                "Moderate",
                "USD/INR and capital flows"
            ],
            [
                "External shock",
                "Low–Moderate",
                "Oil prices and global risk"
            ],
            [
                "Credit overheating",
                "Moderate",
                "Credit quality and deposits"
            ],
            [
                "Growth slowdown",
                "Low",
                "Consumption and investment"
            ]
        ],
        columns=[
            "Risk",
            "Assessment",
            "Watch"
        ]
    )

    st.dataframe(
        risks,
        use_container_width=True,
        hide_index=True
    )

    board = pd.DataFrame(
        [
            [
                key,
                value,
                unit,
                date
            ]
            for key, (
                value,
                unit,
                date
            ) in REFERENCE.items()
        ],
        columns=[
            "Indicator",
            "Value",
            "Unit",
            "Observation"
        ]
    )

    st.header(
        "📊 Indicator Board"
    )

    st.dataframe(
        board,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇ Download indicator board",
        board.to_csv(index=False),
        "india_macro_board.csv",
        "text/csv"
    )


# ============================================================
# GROWTH
# ============================================================

elif page == "📈 Growth":

    st.title(
        "📈 Growth & Output"
    )

    a, b, c = st.columns(3)

    a.metric(
        "Real GDP Growth",
        f"{values['GDP growth']:.2f}%"
    )

    b.metric(
        "Growth Score",
        f"{pillars['Growth']}/100"
    )

    c.metric(
        "Regime",
        "Strong"
        if values["GDP growth"] >= 7
        else "Moderate"
    )

    st.divider()

    st.header(
        "What GDP tells us"
    )

    st.markdown(
        "GDP measures the value of final goods and services "
        "produced within an economy. Real GDP growth focuses "
        "on changes in output after accounting for price effects."
    )

    st.markdown(
        '<div class="explain">'
        '<b>Important:</b> GDP growth alone is not enough. '
        'Analysts also ask what is driving the growth — '
        'consumption, investment, government spending, '
        'exports and imports.'
        '</div>',
        unsafe_allow_html=True
    )

    df = pd.DataFrame(
        [
            [
                "Private consumption",
                "Household spending",
                "Consumer demand"
            ],
            [
                "Investment",
                "Capital formation",
                "Future productive capacity"
            ],
            [
                "Government spending",
                "Public demand",
                "Fiscal support"
            ],
            [
                "Exports",
                "Foreign demand",
                "External growth"
            ],
            [
                "Imports",
                "Foreign goods/services",
                "Demand and production inputs"
            ]
        ],
        columns=[
            "Component",
            "Meaning",
            "Why it matters"
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# INFLATION
# ============================================================

elif page == "🔥 Inflation":

    st.title(
        "🔥 Inflation & Prices"
    )

    a, b, c = st.columns(3)

    a.metric(
        "CPI Inflation",
        f"{values['CPI inflation']:.2f}%"
    )

    b.metric(
        "Repo Rate",
        f"{values['Repo rate']:.2f}%"
    )

    c.metric(
        "Real Policy Rate",
        f"{values['Repo rate'] - values['CPI inflation']:.2f}%"
    )

    st.divider()

    if 3 <= values["CPI inflation"] <= 6:

        st.info(
            "Inflation is within a broadly manageable range. "
            "Its composition remains important."
        )

    else:

        st.warning(
            "Inflation is outside the broad manageable range "
            "and deserves closer monitoring."
        )

    st.header(
        "Inflation Sources"
    )

    df = pd.DataFrame(
        [
            [
                "Food",
                "Weather, crop output, supply shocks"
            ],
            [
                "Fuel",
                "Oil prices, taxes, currency"
            ],
            [
                "Core goods",
                "Demand and input costs"
            ],
            [
                "Services",
                "Wages and demand"
            ],
            [
                "Imported inflation",
                "Global prices and exchange rate"
            ]
        ],
        columns=[
            "Category",
            "Main drivers"
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.header(
        "Real Interest Rate"
    )

    st.markdown(
        "**Approximate real policy rate = Repo Rate − CPI Inflation**"
    )

    st.markdown(
        f"**{values['Repo rate']:.2f}% − "
        f"{values['CPI inflation']:.2f}% = "
        f"{values['Repo rate'] - values['CPI inflation']:.2f}%**"
    )

    chart = pd.DataFrame(
        {
            "Rate": [
                values["CPI inflation"],
                values["Repo rate"],
                values["Repo rate"] - values["CPI inflation"]
            ]
        },
        index=[
            "CPI Inflation",
            "Repo Rate",
            "Real Policy Rate"
        ]
    )

    st.bar_chart(chart)


# ============================================================
# RBI
# ============================================================

elif page == "🏦 RBI & Rates":

    st.title(
        "🏦 RBI, Monetary Policy & Interest Rates"
    )

    a, b, c, d = st.columns(4)

    a.metric(
        "Repo Rate",
        f"{values['Repo rate']:.2f}%"
    )

    b.metric(
        "CPI",
        f"{values['CPI inflation']:.2f}%"
    )

    c.metric(
        "Real Policy Rate",
        f"{values['Repo rate'] - values['CPI inflation']:.2f}%"
    )

    d.metric(
        "10Y G-Sec",
        f"{values['10Y G-Sec']:.2f}%"
    )

    st.divider()

    st.header(
        "How monetary policy reaches the economy"
    )

    df = pd.DataFrame(
        [
            ["1", "RBI policy rate", "Policy signal"],
            ["2", "Money-market conditions", "Liquidity and short-term rates"],
            ["3", "Bank lending rates", "Cost of borrowing"],
            ["4", "Credit demand", "Borrowing decisions"],
            ["5", "Consumption and investment", "Economic spending"],
            ["6", "Aggregate demand", "Output pressure"],
            ["7", "Inflation", "Price pressure"]
        ],
        columns=[
            "Step",
            "Channel",
            "Meaning"
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.header(
        "Rate Comparison"
    )

    rate_chart = pd.DataFrame(
        {
            "Rate": [
                values["CPI inflation"],
                values["Repo rate"],
                values["10Y G-Sec"]
            ]
        },
        index=[
            "CPI Inflation",
            "Repo Rate",
            "10Y G-Sec"
        ]
    )

    st.bar_chart(rate_chart)


# ============================================================
# BANKING
# ============================================================

elif page == "💳 Banking & Credit":

    st.title(
        "💳 Banking, Credit & Financial Conditions"
    )

    a, b = st.columns(2)

    a.metric(
        "Bank Credit Growth",
        f"{values['Bank credit growth']:.1f}%"
    )

    b.metric(
        "Credit Score",
        f"{pillars['Credit']}/100"
    )

    st.divider()

    if values["Bank credit growth"] >= 20:

        st.warning(
            "Credit growth is extremely strong. "
            "Watch deposit growth, liquidity, underwriting "
            "standards and asset quality."
        )

    elif values["Bank credit growth"] >= 15:

        st.success(
            "Credit growth is strong and can support "
            "consumption, investment and business financing."
        )

    else:

        st.info(
            "Credit growth is moderate. Examine it alongside "
            "GDP growth and investment."
        )

    st.header(
        "Who uses bank credit?"
    )

    df = pd.DataFrame(
        [
            [
                "Households",
                "Housing, vehicles, consumption",
                "Consumer demand"
            ],
            [
                "MSMEs",
                "Working capital and expansion",
                "Business activity"
            ],
            [
                "Corporates",
                "Capital expenditure",
                "Investment"
            ],
            [
                "NBFCs",
                "Specialised lending",
                "Financial transmission"
            ],
            [
                "Banks",
                "Credit creation",
                "Money transmission"
            ]
        ],
        columns=[
            "Borrower",
            "Typical use",
            "Macro impact"
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.header(
        "Credit Transmission"
    )

    st.markdown(
        "**Lower borrowing cost → more credit demand → "
        "more spending/investment → stronger demand**"
    )

    st.markdown(
        "The reverse can also happen when borrowing costs rise."
    )


# ============================================================
# EXTERNAL
# ============================================================

elif page == "🌐 External Sector":

    st.title(
        "🌐 External Sector & Currency"
    )

    a, b, c = st.columns(3)

    a.metric(
        "USD / INR",
        f"₹{values['USD/INR']:.2f}"
    )

    b.metric(
        "FX Reserves",
        f"${values['FX reserves']:.1f}B"
    )

    c.metric(
        "Import Cover",
        f"{values['Import cover']:.1f} months"
    )

    st.divider()

    external_chart = pd.DataFrame(
        {
            "Value": [
                values["FX reserves"],
                values["Import cover"]
            ]
        },
        index=[
            "FX Reserves ($ bn)",
            "Import Cover (months)"
        ]
    )

    st.bar_chart(
        external_chart
    )

    if (
        values["FX reserves"] >= 650
        and values["Import cover"] >= 9
    ):

        st.success(
            "India has a substantial external buffer "
            "based on reserves and import cover."
        )

    else:

        st.warning(
            "External buffers require closer monitoring."
        )

    st.header(
        "What moves the rupee?"
    )

    df = pd.DataFrame(
        [
            [
                "US dollar strength",
                "Can increase demand for dollars"
            ],
            [
                "Crude oil",
                "India's import requirement creates sensitivity"
            ],
            [
                "Capital flows",
                "Foreign investment affects currency demand"
            ],
            [
                "Trade balance",
                "Exports and imports affect foreign-currency flows"
            ],
            [
                "Interest-rate differential",
                "Relative returns influence capital flows"
            ],
            [
                "RBI intervention",
                "Can reduce excessive currency volatility"
            ]
        ],
        columns=[
            "Factor",
            "Transmission"
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FISCAL
# ============================================================

elif page == "🏛 Fiscal & Government":

    st.title(
        "🏛 Fiscal Policy & Government Finances"
    )

    st.markdown(
        "Fiscal policy influences demand through expenditure "
        "and taxation and affects long-term productive capacity "
        "through public investment."
    )

    df = pd.DataFrame(
        [
            [
                "Government expenditure",
                "Public demand"
            ],
            [
                "Capital expenditure",
                "Infrastructure and productive capacity"
            ],
            [
                "Revenue expenditure",
                "Regular government spending"
            ],
            [
                "Tax revenue",
                "Government income"
            ],
            [
                "Fiscal deficit",
                "Government borrowing requirement"
            ],
            [
                "Public debt",
                "Accumulated government liabilities"
            ]
        ],
        columns=[
            "Indicator",
            "Macro role"
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.header(
        "Why fiscal policy matters"
    )

    st.markdown(
        "**Short term:** Government spending can support aggregate demand."
    )

    st.markdown(
        "**Medium term:** Infrastructure spending can increase productive capacity."
    )

    st.markdown(
        "**Long term:** Persistent borrowing can increase debt and interest obligations."
    )

    st.info(
        "Use the DBIE Data Explorer to retrieve specific fiscal deficit, "
        "government revenue, expenditure and debt series."
    )


# ============================================================
# MARKETS
# ============================================================

elif page == "💹 Markets":

    st.title(
        "💹 Rates, Bonds & Market Signals"
    )

    a, b, c = st.columns(3)

    a.metric(
        "10Y G-Sec",
        f"{values['10Y G-Sec']:.2f}%"
    )

    b.metric(
        "Repo Rate",
        f"{values['Repo rate']:.2f}%"
    )

    c.metric(
        "CPI",
        f"{values['CPI inflation']:.2f}%"
    )

    st.divider()

    market_chart = pd.DataFrame(
        {
            "Value": [
                values["CPI inflation"],
                values["Repo rate"],
                values["10Y G-Sec"]
            ]
        },
        index=[
            "CPI Inflation",
            "Repo Rate",
            "10Y G-Sec"
        ]
    )

    st.bar_chart(
        market_chart
    )

    st.header(
        "Bond Yield Decoder"
    )

    st.markdown(
        "Government bond yields can move because of inflation "
        "expectations, future policy expectations, government "
        "borrowing, economic growth, global bond yields, currency "
        "conditions and capital flows."
    )


# ============================================================
# DIGITAL ECONOMY
# ============================================================

elif page == "📲 Digital Economy":

    st.title(
        "📲 Digital Economy & Payments"
    )

    st.markdown(
        "Digital financial infrastructure affects transaction speed, "
        "formalisation, financial inclusion and the availability "
        "of transaction data."
    )

    df = pd.DataFrame(
        [
            [
                "UPI",
                "Real-time digital payments",
                "Retail transaction infrastructure"
            ],
            [
                "IMPS",
                "Instant bank transfers",
                "Digital money movement"
            ],
            [
                "NEFT",
                "Electronic bank transfers",
                "Formal banking"
            ],
            [
                "Cards",
                "Digital retail payments",
                "Consumer spending"
            ],
            [
                "Mobile banking",
                "Digital banking access",
                "Financial inclusion"
            ],
            [
                "FinTech",
                "Technology-enabled finance",
                "Innovation and competition"
            ]
        ],
        columns=[
            "System",
            "Function",
            "Macro relevance"
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.header(
        "Digital Finance → Credit"
    )

    st.markdown(
        "**Digital transactions → financial records → "
        "better visibility → potential credit access**"
    )

    st.info(
        "Search UPI, digital payments, NEFT or IMPS "
        "in the DBIE Explorer for specific series."
    )


# ============================================================
# SCENARIO LAB
# ============================================================

elif page == "🧭 Scenario Lab":

    st.title(
        "🧭 Macro Scenario Lab"
    )

    st.markdown(
        "Change assumptions and see how the analytical macro "
        "score responds. This is a scenario tool, not an "
        "economic forecast."
    )

    c1, c2 = st.columns(2)

    with c1:

        scenario_gdp = st.slider(
            "Real GDP Growth (%)",
            0.0,
            12.0,
            float(values["GDP growth"]),
            0.1
        )

        scenario_inflation = st.slider(
            "CPI Inflation (%)",
            0.0,
            12.0,
            float(values["CPI inflation"]),
            0.1
        )

        scenario_credit = st.slider(
            "Bank Credit Growth (%)",
            0.0,
            30.0,
            float(values["Bank credit growth"]),
            0.5
        )

    with c2:

        scenario_repo = st.slider(
            "Repo Rate (%)",
            2.0,
            10.0,
            float(values["Repo rate"]),
            0.25
        )

        scenario_reserves = st.slider(
            "FX Reserves ($ bn)",
            300.0,
            1000.0,
            float(values["FX reserves"]),
            5.0
        )

        scenario_cover = st.slider(
            "Import Cover (months)",
            2.0,
            18.0,
            float(values["Import cover"]),
            0.5
        )

    scenario_score, scenario_pillars = calculate_macro_score(
        scenario_gdp,
        scenario_inflation,
        scenario_repo,
        scenario_credit,
        scenario_reserves,
        scenario_cover
    )

    st.divider()

    a, b, c = st.columns(3)

    a.metric(
        "Scenario Score",
        f"{scenario_score}/100"
    )

    b.metric(
        "Regime",
        regime(scenario_score)
    )

    c.metric(
        "Real Policy Rate",
        f"{scenario_repo - scenario_inflation:.2f}%"
    )

    st.bar_chart(
        pd.DataFrame(
            {
                "Score": scenario_pillars
            }
        )
    )

    if scenario_score >= 80:

        st.success(
            "Strong scenario: the overall combination of growth, "
            "inflation, credit, rates and external resilience is favourable."
        )

    elif scenario_score >= 65:

        st.info(
            "Healthy scenario: conditions are broadly supportive, "
            "although trade-offs remain."
        )

    elif scenario_score >= 50:

        st.warning(
            "Cautious scenario: macro conditions are mixed and "
            "several indicators need attention."
        )

    else:

        st.error(
            "Stressed scenario: macro pressure is significant."
        )

    st.header(
        "Conceptual Scenarios"
    )

    df = pd.DataFrame(
        [
            [
                "Bull",
                "High growth",
                "Controlled inflation",
                "Strong credit",
                "Strong macro"
            ],
            [
                "Base",
                "Healthy growth",
                "Manageable inflation",
                "Normal credit",
                "Balanced"
            ],
            [
                "Bear",
                "Weak growth",
                "High inflation",
                "Weak credit",
                "Stressed"
            ]
        ],
        columns=[
            "Scenario",
            "Growth",
            "Inflation",
            "Credit",
            "Interpretation"
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# DBIE EXPLORER
# ============================================================

elif page == "🔎 DBIE Data Explorer":

    st.title(
        "🔎 DBIE Data Explorer"
    )

    st.markdown(
        "Search the RBI Database on Indian Economy directly "
        "from the application."
    )

    query = st.text_input(
        "Search DBIE",
        placeholder=(
            "Try GDP, CPI, inflation, bank credit, "
            "exports, imports, UPI, fiscal deficit..."
        )
    )

    if query:

        with st.spinner(
            "Searching DBIE..."
        ):

            results = dbie_search(query)

        if results:

            df = pd.DataFrame(results)

            st.success(
                f"Found {len(results)} result(s)."
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "⬇ Download search results",
                df.to_csv(index=False),
                "dbie_search_results.csv",
                "text/csv"
            )

        else:

            st.warning(
                "No structured result was returned. "
                "Try a broader search."
            )

    st.divider()

    st.header(
        "Load a DBIE table directly"
    )

    schema = st.text_input(
        "Schema name"
    )

    table = st.text_input(
        "Table name"
    )

    if schema and table:

        if st.button(
            "Load table"
        ):

            with st.spinner(
                "Loading table..."
            ):

                rows = dbie_rows(
                    schema,
                    table
                )

            if rows:

                df = pd.DataFrame(
                    rows
                )

                st.success(
                    f"Loaded {len(df)} rows."
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                st.download_button(
                    "⬇ Download table",
                    df.to_csv(index=False),
                    "dbie_table.csv",
                    "text/csv"
                )

                numeric_columns = (
                    df.select_dtypes(
                        include=np.number
                    ).columns.tolist()
                )

                if numeric_columns:

                    selected = st.selectbox(
                        "Select a numeric series",
                        numeric_columns
                    )

                    chart = (
                        df[[selected]]
                        .dropna()
                    )

                    if len(chart) > 1:

                        st.line_chart(
                            chart
                        )

            else:

                st.error(
                    "The table could not be loaded. "
                    "Check the schema and table name."
                )


# ============================================================
# MACRO ACADEMY
# ============================================================

elif page == "📚 Macro Academy":

    st.title(
        "📚 Macro Academy"
    )

    topic = st.selectbox(
        "Choose a concept",
        [
            "GDP",
            "Inflation",
            "Repo Rate",
            "Real Interest Rate",
            "10-Year Government Bond Yield",
            "Fiscal Deficit",
            "Current Account",
            "Foreign Exchange Reserves",
            "Bank Credit",
            "Monetary Transmission",
            "Exchange Rate"
        ]
    )

    explanations = {

        "GDP":
            "GDP measures the value of final goods and services "
            "produced within an economy. Real GDP growth focuses "
            "on changes in actual output after accounting for "
            "price effects.",

        "Inflation":
            "Inflation is the rate at which the general price level "
            "increases. Persistent inflation reduces purchasing power.",

        "Repo Rate":
            "The repo rate is the RBI's main policy interest rate. "
            "It influences broader financial conditions and "
            "borrowing costs.",

        "Real Interest Rate":
            "A simple approximation is nominal interest rate minus "
            "inflation. Here, the dashboard uses Repo Rate minus "
            "CPI Inflation.",

        "10-Year Government Bond Yield":
            "The 10-year yield reflects expectations about inflation, "
            "growth, future interest rates, government borrowing "
            "and global markets.",

        "Fiscal Deficit":
            "Fiscal deficit represents the government's financing "
            "gap and therefore its borrowing requirement.",

        "Current Account":
            "The current account covers major international "
            "transactions involving goods, services, income "
            "and transfers.",

        "Foreign Exchange Reserves":
            "Foreign exchange reserves provide a buffer against "
            "external shocks, currency volatility and financing pressure.",

        "Bank Credit":
            "Bank credit represents financing provided by banks "
            "to households, businesses and other borrowers.",

        "Monetary Transmission":
            "Monetary transmission describes how central-bank "
            "policy influences financial conditions, credit, "
            "spending, output and inflation.",

        "Exchange Rate":
            "USD/INR tells us how many rupees are required to "
            "purchase one US dollar. A higher number generally "
            "means a weaker rupee against the dollar."
    }

    st.markdown(
        f"""
        <div class="macro-card">
            <h3>{topic}</h3>
            <p>{explanations[topic]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.header(
        "Indicator Relationships"
    )

    df = pd.DataFrame(
        [
            [
                "GDP ↑",
                "Inflation",
                "Strong demand can increase price pressure"
            ],
            [
                "Inflation ↑",
                "RBI",
                "May require tighter policy"
            ],
            [
                "Repo ↑",
                "Credit",
                "Borrowing generally becomes more expensive"
            ],
            [
                "Credit ↑",
                "GDP",
                "Can support spending and investment"
            ],
            [
                "Oil ↑",
                "Inflation",
                "Raises import costs"
            ],
            [
                "USD/INR ↑",
                "Imported inflation",
                "Imports become more expensive"
            ],
            [
                "Reserves ↑",
                "External resilience",
                "Larger external buffer"
            ]
        ],
        columns=[
            "Change",
            "Connected variable",
            "Possible mechanism"
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        <b>India Macro Intelligence Terminal</b><br><br>
        Built as a macroeconomic research and educational dashboard.<br>
        Primary data framework: RBI Database on Indian Economy (DBIE).<br><br>
        The composite score, scenario analysis and interpretations are
        analytical features created for this application and are not
        official RBI ratings, forecasts or investment advice.
    </div>
    """,
    unsafe_allow_html=True
)
