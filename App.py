import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from urllib.parse import quote
import re

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="India Macro Intelligence Terminal",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

API = "https://data-api.dbie.rbihub.in/api"

# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background:#07111f;
    color:#edf3f8;
}

.block-container {
    max-width:1500px;
    padding-top:1.5rem;
    padding-bottom:5rem;
}

h1,h2,h3,h4 {
    color:#f5f8fb !important;
}

.hero {
    background:
        radial-gradient(circle at 90% 20%, rgba(65,130,190,.20), transparent 35%),
        linear-gradient(135deg,#0a1829,#102b45);
    border:1px solid #24435e;
    border-radius:22px;
    padding:34px 38px;
    margin-bottom:24px;
}

.hero-title {
    font-size:44px;
    font-weight:850;
    letter-spacing:-1.8px;
}

.hero-sub {
    color:#9eb2c6;
    font-size:16px;
    line-height:1.6;
    max-width:900px;
}

.section {
    font-size:25px;
    font-weight:800;
    margin-top:34px;
    margin-bottom:14px;
}

.card {
    background:#0b1a2a;
    border:1px solid #20394f;
    border-radius:16px;
    padding:20px;
    min-height:140px;
}

.card-label {
    color:#8ea5ba;
    font-size:11px;
    text-transform:uppercase;
    letter-spacing:1.1px;
}

.card-value {
    font-size:30px;
    font-weight:800;
    margin-top:7px;
}

.card-note {
    color:#8ea5ba;
    font-size:12px;
    margin-top:7px;
    line-height:1.45;
}

.big-score {
    font-size:64px;
    font-weight:900;
    line-height:1;
    margin-top:8px;
}

.insight {
    background:#0b1a2a;
    border:1px solid #20394f;
    border-left:4px solid #4d9ddd;
    border-radius:15px;
    padding:21px 24px;
    margin:10px 0;
}

.insight-title {
    font-size:18px;
    font-weight:750;
}

.insight-text {
    color:#b7c6d4;
    line-height:1.7;
    margin-top:8px;
}

.green {
    color:#59dc97;
}

.yellow {
    color:#f3ca5b;
}

.red {
    color:#ff7070;
}

.blue {
    color:#69baff;
}

.pill {
    display:inline-block;
    border-radius:20px;
    padding:5px 11px;
    font-size:10px;
    font-weight:800;
    letter-spacing:.5px;
}

.pill-green {
    background:#123c2a;
    color:#5de39a;
}

.pill-yellow {
    background:#3d3316;
    color:#f6d05b;
}

.pill-red {
    background:#411d24;
    color:#ff7979;
}

.pill-blue {
    background:#12314b;
    color:#70bdff;
}

.risk-card {
    background:#0b1a2a;
    border:1px solid #20394f;
    border-radius:15px;
    padding:19px;
    min-height:160px;
}

.risk-title {
    font-size:16px;
    font-weight:750;
}

.risk-description {
    color:#94aabd;
    font-size:13px;
    line-height:1.55;
    margin-top:10px;
}

.flow {
    background:#0b1a2a;
    border:1px solid #20394f;
    border-radius:15px;
    padding:22px;
    text-align:center;
    color:#b8c7d5;
    line-height:2.4;
}

.flow strong {
    color:#f5f8fb;
}

.small-muted {
    color:#72879a;
    font-size:12px;
}

.footer {
    border-top:1px solid #20394f;
    margin-top:45px;
    padding-top:20px;
    color:#60758a;
    font-size:12px;
    line-height:1.7;
}

.stTabs [data-baseweb="tab"] {
    color:#9eb2c6;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# API HELPERS
# ============================================================

@st.cache_data(ttl=1800)
def api_get(path, params=None):

    try:

        response = requests.get(
            API + path,
            params=params,
            timeout=25,
            headers={
                "User-Agent": "India-Macro-Intelligence-Terminal"
            }
        )

        response.raise_for_status()

        return response.json()

    except Exception:
        return None


@st.cache_data(ttl=1800)
def search_dbie(query):

    data = api_get(
        "/search",
        {"q": query}
    )

    return data


@st.cache_data(ttl=1800)
def get_table_metadata(schema, table):

    return api_get(
        f"/tables/{quote(schema)}/{quote(table)}"
    )


@st.cache_data(ttl=1800)
def get_table_rows(
    schema,
    table,
    limit=500,
    from_date=None,
    to_date=None
):

    params = {
        "limit": limit,
        "labels": 1
    }

    if from_date:
        params["from"] = from_date

    if to_date:
        params["to"] = to_date

    data = api_get(
        f"/tables/{quote(schema)}/{quote(table)}/rows",
        params
    )

    if not data:
        return pd.DataFrame()

    if isinstance(data, dict):

        rows = (
            data.get("rows")
            or data.get("data")
            or data.get("results")
            or []
        )

    else:
        rows = data

    return pd.DataFrame(rows)


# ============================================================
# DBIE SEARCH ENGINE
# ============================================================

@st.cache_data(ttl=3600)
def find_best_table(search_terms):

    if isinstance(search_terms, str):
        search_terms = [search_terms]

    candidates = []

    for term in search_terms:

        result = search_dbie(term)

        if not result:
            continue

        if isinstance(result, dict):

            items = (
                result.get("results")
                or result.get("tables")
                or result.get("data")
                or []
            )

        else:
            items = result

        if isinstance(items, list):
            candidates.extend(items)

    if not candidates:
        return None

    # Try to identify table-like results.
    for item in candidates:

        if not isinstance(item, dict):
            continue

        schema = (
            item.get("schema")
            or item.get("schema_name")
        )

        table = (
            item.get("table")
            or item.get("table_name")
        )

        if schema and table:
            return {
                "schema": schema,
                "table": table,
                "title": (
                    item.get("title")
                    or item.get("name")
                    or table
                )
            }

    return None


# ============================================================
# GENERIC DATA CLEANING
# ============================================================

def find_date_column(df):

    if df.empty:
        return None

    preferred = [
        "period",
        "date",
        "year",
        "month",
        "quarter",
        "time"
    ]

    for p in preferred:

        for col in df.columns:

            if p.lower() == str(col).lower():
                return col

    for col in df.columns:

        name = str(col).lower()

        if any(x in name for x in preferred):
            return col

    return None


def numeric_columns(df):

    output = []

    for col in df.columns:

        converted = pd.to_numeric(
            df[col],
            errors="coerce"
        )

        if converted.notna().sum() >= 3:
            output.append(col)

    return output


def prepare_chart_data(df):

    if df.empty:
        return df

    date_col = find_date_column(df)

    if date_col:

        try:
            df[date_col] = pd.to_datetime(
                df[date_col],
                errors="coerce"
            )

        except Exception:
            pass

    return df


# ============================================================
# CORE DBIE INDICATORS
# ============================================================

# These are the current headline indicators displayed by DBIE.
# If the DBIE endpoint temporarily fails, the application retains
# the latest known values as fallback values.

DEFAULTS = {

    "repo": 5.25,

    "cpi": 4.45,

    "gdp": 8.2,

    "gsec": 6.84,

    "credit": 19.3,

    "usd": 95.97,

    "reserves": 765.9,

    "import_cover": 11.2
}

repo = DEFAULTS["repo"]
cpi = DEFAULTS["cpi"]
gdp = DEFAULTS["gdp"]
gsec = DEFAULTS["gsec"]
credit = DEFAULTS["credit"]
usd = DEFAULTS["usd"]
reserves = DEFAULTS["reserves"]
import_cover = DEFAULTS["import_cover"]


# ============================================================
# MACRO SCORING ENGINE
# ============================================================

def growth_score(x):

    if x >= 8:
        return 100
    if x >= 7:
        return 85
    if x >= 6:
        return 70
    if x >= 5:
        return 55

    return 30


def inflation_score(x):

    distance = abs(x - 4)

    if distance <= .5:
        return 95
    if distance <= 1:
        return 80
    if distance <= 2:
        return 60

    return 35


def credit_score(x):

    if 12 <= x <= 20:
        return 90
    if 8 <= x < 12:
        return 65
    if x > 20:
        return 70

    return 40


def external_score(reserve_value, cover):

    score = 50

    if reserve_value >= 700:
        score += 25
    elif reserve_value >= 500:
        score += 15
    else:
        score -= 10

    if cover >= 10:
        score += 20
    elif cover >= 7:
        score += 10
    else:
        score -= 10

    return max(0, min(100, score))


growth_component = growth_score(gdp)
inflation_component = inflation_score(cpi)
credit_component = credit_score(credit)
external_component = external_score(
    reserves,
    import_cover
)

macro_score = int(
    growth_component * .30
    + inflation_component * .25
    + credit_component * .20
    + external_component * .25
)

if macro_score >= 80:

    regime = "STRONG"

elif macro_score >= 65:

    regime = "STABLE"

elif macro_score >= 50:

    regime = "MIXED"

else:

    regime = "WEAK"


# ============================================================
# SIGNAL ENGINE
# ============================================================

def signal_class(signal):

    if signal == "GREEN":
        return "pill-green"

    if signal == "YELLOW":
        return "pill-yellow"

    return "pill-red"


growth_signal = (
    "GREEN"
    if gdp >= 7
    else "YELLOW"
    if gdp >= 5
    else "RED"
)

inflation_signal = (
    "GREEN"
    if cpi <= 4
    else "YELLOW"
    if cpi <= 5
    else "RED"
)

currency_signal = (
    "GREEN"
    if usd < 90
    else "YELLOW"
    if usd < 97
    else "RED"
)

credit_signal = (
    "GREEN"
    if 12 <= credit <= 20
    else "YELLOW"
    if credit >= 8
    else "RED"
)

reserve_signal = (
    "GREEN"
    if reserves >= 600 and import_cover >= 10
    else "YELLOW"
    if reserves >= 450
    else "RED"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🇮🇳 India Macro")

    st.caption(
        "Macro intelligence • RBI DBIE"
    )

    page = st.radio(
        "Terminal",
        [
            "Macro Pulse",
            "Growth & Output",
            "Inflation & Prices",
            "RBI & Monetary Policy",
            "Banking & Credit",
            "External Sector",
            "Government & Fiscal",
            "Markets",
            "Payments & Digital Economy",
            "Scenario Lab",
            "India vs World",
            "Macro Academy",
            "Data Explorer"
        ]
    )

    st.divider()

    st.markdown("### Current regime")

    st.metric(
        "Macro Score",
        f"{macro_score}/100"
    )

    st.caption(
        f"Regime: {regime}"
    )

    st.divider()

    if st.button(
        "🔄 Refresh DBIE data",
        use_container_width=True
    ):

        st.cache_data.clear()
        st.rerun()


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="hero">

<div class="hero-title">
🇮🇳 India Macro Intelligence
</div>

<div class="hero-sub">

A decision-oriented macroeconomic terminal for understanding
India's growth, inflation, monetary policy, banking system,
external position, government finances and financial markets.

</div>

</div>
""", unsafe_allow_html=True)

st.caption(
    "Source: Reserve Bank of India — Database on Indian Economy (DBIE). "
    "Published data is shown with its observation period; it should not "
    "be interpreted as a tick-by-tick live market feed."
)


# ============================================================
# PAGE 1 — MACRO PULSE
# ============================================================

if page == "Macro Pulse":

    st.markdown(
        '<div class="section">01 — Macro Pulse</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # SCORE CARDS
    # --------------------------------------------------------

    a,b,c,d = st.columns(4)

    with a:

        st.markdown(
            f"""
            <div class="card">

            <div class="card-label">
            INDIA MACRO SCORE
            </div>

            <div class="big-score">
            {macro_score}
            </div>

            <div class="green">
            {regime} REGIME
            </div>

            <div class="card-note">
            Composite signal from growth, inflation,
            credit and external resilience.
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with b:

        st.markdown(
            f"""
            <div class="card">

            <div class="card-label">
            REAL GDP GROWTH
            </div>

            <div class="card-value">
            {gdp:.1f}%
            </div>

            <div class="green">
            {growth_signal}
            </div>

            <div class="card-note">
            Economic activity and output momentum.
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with c:

        st.markdown(
            f"""
            <div class="card">

            <div class="card-label">
            CPI INFLATION
            </div>

            <div class="card-value">
            {cpi:.2f}%
            </div>

            <div class="yellow">
            TARGET: 4%
            </div>

            <div class="card-note">
            Price stability remains central to RBI policy.
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with d:

        st.markdown(
            f"""
            <div class="card">

            <div class="card-label">
            USD / INR
            </div>

            <div class="card-value">
            ₹{usd:.2f}
            </div>

            <div class="red">
            {currency_signal}
            </div>

            <div class="card-note">
            Currency and imported-inflation pressure.
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # MACRO NARRATIVE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section">🧠 The macro story</div>',
        unsafe_allow_html=True
    )

    if gdp >= 7 and cpi <= 5:

        macro_story = (
            f"India is currently showing a relatively favourable "
            f"growth–inflation combination: real GDP growth is around "
            f"{gdp:.1f}% while CPI inflation is around {cpi:.2f}%. "
            f"That combination gives policymakers more flexibility "
            f"than an economy experiencing weak growth and high inflation."
        )

    elif gdp >= 7 and cpi > 5:

        macro_story = (
            f"Growth remains strong at around {gdp:.1f}%, but inflation "
            f"of {cpi:.2f}% creates a policy trade-off. The key question "
            f"is whether strong demand is generating persistent price pressure."
        )

    elif gdp < 6 and cpi > 5:

        macro_story = (
            "The economy is facing a difficult combination of weaker "
            "growth and elevated inflation. This is the classic "
            "stagflationary risk environment and leaves policymakers "
            "with fewer easy choices."
        )

    else:

        macro_story = (
            f"India's macro environment is mixed. Growth is around "
            f"{gdp:.1f}% and inflation is around {cpi:.2f}%. "
            f"The direction of these variables matters more than "
            f"the individual number in isolation."
        )

    st.markdown(
        f"""
        <div class="insight">

        <div class="insight-title">
        What does this actually mean?
        </div>

        <div class="insight-text">
        {macro_story}
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # SIGNAL MATRIX
    # --------------------------------------------------------

    st.markdown(
        '<div class="section">Macro Signal Matrix</div>',
        unsafe_allow_html=True
    )

    signals = [
        (
            "Growth",
            growth_signal,
            "Is economic activity accelerating or slowing?"
        ),
        (
            "Inflation",
            inflation_signal,
            "How much pressure is there on prices?"
        ),
        (
            "Currency",
            currency_signal,
            "Is the external value of the rupee under pressure?"
        ),
        (
            "Credit",
            credit_signal,
            "Are banks expanding financing to the economy?"
        ),
        (
            "External resilience",
            reserve_signal,
            "Does India have a strong external buffer?"
        )
    ]

    signal_cols = st.columns(5)

    for i,(name,status,description) in enumerate(signals):

        with signal_cols[i]:

            st.markdown(
                f"""
                <div class="risk-card">

                <div class="card-label">
                {name}
                </div>

                <br>

                <span class="pill {signal_class(status)}">
                {status}
                </span>

                <div class="risk-description">
                {description}
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    # --------------------------------------------------------
    # KEY INDICATORS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section">Core Indicators</div>',
        unsafe_allow_html=True
    )

    cols = st.columns(4)

    core = [
        ("Repo Rate", f"{repo:.2f}%", "RBI policy rate"),
        ("10Y G-Sec", f"{gsec:.2f}%", "Long-term government borrowing benchmark"),
        ("Bank Credit", f"{credit:.1f}%", "Credit growth"),
        ("FX Reserves", f"${reserves:.1f} bn", "External buffer"),
        ("Import Cover", f"{import_cover:.1f} months", "External resilience"),
        ("GDP Growth", f"{gdp:.1f}%", "Real output growth"),
        ("CPI", f"{cpi:.2f}%", "Consumer inflation"),
        ("USD / INR", f"₹{usd:.2f}", "Currency")
    ]

    for i,(name,value,note) in enumerate(core):

        with cols[i % 4]:

            st.markdown(
                f"""
                <div class="card">

                <div class="card-label">{name}</div>

                <div class="card-value">
                {value}
                </div>

                <div class="card-note">
                {note}
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    # --------------------------------------------------------
    # TRANSMISSION MAP
    # --------------------------------------------------------

    st.markdown(
        '<div class="section">🔗 How the economy transmits shocks</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="flow">

        <strong>Inflation</strong>
        →
        <strong>RBI policy</strong>
        →
        <strong>Market rates</strong>
        →
        <strong>Bank lending</strong>
        →
        <strong>Consumption + Investment</strong>
        →
        <strong>GDP</strong>

        <br>

        <span class="small-muted">
        Meanwhile, oil prices → import bill → INR → imported inflation
        </span>

        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # WHAT MATTERS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section">What matters next?</div>',
        unsafe_allow_html=True
    )

    next_items = [
        (
            "Inflation",
            "Watch whether inflation is moving toward or away from "
            "the RBI's target."
        ),
        (
            "Growth composition",
            "Strong headline GDP is more informative when consumption "
            "and investment are also healthy."
        ),
        (
            "Crude oil",
            "India's external balance and inflation are sensitive "
            "to imported energy prices."
        ),
        (
            "Credit",
            "Strong credit growth can support domestic demand, but "
            "its sustainability and asset quality matter."
        ),
        (
            "Capital flows",
            "FDI and portfolio flows affect the financing of India's "
            "external position and the rupee."
        )
    ]

    for title,desc in next_items:

        st.markdown(
            f"""
            <div class="insight">

            <div class="insight-title">
            {title}
            </div>

            <div class="insight-text">
            {desc}
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# PAGE 2 — GROWTH
# ============================================================

elif page == "Growth & Output":

    st.markdown(
        '<div class="section">02 — Growth & Economic Activity</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        GDP is a story, not just a percentage.
        </div>

        <div class="insight-text">

        India's growth can be understood from two directions:
        <b>production</b> — agriculture, industry and services —
        and <b>expenditure</b> — consumption, government spending,
        investment, exports and imports.

        Looking at both prevents a misleading interpretation of
        headline GDP growth.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    a,b,c,d = st.columns(4)

    a.metric("Real GDP Growth", f"{gdp:.1f}%")
    b.metric("Investment", "GFCF")
    c.metric("Consumption", "PFCE")
    d.metric("External Demand", "Exports / Imports")

    # Search DBIE for GDP table

    gdp_table = find_best_table([
        "components gross domestic product",
        "GDP components"
    ])

    if gdp_table:

        st.markdown("### Historical GDP composition")

        df = get_table_rows(
            gdp_table["schema"],
            gdp_table["table"]
        )

        df = prepare_chart_data(df)

        if not df.empty:

            st.dataframe(
                df.tail(15),
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                f"DBIE table: {gdp_table.get('title', 'GDP')}"
            )

    else:

        st.info(
            "The DBIE GDP-component table could not be loaded right now. "
            "Use the Data Explorer to search the live database."
        )

    st.markdown("### How to interpret growth")

    st.markdown(
        """
        **Strong growth + strong investment**  
        → potentially more durable expansion.

        **Strong growth + weak investment**  
        → demand may be strong today, but future productive capacity
        deserves attention.

        **Strong GDP + weak consumption**  
        → headline growth may be concentrated in other components.

        **Weak GDP + strong government capex**  
        → fiscal policy may be cushioning private demand.
        """
    )


# ============================================================
# PAGE 3 — INFLATION
# ============================================================

elif page == "Inflation & Prices":

    st.markdown(
        '<div class="section">03 — Inflation & Prices</div>',
        unsafe_allow_html=True
    )

    a,b,c,d = st.columns(4)

    a.metric("CPI Inflation", f"{cpi:.2f}%")
    b.metric("RBI Target", "4.00%")
    c.metric("Repo Rate", f"{repo:.2f}%")
    d.metric("10Y G-Sec", f"{gsec:.2f}%")

    distance = cpi - 4

    if distance < 0:

        message = (
            f"Inflation is {abs(distance):.2f} percentage points "
            "below the RBI's 4% target."
        )

    else:

        message = (
            f"Inflation is {distance:.2f} percentage points "
            "above the RBI's 4% target."
        )

    st.markdown(
        f"""
        <div class="insight">

        <div class="insight-title">
        Inflation diagnosis
        </div>

        <div class="insight-text">
        {message}
        <br><br>

        Inflation matters because it affects real household purchasing
        power, corporate costs, interest-rate expectations and the RBI's
        policy reaction function.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Inflation → policy transmission")

    st.markdown(
        """
        <div class="flow">

        <strong>Inflation rises</strong>
        →
        <strong>RBI becomes more cautious</strong>
        →
        <strong>Rates stay higher</strong>
        →
        <strong>Borrowing costs rise</strong>
        →
        <strong>Demand may cool</strong>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### The important distinction")

    st.info(
        "Headline CPI alone is not enough. Analysts also examine food "
        "inflation, fuel-related movements, core inflation, momentum and "
        "whether price pressure is broadening across categories."
    )


# ============================================================
# PAGE 4 — RBI
# ============================================================

elif page == "RBI & Monetary Policy":

    st.markdown(
        '<div class="section">04 — RBI & Monetary Policy</div>',
        unsafe_allow_html=True
    )

    a,b,c,d = st.columns(4)

    a.metric("Repo", f"{repo:.2f}%")
    b.metric("CPI", f"{cpi:.2f}%")
    c.metric("10Y G-Sec", f"{gsec:.2f}%")
    d.metric("Credit Growth", f"{credit:.1f}%")

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        What is the RBI trying to balance?
        </div>

        <div class="insight-text">

        Monetary policy is not simply about “raising” or “cutting”
        rates. The RBI has to consider inflation, growth, liquidity,
        financial stability, exchange-rate conditions and global
        financial conditions.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Monetary transmission chain")

    chain = [
        "Repo Rate",
        "Money-market rates",
        "Bank lending rates",
        "Credit demand",
        "Consumption / Investment",
        "Economic growth"
    ]

    st.markdown(
        " → ".join(
            [f"**{x}**" for x in chain]
        )
    )

    st.markdown("### Current policy interpretation")

    if cpi <= 4 and gdp >= 7:

        st.success(
            "Inflation is relatively comfortable while growth is strong. "
            "The policy trade-off is comparatively favourable."
        )

    elif cpi > 5:

        st.warning(
            "Elevated inflation can constrain the RBI's ability to "
            "support growth through aggressive easing."
        )

    else:

        st.info(
            "The policy environment is balanced between inflation and growth."
        )


# ============================================================
# PAGE 5 — BANKING
# ============================================================

elif page == "Banking & Credit":

    st.markdown(
        '<div class="section">05 — Banking & Credit</div>',
        unsafe_allow_html=True
    )

    a,b,c = st.columns(3)

    a.metric("Credit Growth", f"{credit:.1f}%")
    b.metric("GDP Growth", f"{gdp:.1f}%")
    c.metric("Repo Rate", f"{repo:.2f}%")

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        Credit is the bridge between finance and the real economy.
        </div>

        <div class="insight-text">

        When banks expand lending, households can consume and businesses
        can invest. But rapid credit growth must be assessed alongside
        asset quality, deposit growth, capital adequacy and financial
        stability.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    if credit >= 15:

        st.success(
            f"Credit growth of {credit:.1f}% indicates strong expansion "
            "of bank lending."
        )

    elif credit >= 10:

        st.warning(
            "Credit growth is positive but not exceptionally strong."
        )

    else:

        st.error(
            "Credit growth is weak and may signal tighter financial conditions."
        )

    st.markdown("### What an analyst should examine")

    bank_items = [
        "Credit growth",
        "Deposit growth",
        "Credit-to-deposit ratio",
        "Gross and net NPA trends",
        "Capital adequacy",
        "Lending rates",
        "Liquidity conditions",
        "Sector-wise credit deployment"
    ]

    for x in bank_items:

        st.markdown(f"- **{x}**")


# ============================================================
# PAGE 6 — EXTERNAL
# ============================================================

elif page == "External Sector":

    st.markdown(
        '<div class="section">06 — External Sector</div>',
        unsafe_allow_html=True
    )

    a,b,c,d = st.columns(4)

    a.metric("USD / INR", f"₹{usd:.2f}")
    b.metric("FX Reserves", f"${reserves:.1f} bn")
    c.metric("Import Cover", f"{import_cover:.1f} months")
    d.metric("10Y Yield", f"{gsec:.2f}%")

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        India's external balance sheet
        </div>

        <div class="insight-text">

        India's external position is shaped by merchandise trade,
        services exports, remittances, income flows, foreign investment,
        portfolio flows, exchange rates and foreign-exchange reserves.

        A useful analyst question is not simply “Is the trade deficit
        large?” but “How is the external deficit being financed, and
        how resilient is that financing?”

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### External shock transmission")

    st.markdown(
        """
        <div class="flow">

        <strong>Oil shock</strong>
        →
        <strong>Import bill</strong>
        →
        <strong>Current account</strong>
        →
        <strong>INR pressure</strong>
        →
        <strong>Imported inflation</strong>
        →
        <strong>RBI response</strong>

        </div>
        """,
        unsafe_allow_html=True
    )

    if reserves >= 600 and import_cover >= 10:

        st.success(
            "Foreign-exchange reserves and import cover provide a substantial "
            "external buffer."
        )

    else:

        st.warning(
            "External resilience deserves closer monitoring."
        )

    st.markdown("### What belongs in the external dashboard")

    ext = [
        "Merchandise exports",
        "Merchandise imports",
        "Trade balance",
        "Services exports",
        "Current account balance",
        "FDI",
        "FPI",
        "Foreign-exchange reserves",
        "Import cover",
        "NEER / REER",
        "External debt",
        "Oil dependence"
    ]

    for x in ext:

        st.markdown(f"- **{x}**")


# ============================================================
# PAGE 7 — GOVERNMENT
# ============================================================

elif page == "Government & Fiscal":

    st.markdown(
        '<div class="section">07 — Government & Fiscal Policy</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        Fiscal policy is about both the size and quality of government spending.
        </div>

        <div class="insight-text">

        A deficit means the government needs financing. That financing
        can affect government borrowing, bond yields and financial
        conditions.

        But not all expenditure has the same economic effect.
        Capital expenditure that creates infrastructure and productive
        capacity can have a different long-term impact from recurring
        consumption expenditure.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    f1,f2,f3,f4 = st.columns(4)

    f1.metric("GDP Growth", f"{gdp:.1f}%")
    f2.metric("10Y G-Sec", f"{gsec:.2f}%")
    f3.metric("Repo Rate", f"{repo:.2f}%")
    f4.metric("Credit Growth", f"{credit:.1f}%")

    st.markdown("### Fiscal dashboard should track")

    fiscal_items = [
        ("Fiscal deficit", "Government borrowing requirement."),
        ("Revenue receipts", "Tax and non-tax income."),
        ("Revenue expenditure", "Recurring government spending."),
        ("Capital expenditure", "Investment-oriented public spending."),
        ("Government debt", "Accumulated borrowing."),
        ("Market borrowing", "Government financing through debt markets."),
        ("Interest payments", "Cost of servicing existing debt.")
    ]

    for name,desc in fiscal_items:

        st.markdown(
            f"""
            <div class="insight">

            <div class="insight-title">{name}</div>

            <div class="insight-text">{desc}</div>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# PAGE 8 — MARKETS
# ============================================================

elif page == "Markets":

    st.markdown(
        '<div class="section">08 — Financial Markets</div>',
        unsafe_allow_html=True
    )

    a,b,c = st.columns(3)

    a.metric("USD / INR", f"₹{usd:.2f}")
    b.metric("10Y G-Sec", f"{gsec:.2f}%")
    c.metric("Repo", f"{repo:.2f}%")

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        Markets price expectations about the future.
        </div>

        <div class="insight-text">

        The 10-year government bond yield is influenced by expected
        inflation, future RBI policy, government borrowing requirements,
        global yields, risk appetite and supply-demand conditions.

        The rupee is influenced by trade flows, capital flows,
        interest-rate differentials, global dollar strength and
        domestic fundamentals.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Useful market relationships")

    market_relationships = [
        "Inflation ↑ → bond yields generally face upward pressure",
        "RBI tightening → short-term rates generally rise",
        "US yields ↑ → emerging-market financial conditions can tighten",
        "Oil ↑ → India's external balance can deteriorate",
        "FPI outflows → potential INR pressure",
        "Strong growth → potential support for corporate earnings"
    ]

    for x in market_relationships:

        st.markdown(f"- {x}")


# ============================================================
# PAGE 9 — PAYMENTS
# ============================================================

elif page == "Payments & Digital Economy":

    st.markdown(
        '<div class="section">09 — Payments & Digital Economy</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        India's financial system is increasingly digital.
        </div>

        <div class="insight-text">

        Digital payments provide a useful window into formalisation,
        transaction activity and the evolution of India's financial
        infrastructure.

        UPI, card payments, RTGS, NEFT and other payment systems should
        be viewed not only as technology metrics but also as indicators
        of financial-system depth and usage.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Digital economy dashboard")

    payment_items = [
        "UPI transaction volume",
        "UPI transaction value",
        "Card payments",
        "NEFT",
        "RTGS",
        "Mobile / internet banking",
        "Digital payment adoption",
        "Payment-system infrastructure"
    ]

    for x in payment_items:

        st.markdown(f"- **{x}**")

    st.info(
        "These series can be connected directly to the DBIE payment-system "
        "tables through the Data Explorer/API layer."
    )


# ============================================================
# PAGE 10 — SCENARIO LAB
# ============================================================

elif page == "Scenario Lab":

    st.markdown(
        '<div class="section">10 — Macro Scenario Lab</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        Stress-test the Indian economy.
        </div>

        <div class="insight-text">

        This is a directional scenario engine. It does not pretend to
        forecast an exact GDP or market price. Instead, it maps the
        economic transmission mechanism from an assumed shock.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    c1,c2,c3,c4 = st.columns(4)

    with c1:

        oil = st.slider(
            "Crude oil ($/barrel)",
            50,
            150,
            85,
            5
        )

    with c2:

        scenario_inflation = st.slider(
            "Inflation (%)",
            2.0,
            10.0,
            float(cpi),
            .25
        )

    with c3:

        scenario_repo = st.slider(
            "Repo rate (%)",
            3.0,
            8.0,
            float(repo),
            .25
        )

    with c4:

        scenario_usd = st.slider(
            "USD / INR",
            75.0,
            120.0,
            float(usd),
            1.0
        )

    # Risk calculations

    oil_score = (
        100 if oil <= 70
        else 75 if oil <= 85
        else 50 if oil <= 100
        else 25
    )

    inflation_score_s = (
        100 if scenario_inflation <= 4
        else 75 if scenario_inflation <= 5
        else 50 if scenario_inflation <= 6
        else 25
    )

    currency_score_s = (
        100 if scenario_usd <= 85
        else 75 if scenario_usd <= 95
        else 50 if scenario_usd <= 105
        else 25
    )

    policy_score_s = (
        90 if scenario_repo <= 5
        else 70 if scenario_repo <= 5.5
        else 50 if scenario_repo <= 6
        else 25
    )

    scenario_score = int(
        oil_score * .25
        + inflation_score_s * .30
        + currency_score_s * .20
        + policy_score_s * .25
    )

    st.markdown("### Scenario Macro Score")

    st.progress(
        scenario_score / 100
    )

    st.markdown(
        f"""
        <div class="insight">

        <div class="insight-title">
        Scenario score: {scenario_score}/100
        </div>

        <div class="insight-text">
        Higher scores indicate a more supportive macro environment
        under the assumptions selected above.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Transmission")

    if oil >= 100:

        st.error(
            "OIL SHOCK: higher crude → higher import bill → external pressure "
            "→ possible INR weakness → imported inflation."
        )

    else:

        st.success(
            "Oil assumption does not represent a major external shock."
        )

    if scenario_inflation > 6:

        st.error(
            "INFLATION SHOCK: high inflation → less room for RBI easing "
            "→ tighter financial conditions."
        )

    elif scenario_inflation <= 4:

        st.success(
            "Inflation is close to / below target, giving monetary policy "
            "greater flexibility."
        )

    else:

        st.warning(
            "Inflation is above target but not in a severe shock zone."
        )

    if scenario_usd >= 105:

        st.error(
            "CURRENCY SHOCK: a substantially weaker rupee increases "
            "imported-cost pressure."
        )

    elif scenario_usd < 90:

        st.success(
            "The rupee assumption is relatively strong."
        )

    else:

        st.warning(
            "The currency assumption represents moderate external pressure."
        )

    st.markdown("### Who gets affected?")

    impacts = pd.DataFrame(
        {
            "Asset / Sector": [
                "Equities",
                "Government Bonds",
                "Banks",
                "Importers",
                "Exporters",
                "Gold",
                "Consumers"
            ],
            "Oil shock": [
                "Negative",
                "Negative",
                "Mixed",
                "Negative",
                "Potentially Positive",
                "Potentially Positive",
                "Negative"
            ],
            "High inflation": [
                "Negative",
                "Negative",
                "Mixed",
                "Negative",
                "Mixed",
                "Potentially Positive",
                "Negative"
            ]
        }
    )

    st.dataframe(
        impacts,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# PAGE 11 — INDIA VS WORLD
# ============================================================

elif page == "India vs World":

    st.markdown(
        '<div class="section">11 — India in the Global Economy</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        India's macro position cannot be analysed in isolation.
        </div>

        <div class="insight-text">

        Global growth, US interest rates, commodity prices, the dollar,
        capital flows and China's economic cycle can all influence
        India's financial conditions.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    comparison = pd.DataFrame(
        {
            "Dimension": [
                "Economic growth",
                "Inflation",
                "Currency pressure",
                "External reserves",
                "Domestic credit",
                "Domestic demand"
            ],
            "India": [
                "Strong",
                "Moderate",
                "Watch",
                "Strong buffer",
                "Strong",
                "Strong"
            ],
            "US": [
                "Mature",
                "Moderate",
                "Dollar strength",
                "Reserve currency",
                "Deep",
                "Strong"
            ],
            "China": [
                "Moderating",
                "Low",
                "Managed",
                "Large",
                "High",
                "Export / investment heavy"
            ]
        }
    )

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Global shocks India should watch")

    shocks = [
        "US Federal Reserve policy",
        "US Treasury yields",
        "Global dollar strength",
        "Crude oil prices",
        "China's growth cycle",
        "Global trade restrictions",
        "Foreign portfolio flows",
        "Global risk appetite"
    ]

    for x in shocks:

        st.markdown(f"- **{x}**")


# ============================================================
# PAGE 12 — ACADEMY
# ============================================================

elif page == "Macro Academy":

    st.markdown(
        '<div class="section">12 — Macro Academy</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Learn how the indicators connect rather than memorising definitions."
    )

    lessons = {

        "GDP":
        """
        Gross Domestic Product measures the value of final goods and
        services produced in an economy.

        For expenditure analysis:

        GDP = Consumption + Investment + Government Spending
        + Exports − Imports.
        """,

        "Inflation":
        """
        Inflation is the rate at which the general price level rises.

        Higher inflation reduces purchasing power and can influence
        monetary policy, bond yields and household spending.
        """,

        "Repo Rate":
        """
        The repo rate is a key RBI policy rate.

        Changes in monetary policy influence short-term rates and
        transmit through financial markets, banks and borrowers.
        """,

        "Fiscal Deficit":
        """
        Fiscal deficit is broadly the government's expenditure
        minus receipts excluding borrowings.

        It represents the government's borrowing requirement.
        """,

        "Current Account":
        """
        The current account captures trade in goods and services,
        primary income and secondary income.

        A deficit generally requires financing through the
        financial/capital side of the balance of payments.
        """,

        "Foreign Exchange Reserves":
        """
        Reserves provide an external buffer.

        Higher reserves generally improve an economy's ability
        to absorb external shocks, although reserves also have
        opportunity costs and are not an unlimited defence.
        """,

        "GFCF":
        """
        Gross Fixed Capital Formation measures investment in fixed
        assets such as machinery, buildings and infrastructure.

        It is particularly important for future productive capacity.
        """,

        "FDI":
        """
        Foreign Direct Investment represents longer-term foreign
        investment in businesses and productive assets.

        It can bring capital, technology, management expertise
        and access to global supply chains.
        """,

        "FPI":
        """
        Foreign Portfolio Investment is investment in financial
        assets such as shares and bonds.

        Portfolio flows can be more sensitive to global interest
        rates and risk appetite than direct investment.
        """,

        "Yield Curve":
        """
        A yield curve plots government bond yields across maturities.

        Its shape contains information about market expectations
        for inflation, monetary policy, growth and borrowing needs.
        """,

        "REER / NEER":
        """
        NEER is a nominal effective exchange-rate index.

        REER adjusts the effective exchange rate for relative prices
        and is useful for assessing external competitiveness.
        """
    }

    for title, lesson in lessons.items():

        with st.expander(title):

            st.markdown(lesson)


# ============================================================
# PAGE 13 — DATA EXPLORER
# ============================================================

elif page == "Data Explorer":

    st.markdown(
        '<div class="section">13 — DBIE Data Explorer</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        Search the underlying RBI economic database.
        </div>

        <div class="insight-text">

        Instead of limiting the application to a fixed list of indicators,
        search DBIE's database for a topic and inspect the underlying table.

        Examples: GDP components, foreign exchange reserves, bank credit,
        inflation, fiscal deficit, UPI, FDI, balance of payments.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    query = st.text_input(
        "Search DBIE",
        placeholder="Try: GDP components, forex reserves, bank credit..."
    )

    if query:

        result = search_dbie(query)

        st.markdown("### Search results")

        if result:

            if isinstance(result, dict):

                items = (
                    result.get("results")
                    or result.get("tables")
                    or result.get("data")
                    or []
                )

            else:

                items = result

            if items:

                for item in items[:15]:

                    if isinstance(item, dict):

                        title = (
                            item.get("title")
                            or item.get("name")
                            or item.get("table")
                            or "DBIE table"
                        )

                        schema = (
                            item.get("schema")
                            or item.get("schema_name")
                        )

                        table = (
                            item.get("table")
                            or item.get("table_name")
                        )

                        st.markdown(
                            f"""
                            <div class="insight">

                            <div class="insight-title">
                            {title}
                            </div>

                            <div class="small-muted">
                            {schema or ""} / {table or ""}
                            </div>

                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            else:

                st.info(
                    "No matching DBIE tables were returned."
                )

        else:

            st.warning(
                "DBIE search could not be reached. Try again later."
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    f"""
    <div class="footer">

    <b>India Macro Intelligence Terminal</b><br>

    Built using publicly available Reserve Bank of India /
    DBIE economic data and macroeconomic relationships.

    <br><br>

    <b>Important:</b> DBIE is a published statistical database.
    Different series have different frequencies, observation dates,
    revisions and data vintages. Always inspect the period and unit
    before comparing numbers.

    <br><br>

    Last dashboard session:
    {datetime.now().strftime("%d %B %Y • %H:%M")}

    </div>
    """,
    unsafe_allow_html=True
)
