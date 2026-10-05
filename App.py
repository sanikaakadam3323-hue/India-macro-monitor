import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="India Macro Intelligence",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

API = "https://data-api.dbie.rbihub.in/api"

# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>

.stApp {
    background:#07111f;
    color:#edf3f8;
}

.block-container {
    max-width:1500px;
    padding-top:2rem;
    padding-bottom:5rem;
}

h1,h2,h3,h4 {
    color:#f5f8fb !important;
}

.hero {
    background:linear-gradient(135deg,#0b1b2d,#102a45);
    border:1px solid #24435e;
    border-radius:20px;
    padding:35px;
    margin-bottom:25px;
}

.hero-title {
    font-size:44px;
    font-weight:800;
    letter-spacing:-1.5px;
}

.hero-sub {
    color:#9eb2c6;
    font-size:16px;
    margin-top:8px;
}

.section {
    font-size:25px;
    font-weight:750;
    margin-top:34px;
    margin-bottom:15px;
}

.card {
    background:#0c1b2b;
    border:1px solid #20394f;
    border-radius:16px;
    padding:21px;
    min-height:135px;
}

.card-label {
    color:#91a7ba;
    font-size:12px;
    text-transform:uppercase;
    letter-spacing:1px;
}

.card-value {
    font-size:30px;
    font-weight:750;
    margin-top:8px;
}

.card-small {
    color:#91a7ba;
    font-size:13px;
    margin-top:7px;
}

.green {
    color:#55dc94;
}

.yellow {
    color:#f4ca59;
}

.red {
    color:#ff7070;
}

.blue {
    color:#66b7ff;
}

.big-score {
    font-size:65px;
    font-weight:850;
    line-height:1;
}

.score-label {
    color:#91a7ba;
    text-transform:uppercase;
    letter-spacing:1px;
    font-size:12px;
}

.insight {
    background:#0c1b2b;
    border:1px solid #20394f;
    border-left:4px solid #4e9bd6;
    border-radius:14px;
    padding:20px 24px;
    margin-bottom:12px;
}

.insight-title {
    font-size:18px;
    font-weight:700;
}

.insight-text {
    color:#b7c6d4;
    line-height:1.65;
    margin-top:7px;
}

.risk {
    background:#0c1b2b;
    border:1px solid #20394f;
    border-radius:15px;
    padding:20px;
    min-height:155px;
}

.pill {
    display:inline-block;
    border-radius:20px;
    padding:5px 11px;
    font-size:11px;
    font-weight:700;
    letter-spacing:.4px;
}

.pill-green {
    background:#123c2a;
    color:#5de39a;
}

.pill-yellow {
    background:#3b3217;
    color:#f6d05d;
}

.pill-red {
    background:#421d24;
    color:#ff7777;
}

.pill-blue {
    background:#12304a;
    color:#72bfff;
}

.flow {
    text-align:center;
    font-size:17px;
    color:#b7c6d4;
    padding:10px;
}

.flow strong {
    color:#f5f8fb;
}

.metric-card {
    background:#0c1b2b;
    border:1px solid #20394f;
    border-radius:14px;
    padding:17px;
}

.metric-name {
    color:#91a7ba;
    font-size:12px;
}

.metric-number {
    font-size:27px;
    font-weight:700;
    margin-top:5px;
}

.footer {
    margin-top:50px;
    border-top:1px solid #20394f;
    padding-top:20px;
    color:#61778c;
    font-size:12px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# API HELPERS
# =========================================================

@st.cache_data(ttl=1800)
def api_get(endpoint, params=None):

    try:

        r = requests.get(
            API + endpoint,
            params=params,
            timeout=20,
            headers={"User-Agent":"India-Macro-Intelligence"}
        )

        r.raise_for_status()

        return r.json()

    except Exception:
        return None


def get_rows(schema, table, limit=100):

    data = api_get(
        f"/tables/{schema}/{table}/rows",
        {
            "limit": limit,
            "labels": 1
        }
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


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🇮🇳 India Macro")

    st.caption("Macroeconomic intelligence terminal")

    page = st.radio(
        "Navigate",
        [
            "Macro Pulse",
            "Growth",
            "Inflation",
            "RBI & Money",
            "Banking & Credit",
            "External Sector",
            "Government",
            "Scenario Lab",
            "Macro Academy"
        ]
    )

    st.divider()

    st.markdown("### Dashboard logic")

    st.caption(
        "The dashboard combines macro indicators into signals, "
        "relationships and scenario analysis."
    )

    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()


# =========================================================
# CORE CURRENT DATA
# =========================================================

# Current values are taken from DBIE's public indicator surface.
# These defaults are used only if an individual API request fails.

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


# =========================================================
# SIGNAL FUNCTIONS
# =========================================================

def signal(value, green_max=None, green_min=None,
           yellow_max=None, yellow_min=None):

    if green_max is not None and value <= green_max:
        return "GREEN"

    if green_min is not None and value >= green_min:
        return "GREEN"

    if yellow_max is not None and value <= yellow_max:
        return "YELLOW"

    if yellow_min is not None and value >= yellow_min:
        return "YELLOW"

    return "RED"


growth_signal = (
    "GREEN" if gdp >= 7
    else "YELLOW" if gdp >= 5
    else "RED"
)

inflation_signal = (
    "GREEN" if cpi < 4
    else "YELLOW" if cpi <= 5
    else "RED"
)

currency_signal = (
    "GREEN" if usd < 90
    else "YELLOW" if usd < 97
    else "RED"
)

credit_signal = (
    "GREEN" if credit >= 15
    else "YELLOW" if credit >= 10
    else "RED"
)

external_signal = (
    "GREEN" if reserves >= 600
    else "YELLOW" if reserves >= 450
    else "RED"
)


# =========================================================
# MACRO SCORE
# =========================================================

score = 50

score += 15 if gdp >= 7 else 7 if gdp >= 5 else -10
score += 12 if cpi < 4 else 4 if cpi <= 5 else -12
score += 10 if credit >= 15 else 5 if credit >= 10 else -8
score += 8 if reserves >= 600 else 4 if reserves >= 450 else -8
score += 5 if import_cover >= 10 else 2 if import_cover >= 7 else -5

score = int(max(0, min(100, score)))

if score >= 75:
    regime = "STRONG"
    regime_css = "green"
elif score >= 60:
    regime = "STABLE"
    regime_css = "green"
elif score >= 45:
    regime = "MIXED"
    regime_css = "yellow"
else:
    regime = "WEAK"
    regime_css = "red"


# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="hero">

<div class="hero-title">
🇮🇳 India Macro Intelligence
</div>

<div class="hero-sub">
A decision-oriented view of India's economy — growth, inflation,
monetary policy, banking, government finances and the external sector.
</div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# MACRO PULSE
# =========================================================

if page == "Macro Pulse":

    st.markdown(
        '<div class="section">The India Macro Pulse</div>',
        unsafe_allow_html=True
    )

    a,b,c,d = st.columns(4)

    with a:
        st.markdown(
            f"""
            <div class="card">
            <div class="score-label">Macro Score</div>
            <div class="big-score">{score}</div>
            <div class="{regime_css}">
            {regime} MACRO REGIME
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with b:
        st.markdown(
            f"""
            <div class="card">
            <div class="card-label">Real GDP Growth</div>
            <div class="card-value">{gdp:.1f}%</div>
            <div class="card-small green">
            Strong domestic growth
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c:
        st.markdown(
            f"""
            <div class="card">
            <div class="card-label">CPI Inflation</div>
            <div class="card-value">{cpi:.2f}%</div>
            <div class="card-small yellow">
            RBI target: 4%
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with d:
        st.markdown(
            f"""
            <div class="card">
            <div class="card-label">USD / INR</div>
            <div class="card-value">₹{usd:.2f}</div>
            <div class="card-small red">
            Currency pressure
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # -----------------------------------------------------
    # THE MACRO STORY
    # -----------------------------------------------------

    st.markdown(
        '<div class="section">🧠 What is happening?</div>',
        unsafe_allow_html=True
    )

    story = f"""
    India's current macro picture is characterised by strong growth
    alongside relatively contained inflation. Real GDP growth is around
    {gdp:.1f}%, while CPI inflation is around {cpi:.2f}%.
    Bank credit is expanding at roughly {credit:.1f}%, suggesting
    continued financial-system support for economic activity.

    The main area to watch is the external side of the economy.
    The rupee is around ₹{usd:.2f} per US dollar, making imported
    energy and other commodities an important transmission channel.
    """

    st.markdown(
        f"""
        <div class="insight">
        <div class="insight-title">
        India's macro story in one paragraph
        </div>

        <div class="insight-text">
        {story}
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # SIGNALS
    # -----------------------------------------------------

    st.markdown(
        '<div class="section">Macro Signal Board</div>',
        unsafe_allow_html=True
    )

    signals = [
        ("Growth", growth_signal,
         "Economic activity and GDP momentum"),
        ("Inflation", inflation_signal,
         "Price pressure relative to the RBI framework"),
        ("Currency", currency_signal,
         "External and imported-inflation pressure"),
        ("Credit", credit_signal,
         "Bank lending and financial conditions"),
        ("Reserves", external_signal,
         "External shock absorption capacity")
    ]

    cols = st.columns(5)

    for i,(name,sig,desc) in enumerate(signals):

        css = (
            "pill-green" if sig == "GREEN"
            else "pill-yellow" if sig == "YELLOW"
            else "pill-red"
        )

        with cols[i]:

            st.markdown(
                f"""
                <div class="risk">

                <div class="card-label">{name}</div>

                <br>

                <span class="pill {css}">
                {sig}
                </span>

                <div class="card-small">
                {desc}
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    # -----------------------------------------------------
    # TRANSMISSION MAP
    # -----------------------------------------------------

    st.markdown(
        '<div class="section">🔗 How the economy connects</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="insight">

        <div class="flow">
        <strong>Inflation</strong>
        →
        <strong>RBI policy</strong>
        →
        <strong>Interest rates</strong>
        →
        <strong>Credit</strong>
        →
        <strong>Consumption & Investment</strong>
        →
        <strong>GDP</strong>
        </div>

        <div class="insight-text">
        This is the key monetary-policy transmission mechanism.
        If inflation becomes persistent, the RBI may have less room
        to reduce rates. Higher borrowing costs can then affect
        household consumption, corporate investment and credit demand.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # INVESTOR LENS
    # -----------------------------------------------------

    st.markdown(
        '<div class="section">💰 Investor Lens</div>',
        unsafe_allow_html=True
    )

    inv = st.columns(5)

    assets = [
        ("Equities",
         "POSITIVE" if gdp >= 7 else "MIXED",
         "Growth supports earnings"),

        ("Bonds",
         "POSITIVE" if cpi <= 4.5 else "CAUTIOUS",
         "Inflation drives rate expectations"),

        ("Banks",
         "POSITIVE" if credit >= 15 else "MIXED",
         "Credit growth remains important"),

        ("INR",
         "PRESSURED" if usd >= 95 else "STABLE",
         "External conditions matter"),

        ("Gold",
         "SUPPORTIVE" if usd >= 95 else "NEUTRAL",
         "Currency and global uncertainty")
    ]

    for i,(asset,status,reason) in enumerate(assets):

        css = (
            "pill-red" if status == "PRESSURED"
            else "pill-yellow" if status in ["MIXED","CAUTIOUS","NEUTRAL"]
            else "pill-green"
        )

        with inv[i]:

            st.markdown(
                f"""
                <div class="card">

                <div class="card-label">{asset}</div>

                <br>

                <span class="pill {css}">
                {status}
                </span>

                <div class="card-small">
                {reason}
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    # -----------------------------------------------------
    # WATCHLIST
    # -----------------------------------------------------

    st.markdown(
        '<div class="section">👁 What to watch next</div>',
        unsafe_allow_html=True
    )

    watches = [
        "CPI and food inflation",
        "RBI policy decisions and liquidity",
        "Quarterly GDP and investment",
        "Crude oil prices",
        "USD/INR and foreign-exchange reserves",
        "Bank credit and deposit growth",
        "Government borrowing and fiscal deficit",
        "FDI/FPI flows and balance of payments"
    ]

    for w in watches:

        st.markdown(
            f"""
            <div class="metric-card">
            👁️ {w}
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# GROWTH
# =========================================================

elif page == "Growth":

    st.markdown(
        '<div class="section">📈 Growth & Economic Activity</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        What actually drives India's GDP?
        </div>

        <div class="insight-text">
        GDP is not just a single growth number. It reflects
        household consumption, government consumption, investment,
        exports and imports. Looking at the components tells us
        whether growth is being driven by consumers, capital formation,
        government spending or external demand.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    g1,g2,g3,g4 = st.columns(4)

    g1.metric("Real GDP Growth", f"{gdp:.1f}%")
    g2.metric("Investment", "Track via GFCF")
    g3.metric("Consumption", "Track via PFCE")
    g4.metric("Exports", "Track external demand")

    st.markdown("### GDP composition")

    st.info(
        "The DBIE GDP-components dataset contains Private Final "
        "Consumption Expenditure, Government Final Consumption "
        "Expenditure, Gross Fixed Capital Formation, exports, imports "
        "and GDP. These are the components to use for a proper growth analysis."
    )

    st.markdown("### Growth interpretation")

    if gdp >= 7:

        st.success(
            f"Growth is currently strong at approximately {gdp:.1f}%. "
            "The next question is whether that growth is broad-based "
            "and supported by consumption and investment."
        )

    else:

        st.warning(
            "Growth is below the level normally associated with "
            "strong economic momentum. Composition becomes particularly important."
        )


# =========================================================
# INFLATION
# =========================================================

elif page == "Inflation":

    st.markdown(
        '<div class="section">🛒 Inflation Intelligence</div>',
        unsafe_allow_html=True
    )

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Headline CPI", f"{cpi:.2f}%")
    c2.metric("RBI Target", "4.00%")
    c3.metric("Repo Rate", f"{repo:.2f}%")
    c4.metric("10Y G-Sec", f"{gsec:.2f}%")

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        Why inflation matters
        </div>

        <div class="insight-text">

        Inflation affects household purchasing power, interest rates,
        bond yields, corporate costs and the RBI's policy decisions.

        A useful distinction is between temporary price shocks and
        persistent inflation. Food and energy shocks can temporarily
        push headline CPI higher, while broader persistent inflation
        can have a larger effect on monetary policy.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    if cpi < 4:

        st.success(
            "Inflation is below the RBI's 4% target, giving monetary "
            "policy comparatively more room."
        )

    elif cpi <= 5:

        st.warning(
            "Inflation is close enough to the target to remain manageable, "
            "but the direction and composition of inflation matter."
        )

    else:

        st.error(
            "Inflation is elevated. Persistent inflation could restrict "
            "the RBI's ability to ease monetary policy."
        )


# =========================================================
# RBI & MONEY
# =========================================================

elif page == "RBI & Money":

    st.markdown(
        '<div class="section">🏦 RBI, Rates & Liquidity</div>',
        unsafe_allow_html=True
    )

    a,b,c,d = st.columns(4)

    a.metric("Repo Rate", f"{repo:.2f}%")
    b.metric("10Y G-Sec", f"{gsec:.2f}%")
    c.metric("CPI", f"{cpi:.2f}%")
    d.metric("Credit Growth", f"{credit:.1f}%")

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        Monetary-policy transmission
        </div>

        <div class="insight-text">

        <b>RBI policy rate</b><br>
        ↓<br>
        Money-market conditions<br>
        ↓<br>
        Bank lending and deposit rates<br>
        ↓<br>
        Credit demand<br>
        ↓<br>
        Consumption + investment<br>
        ↓<br>
        Economic activity

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### How to read the rate environment")

    if cpi < 4 and gdp >= 7:

        st.info(
            "Low inflation combined with strong growth creates an unusual "
            "policy environment: the RBI can focus on balancing price "
            "stability with continued growth."
        )

    elif cpi > 5:

        st.warning(
            "Elevated inflation makes aggressive monetary easing harder."
        )

    else:

        st.info(
            "The policy environment depends on the balance between "
            "inflation risks and growth momentum."
        )


# =========================================================
# BANKING
# =========================================================

elif page == "Banking & Credit":

    st.markdown(
        '<div class="section">🏦 Banking & Credit Conditions</div>',
        unsafe_allow_html=True
    )

    a,b,c = st.columns(3)

    a.metric("Bank Credit Growth", f"{credit:.1f}%")
    b.metric("GDP Growth", f"{gdp:.1f}%")
    c.metric("Repo Rate", f"{repo:.2f}%")

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        Why credit matters
        </div>

        <div class="insight-text">

        Credit is one of the transmission channels between the financial
        system and the real economy. When businesses and households borrow,
        they can increase investment and consumption. However, very rapid
        credit growth can also create financial-stability risks.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    if credit >= 15:

        st.success(
            "Bank credit is expanding strongly. The key question is "
            "whether lending is translating into productive investment "
            "and sustainable economic activity."
        )

    elif credit >= 10:

        st.warning(
            "Credit growth is moderate."
        )

    else:

        st.error(
            "Weak credit growth could indicate softer financial conditions."
        )


# =========================================================
# EXTERNAL SECTOR
# =========================================================

elif page == "External Sector":

    st.markdown(
        '<div class="section">🌎 External Sector</div>',
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
        India's external transmission chain
        </div>

        <div class="insight-text">

        <b>Crude oil rises</b>
        → import bill rises
        → current account pressure
        → rupee pressure
        → imported inflation
        → monetary-policy implications.

        Foreign-exchange reserves provide an important buffer against
        external shocks, while capital flows such as FDI and portfolio
        investment influence the financing side of the balance of payments.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### External resilience")

    if reserves >= 600 and import_cover >= 10:

        st.success(
            "India currently has a substantial external buffer based on "
            "foreign-exchange reserves and import-cover indicators."
        )

    else:

        st.warning(
            "External buffers should be monitored closely."
        )


# =========================================================
# GOVERNMENT
# =========================================================

elif page == "Government":

    st.markdown(
        '<div class="section">🏛️ Government & Fiscal Position</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="insight">

        <div class="insight-title">
        Why fiscal policy matters
        </div>

        <div class="insight-text">

        Government spending affects aggregate demand and can support
        infrastructure and investment. But persistent fiscal deficits
        also mean government borrowing, which can influence bond yields
        and the availability of financial resources.

        The important distinction is between <b>productive capital expenditure</b>
        and expenditure that primarily supports current consumption.

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

    st.info(
        "For a complete fiscal dashboard, connect the DBIE government "
        "tables for fiscal deficit, revenue receipts, expenditure, "
        "capital expenditure, public debt and government borrowing."
    )


# =========================================================
# SCENARIO LAB
# =========================================================

elif page == "Scenario Lab":

    st.markdown(
        '<div class="section">🧪 Macro Scenario Lab</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Change the assumptions below. The model is directional: "
        "it explains transmission channels rather than pretending "
        "to forecast exact future values."
    )

    s1,s2,s3 = st.columns(3)

    with s1:
        oil = st.slider(
            "Crude oil ($/barrel)",
            50,150,85,5
        )

    with s2:
        scenario_rate = st.slider(
            "RBI repo rate (%)",
            3.0,8.0,float(repo),0.25
        )

    with s3:
        scenario_inflation = st.slider(
            "Inflation (%)",
            2.0,10.0,float(cpi),0.25
        )

    st.markdown("### Scenario diagnosis")

    oil_risk = (
        "HIGH" if oil >= 100
        else "MEDIUM" if oil >= 85
        else "LOW"
    )

    rate_condition = (
        "TIGHT" if scenario_rate >= 6
        else "NEUTRAL" if scenario_rate >= 5.5
        else "EASING"
    )

    inflation_condition = (
        "HIGH" if scenario_inflation > 6
        else "WATCH" if scenario_inflation > 4
        else "COMFORTABLE"
    )

    cols = st.columns(3)

    scenarios = [
        (
            "Oil shock",
            oil_risk,
            "Higher crude increases India's import bill and can "
            "create rupee and inflation pressure."
        ),
        (
            "Monetary policy",
            rate_condition,
            "Higher rates generally tighten financial conditions, "
            "while lower rates support credit and demand."
        ),
        (
            "Inflation regime",
            inflation_condition,
            "Higher inflation reduces the RBI's room to ease policy."
        )
    ]

    for i,(title,status,desc) in enumerate(scenarios):

        css = (
            "pill-red" if status in ["HIGH","TIGHT"]
            else "pill-yellow" if status in ["MEDIUM","WATCH","NEUTRAL"]
            else "pill-green"
        )

        with cols[i]:

            st.markdown(
                f"""
                <div class="risk">

                <div class="card-label">{title}</div>

                <br>

                <span class="pill {css}">
                {status}
                </span>

                <div class="card-small">
                {desc}
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("### Transmission map")

    if oil >= 100:

        st.error(
            "Oil shock → higher import bill → rupee pressure → "
            "imported inflation → reduced monetary-policy flexibility."
        )

    if scenario_inflation > 6:

        st.error(
            "High inflation → tighter monetary policy → higher borrowing "
            "costs → weaker demand/investment → growth risk."
        )

    if scenario_rate < 5:

        st.success(
            "Lower policy rate → easier financial conditions → cheaper "
            "credit → potential support to consumption and investment."
        )


# =========================================================
# MACRO ACADEMY
# =========================================================

elif page == "Macro Academy":

    st.markdown(
        '<div class="section">🎓 Macro Academy</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Understand the economy instead of memorising indicators."
    )

    topics = {

        "GDP Growth":
        "Measures the expansion of economic output. Real GDP removes "
        "the effect of changing prices.",

        "CPI Inflation":
        "Measures the rate at which consumer prices change. Persistent "
        "inflation reduces purchasing power and influences monetary policy.",

        "Repo Rate":
        "The RBI's policy rate used as a key instrument for influencing "
        "short-term financial conditions.",

        "10Y Government Bond Yield":
        "A market-based measure of the return investors demand to hold "
        "a 10-year government security. It is influenced by inflation, "
        "policy expectations, government borrowing and global yields.",

        "Bank Credit":
        "Measures the expansion of bank lending. Credit can support "
        "consumption, investment and business activity.",

        "Foreign Exchange Reserves":
        "External assets held by the central bank. They provide a buffer "
        "against external shocks and disorderly currency movements.",

        "Import Cover":
        "Shows approximately how many months of imports could be financed "
        "using foreign-exchange reserves.",

        "Current Account":
        "Captures trade in goods and services plus income and transfers. "
        "A persistent deficit means the economy needs financing from the "
        "capital/financial account.",

        "Fiscal Deficit":
        "The gap between government expenditure and government receipts "
        "excluding borrowings. It represents the government's borrowing requirement.",

        "FDI":
        "Foreign direct investment generally represents longer-term "
        "investment and ownership interests in businesses.",

        "FPI":
        "Foreign portfolio investment flows into financial assets such "
        "as equities and debt and can be more sensitive to global conditions.",

        "GFCF":
        "Gross fixed capital formation is a measure of investment in "
        "fixed assets such as machinery, infrastructure and buildings."
    }

    for title, explanation in topics.items():

        with st.expander(title):

            st.write(explanation)


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    f"""
    <div class="footer">

    <b>India Macro Intelligence</b><br><br>

    Data source: Reserve Bank of India — Database on Indian Economy (DBIE).<br>
    DBIE data has different frequencies and publication dates; always
    interpret an observation together with its period and data vintage.<br><br>

    Dashboard generated: {datetime.now().strftime("%d %B %Y, %H:%M")}

    </div>
    """,
    unsafe_allow_html=True
)
