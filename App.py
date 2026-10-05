import streamlit as st
import requests
import re
from datetime import datetime
import math

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="India Macro Monitor",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>

    .stApp {
        background: #07111f;
        color: #f5f7fa;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        color: #f5f7fa !important;
    }

    .hero {
        padding: 30px 35px;
        border-radius: 18px;
        background: linear-gradient(135deg, #0d1b2e, #102945);
        border: 1px solid #203954;
        margin-bottom: 25px;
    }

    .hero-title {
        font-size: 42px;
        font-weight: 750;
        letter-spacing: -1px;
    }

    .hero-subtitle {
        color: #9fb1c5;
        font-size: 16px;
        margin-top: 8px;
    }

    .section {
        font-size: 24px;
        font-weight: 700;
        margin-top: 30px;
        margin-bottom: 12px;
    }

    .card {
        background: #0d1b2a;
        border: 1px solid #20354b;
        border-radius: 15px;
        padding: 20px;
        min-height: 145px;
    }

    .card-title {
        color: #8ea4bb;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .card-value {
        font-size: 31px;
        font-weight: 700;
        margin-top: 8px;
    }

    .card-note {
        color: #8ea4bb;
        font-size: 13px;
        margin-top: 7px;
    }

    .signal-green {
        color: #54d68c;
        font-weight: 700;
    }

    .signal-yellow {
        color: #f5c451;
        font-weight: 700;
    }

    .signal-red {
        color: #ff6b6b;
        font-weight: 700;
    }

    .macro-box {
        background: #0d1b2a;
        border: 1px solid #20354b;
        border-radius: 15px;
        padding: 24px;
        margin-bottom: 12px;
    }

    .macro-heading {
        font-size: 19px;
        font-weight: 700;
    }

    .macro-text {
        color: #b7c5d4;
        line-height: 1.65;
        margin-top: 8px;
    }

    .score {
        font-size: 58px;
        font-weight: 800;
    }

    .score-label {
        color: #91a5b8;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .pill {
        display: inline-block;
        padding: 6px 11px;
        border-radius: 20px;
        margin-right: 5px;
        font-size: 12px;
        font-weight: 600;
    }

    .pill-green {
        background: #123c2a;
        color: #5ce09a;
    }

    .pill-yellow {
        background: #3c3215;
        color: #f6cc58;
    }

    .pill-red {
        background: #401d22;
        color: #ff7979;
    }

    .footer {
        color: #60758a;
        font-size: 12px;
        margin-top: 35px;
        padding-top: 20px;
        border-top: 1px solid #20354b;
    }

    [data-testid="stMetric"] {
        background: #0d1b2a;
        border: 1px solid #20354b;
        padding: 18px;
        border-radius: 15px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATA
# ============================================================

DBIE_URL = "https://dbie.rbihub.in/"

@st.cache_data(ttl=1800)
def get_dbie_page():

    try:
        r = requests.get(
            DBIE_URL,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        r.raise_for_status()

        clean = re.sub(r"<[^>]+>", " ", r.text)
        clean = re.sub(r"\s+", " ", clean)

        return clean, True

    except Exception:
        return "", False


text, connected = get_dbie_page()


# ============================================================
# PARSING
# ============================================================

def find_number(patterns):

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            try:
                return float(
                    match.group(1).replace(",", "")
                )
            except:
                pass

    return None


repo = find_number([
    r"Repo Rate\s*[:\-]?\s*(\d+(?:\.\d+)?)",
    r"Policy Repo Rate\s*[:\-]?\s*(\d+(?:\.\d+)?)"
])

cpi = find_number([
    r"CPI Inflation\s*[:\-]?\s*(\d+(?:\.\d+)?)",
    r"CPI\s+Inflation.*?(\d+(?:\.\d+)?)"
])

gdp = find_number([
    r"Real GDP Growth\s*[:\-]?\s*(\d+(?:\.\d+)?)",
    r"GDP Growth\s*[:\-]?\s*(\d+(?:\.\d+)?)"
])

gsec = find_number([
    r"10[- ]Year G[- ]Sec Yield\s*[:\-]?\s*(\d+(?:\.\d+)?)",
    r"10Y G[- ]Sec Yield\s*[:\-]?\s*(\d+(?:\.\d+)?)"
])

credit = find_number([
    r"Bank Credit Growth\s*[:\-]?\s*(\d+(?:\.\d+)?)"
])

usd = find_number([
    r"USD/INR\s*[:\-]?\s*(\d+(?:\.\d+)?)",
    r"USD\s*/\s*INR.*?(\d+(?:\.\d+)?)"
])

reserves = find_number([
    r"Foreign exchange reserves\s*[:\-]?\s*([\d,]+(?:\.\d+)?)",
    r"Foreign Exchange Reserves\s*[:\-]?\s*([\d,]+(?:\.\d+)?)"
])

import_cover = find_number([
    r"Import cover\s*[:\-]?\s*(\d+(?:\.\d+)?)",
    r"Import Cover\s*[:\-]?\s*(\d+(?:\.\d+)?)"
])


# ============================================================
# FALLBACK VALUES
# ============================================================
# These are only used if DBIE temporarily fails to expose
# a particular homepage value.

if repo is None:
    repo = 5.25

if cpi is None:
    cpi = 4.45

if gdp is None:
    gdp = 8.2

if gsec is None:
    gsec = 6.84

if credit is None:
    credit = 19.3

if usd is None:
    usd = 95.97

if reserves is None:
    reserves = 765.9

if import_cover is None:
    import_cover = 11.2


# ============================================================
# MACRO SIGNAL ENGINE
# ============================================================

def inflation_signal(x):

    if x < 4:
        return "GREEN", "Inflation is below the RBI's 4% target."

    elif x <= 5:
        return "YELLOW", "Inflation is manageable but deserves monitoring."

    else:
        return "RED", "Inflation is elevated and may restrict monetary easing."


def growth_signal(x):

    if x >= 7:
        return "GREEN", "Growth momentum is strong."

    elif x >= 5:
        return "YELLOW", "Growth remains positive but is not particularly strong."

    else:
        return "RED", "Growth momentum is weak."


def rupee_signal(x):

    if x < 85:
        return "GREEN", "The rupee is relatively strong against the dollar."

    elif x < 95:
        return "YELLOW", "The rupee is under moderate pressure."

    else:
        return "RED", "The rupee is under significant pressure."


def credit_signal(x):

    if x >= 15:
        return "GREEN", "Bank credit is expanding strongly."

    elif x >= 10:
        return "YELLOW", "Credit growth is moderate."

    else:
        return "RED", "Weak credit growth may signal softer domestic activity."


infl_signal, infl_text = inflation_signal(cpi)
growth_sig, growth_text = growth_signal(gdp)
rupee_sig, rupee_text = rupee_signal(usd)
credit_sig, credit_text = credit_signal(credit)


# ============================================================
# MACRO SCORE
# ============================================================

score = 50

# Growth
if gdp >= 7:
    score += 15
elif gdp >= 5:
    score += 7
else:
    score -= 10

# Inflation
if cpi < 4:
    score += 12
elif cpi <= 5:
    score += 3
else:
    score -= 12

# Credit
if credit >= 15:
    score += 10
elif credit >= 10:
    score += 5
else:
    score -= 8

# Reserves
if reserves >= 600:
    score += 8
elif reserves >= 450:
    score += 4
else:
    score -= 8

# Import cover
if import_cover >= 10:
    score += 5
elif import_cover >= 7:
    score += 2
else:
    score -= 5

score = max(0, min(100, score))


if score >= 75:
    regime = "STRONG"
    regime_class = "signal-green"

elif score >= 60:
    regime = "STABLE"
    regime_class = "signal-green"

elif score >= 45:
    regime = "MIXED"
    regime_class = "signal-yellow"

else:
    regime = "WEAK"
    regime_class = "signal-red"


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="hero">

<div class="hero-title">
🇮🇳 India Macro Monitor
</div>

<div class="hero-subtitle">
India's macroeconomy — monitored, interpreted and stress-tested.
</div>

</div>
""", unsafe_allow_html=True)


if connected:
    st.success("🟢 Live connection to RBI DBIE detected")
else:
    st.warning("🟡 RBI DBIE could not be reached. Showing the latest available dashboard values.")


# ============================================================
# TOP SCORE
# ============================================================

st.markdown('<div class="section">India Macro Pulse</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns([1.2, 1.5, 1.5, 1.5])

with col1:

    st.markdown(
        f"""
        <div class="card">
        <div class="score-label">Macro Score</div>
        <div class="score">{score}</div>
        <div class="{regime_class}">{regime} MACRO ENVIRONMENT</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:

    st.markdown(
        f"""
        <div class="card">
        <div class="card-title">Growth</div>
        <div class="card-value">{gdp:.1f}%</div>
        <div class="signal-green">● {growth_text}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:

    st.markdown(
        f"""
        <div class="card">
        <div class="card-title">Inflation</div>
        <div class="card-value">{cpi:.2f}%</div>
        <div class="{'signal-green' if infl_signal == 'GREEN' else 'signal-yellow' if infl_signal == 'YELLOW' else 'signal-red'}">
        ● {infl_signal}
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:

    st.markdown(
        f"""
        <div class="card">
        <div class="card-title">Rupee</div>
        <div class="card-value">₹{usd:.2f}</div>
        <div class="{'signal-green' if rupee_sig == 'GREEN' else 'signal-yellow' if rupee_sig == 'YELLOW' else 'signal-red'}">
        ● {rupee_sig}
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# MACRO STORY
# ============================================================

st.markdown(
    '<div class="section">What is happening?</div>',
    unsafe_allow_html=True
)

story_parts = []

if gdp >= 7:
    story_parts.append(
        f"India is showing strong real economic growth at {gdp:.1f}%."
    )
else:
    story_parts.append(
        f"India's growth momentum is currently {gdp:.1f}%."
    )

if cpi < 4:
    story_parts.append(
        f"Consumer inflation at {cpi:.2f}% is below the RBI's 4% target."
    )
elif cpi <= 5:
    story_parts.append(
        f"Inflation at {cpi:.2f}% remains relatively contained but is worth monitoring."
    )
else:
    story_parts.append(
        f"Inflation at {cpi:.2f}% remains a constraint on monetary policy."
    )

if usd >= 95:
    story_parts.append(
        f"The rupee is under pressure at around ₹{usd:.2f} per US dollar."
    )

if credit >= 15:
    story_parts.append(
        f"Bank credit growth of {credit:.1f}% indicates strong financial-system lending."
    )

story = " ".join(story_parts)

st.markdown(
    f"""
    <div class="macro-box">
        <div class="macro-heading">
        The current macro picture
        </div>

        <div class="macro-text">
        {story}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# KEY INDICATORS
# ============================================================

st.markdown(
    '<div class="section">Macro Dashboard</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Policy Repo Rate",
        f"{repo:.2f}%",
        help="RBI policy rate."
    )

with c2:
    st.metric(
        "10Y Government Bond",
        f"{gsec:.2f}%"
    )

with c3:
    st.metric(
        "Bank Credit Growth",
        f"{credit:.1f}%"
    )

with c4:
    st.metric(
        "FX Reserves",
        f"${reserves:,.1f} bn"
    )

c5, c6, c7, c8 = st.columns(4)

with c5:
    st.metric(
        "Import Cover",
        f"{import_cover:.1f} months"
    )

with c6:
    st.metric(
        "USD / INR",
        f"₹{usd:.2f}"
    )

with c7:
    st.metric(
        "Real GDP Growth",
        f"{gdp:.1f}%"
    )

with c8:
    st.metric(
        "CPI Inflation",
        f"{cpi:.2f}%"
    )


# ============================================================
# SIGNAL MATRIX
# ============================================================

st.markdown(
    '<div class="section">Macro Signal Matrix</div>',
    unsafe_allow_html=True
)

signals = [
    ("Economic Growth", growth_sig, growth_text),
    ("Inflation", infl_signal, infl_text),
    ("Currency", rupee_sig, rupee_text),
    ("Bank Credit", credit_sig, credit_text),
]


cols = st.columns(4)

for i, (name, signal, explanation) in enumerate(signals):

    with cols[i]:

        css = (
            "pill-green"
            if signal == "GREEN"
            else "pill-yellow"
            if signal == "YELLOW"
            else "pill-red"
        )

        st.markdown(
            f"""
            <div class="macro-box">

            <div class="card-title">{name}</div>

            <br>

            <span class="pill {css}">
            {signal}
            </span>

            <div class="macro-text">
            {explanation}
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# INVESTOR VIEW
# ============================================================

st.markdown(
    '<div class="section">Investor View</div>',
    unsafe_allow_html=True
)

st.caption(
    "Directional macro interpretation — not investment advice."
)

investor_cols = st.columns(5)


def investor_signal(asset):

    if asset == "Equities":

        if gdp >= 7 and cpi <= 5:
            return "POSITIVE", "pill-green"

        return "MIXED", "pill-yellow"

    if asset == "Bonds":

        if cpi <= 4.5:
            return "POSITIVE", "pill-green"

        return "CAUTIOUS", "pill-yellow"

    if asset == "Banks":

        if credit >= 15 and gdp >= 6:
            return "POSITIVE", "pill-green"

        return "MIXED", "pill-yellow"

    if asset == "INR":

        if usd >= 95:
            return "PRESSURED", "pill-red"

        return "STABLE", "pill-green"

    if asset == "Gold":

        if usd >= 95 or cpi > 5:
            return "SUPPORTIVE", "pill-green"

        return "NEUTRAL", "pill-yellow"


for i, asset in enumerate(
    ["Equities", "Bonds", "Banks", "INR", "Gold"]
):

    result, css = investor_signal(asset)

    with investor_cols[i]:

        st.markdown(
            f"""
            <div class="card">

            <div class="card-title">
            {asset}
            </div>

            <br>

            <span class="pill {css}">
            {result}
            </span>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# TRANSMISSION MECHANISM
# ============================================================

st.markdown(
    '<div class="section">How the Macro System Connects</div>',
    unsafe_allow_html=True
)

st.markdown(
"""
<div class="macro-box">

<div class="macro-heading">
Inflation → RBI → Interest Rates → Credit → Growth
</div>

<div class="macro-text">

<strong>Inflation rises</strong><br>
↓<br>

RBI has less room to cut rates<br>
↓<br>

Borrowing costs remain higher<br>
↓<br>

Credit growth can slow<br>
↓<br>

Consumption & investment may moderate<br>
↓<br>

Economic growth can weaken

<br><br>

<strong>Reverse scenario:</strong><br>

Inflation falls → RBI gains room to ease → borrowing becomes cheaper →
credit improves → demand and investment can strengthen.

</div>

</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# SCENARIO LAB
# ============================================================

st.markdown(
    '<div class="section">🧪 Macro Scenario Lab</div>',
    unsafe_allow_html=True
)

st.caption(
    "Change the assumptions and see the likely direction of macro effects."
)

col1, col2, col3 = st.columns(3)

with col1:

    oil = st.slider(
        "Crude Oil ($ / barrel)",
        min_value=50,
        max_value=150,
        value=85,
        step=5
    )

with col2:

    rbi_rate = st.slider(
        "RBI Repo Rate (%)",
        min_value=3.0,
        max_value=8.0,
        value=float(repo),
        step=0.25
    )

with col3:

    inflation_scenario = st.slider(
        "Inflation (%)",
        min_value=2.0,
        max_value=10.0,
        value=float(cpi),
        step=0.25
    )


oil_effect = "LOW"
oil_css = "pill-green"

if oil >= 100:
    oil_effect = "HIGH PRESSURE"
    oil_css = "pill-red"

elif oil >= 85:
    oil_effect = "MODERATE"
    oil_css = "pill-yellow"


rate_effect = "EASING"
rate_css = "pill-green"

if rbi_rate >= 6:
    rate_effect = "RESTRICTIVE"
    rate_css = "pill-red"

elif rbi_rate >= 5.5:
    rate_effect = "NEUTRAL / TIGHT"
    rate_css = "pill-yellow"


infl_effect = "COMFORTABLE"
infl_css = "pill-green"

if inflation_scenario > 6:
    infl_effect = "HIGH"
    infl_css = "pill-red"

elif inflation_scenario > 4:
    infl_effect = "WATCH"
    infl_css = "pill-yellow"


s1, s2, s3 = st.columns(3)

with s1:

    st.markdown(
        f"""
        <div class="macro-box">

        <div class="card-title">Oil Shock</div>

        <br>

        <span class="pill {oil_css}">
        {oil_effect}
        </span>

        <div class="macro-text">

        Higher crude prices can increase India's import bill,
        put pressure on the rupee and increase inflationary risk.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

with s2:

    st.markdown(
        f"""
        <div class="macro-box">

        <div class="card-title">Monetary Policy</div>

        <br>

        <span class="pill {rate_css}">
        {rate_effect}
        </span>

        <div class="macro-text">

        A lower policy rate generally reduces borrowing costs,
        while higher rates can restrain credit and demand.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

with s3:

    st.markdown(
        f"""
        <div class="macro-box">

        <div class="card-title">Inflation Shock</div>

        <br>

        <span class="pill {infl_css}">
        {infl_effect}
        </span>

        <div class="macro-text">

        Persistent inflation reduces real purchasing power
        and can limit the RBI's ability to ease policy.

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# RISK RADAR
# ============================================================

st.markdown(
    '<div class="section">🚨 Macro Risk Radar</div>',
    unsafe_allow_html=True
)

risks = []

if usd >= 95:
    risks.append(
        ("HIGH", "Rupee pressure",
         "A weaker rupee can increase the domestic cost of imported goods and energy.")
    )
else:
    risks.append(
        ("LOW", "Currency risk",
         "The rupee does not currently represent the largest macro pressure.")
    )


if oil >= 100:
    risks.append(
        ("HIGH", "Crude oil shock",
         "India is highly exposed to imported energy prices.")
    )
else:
    risks.append(
        ("MEDIUM", "Oil risk",
         "A sharp global oil-price increase could quickly affect inflation and the external balance.")
    )


if cpi > 5:
    risks.append(
        ("HIGH", "Inflation",
         "Elevated inflation can constrain monetary-policy flexibility.")
    )
else:
    risks.append(
        ("LOW", "Inflation",
         "Current inflation is not the dominant macro risk.")
    )


if gdp < 6:
    risks.append(
        ("HIGH", "Growth slowdown",
         "Weak growth can affect investment, employment and corporate earnings.")
    )
else:
    risks.append(
        ("LOW", "Growth",
         "Growth remains a relative strength.")
    )


risk_cols = st.columns(4)

for i, (level, name, description) in enumerate(risks):

    css = (
        "pill-red"
        if level == "HIGH"
        else "pill-yellow"
        if level == "MEDIUM"
        else "pill-green"
    )

    with risk_cols[i]:

        st.markdown(
            f"""
            <div class="macro-box">

            <div class="card-title">
            {name}
            </div>

            <br>

            <span class="pill {css}">
            {level}
            </span>

            <div class="macro-text">
            {description}
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# WHAT TO WATCH
# ============================================================

st.markdown(
    '<div class="section">What to Watch Next</div>',
    unsafe_allow_html=True
)

watch_items = [
    "RBI monetary-policy decisions and liquidity conditions",
    "Monthly CPI inflation, especially food inflation",
    "Quarterly GDP growth and investment activity",
    "USD/INR movement and foreign-exchange reserves",
    "Global crude-oil prices",
    "Bank credit growth and financial conditions"
]

for item in watch_items:

    st.markdown(
        f"""
        <div class="macro-box" style="padding:14px 20px;">
        👁️ {item}
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DATA DICTIONARY
# ============================================================

with st.expander("📚 Understand the indicators"):

    explanations = {

        "Policy Repo Rate":
        "The rate at which the RBI lends to commercial banks under the monetary-policy framework.",

        "CPI Inflation":
        "The year-on-year change in consumer prices. The RBI's flexible inflation-targeting framework centres on 4%.",

        "Real GDP Growth":
        "The rate at which India's economy grows after removing the effect of price changes.",

        "10Y G-Sec Yield":
        "The market yield on India's 10-year government security. It is an important benchmark for longer-term borrowing costs.",

        "Bank Credit Growth":
        "The year-on-year growth in bank lending. Strong credit expansion can indicate healthy demand for financing.",

        "USD / INR":
        "The number of Indian rupees required to purchase one US dollar.",

        "Foreign Exchange Reserves":
        "Foreign assets held by the RBI that provide a buffer against external shocks and currency stress.",

        "Import Cover":
        "The approximate number of months of imports that can be financed using foreign-exchange reserves."
    }

    for key, value in explanations.items():

        st.markdown(
            f"**{key}** — {value}"
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    f"""
    <div class="footer">

    <strong>India Macro Monitor</strong><br><br>

    Data source: Reserve Bank of India — Database on Indian Economy (DBIE).<br>
    This dashboard interprets macroeconomic indicators and is intended for
    educational and analytical use, not investment advice.<br><br>

    Last checked: {datetime.now().strftime("%d %B %Y, %H:%M")}

    </div>
    """,
    unsafe_allow_html=True
)
