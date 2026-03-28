import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="CreditWorthy",
    page_icon="🌱",
    layout="wide"
)

# ─── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8faf8; }
    .score-big { font-size: 72px; font-weight: 700; text-align: center; line-height: 1; }
    .score-label { font-size: 18px; text-align: center; margin-top: 4px; }
    .loan-card {
        background: #f0faf5;
        border-radius: 10px;
        padding: 16px 20px;
        border: 1px solid #1D9E75;
        margin-bottom: 12px;
    }
    .loan-amount  { font-size: 24px; font-weight: 700; color: #1D9E75; }
    .header-logo  { font-size: 28px; font-weight: 800; color: #1D9E75; }
    .credit-box   { border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; }
    .credit-amount{ font-size: 36px; font-weight: 700; }
    .section-tag  {
        display: inline-block;
        font-size: 11px; font-weight: 700; letter-spacing: 1px;
        padding: 3px 10px; border-radius: 20px; margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ─── CROP CLASSIFICATION ───────────────────────────────────────────────────────
CASH_CROPS = [
    "Vanilla", "Cloves", "Coffee", "Cocoa", "Pepper",
    "Cashew Nuts", "Cotton", "Sisal", "Sugarcane",
    "Lychees", "Tropical Fruits", "Pineapple", "Avocado",
    "Livestock", "Dairy Farming",
]

FOOD_CROPS = [
    "Rice", "Maize", "Cassava", "Potatoes", "Sweet Potato",
    "Tomatoes", "Vegetables", "Cowpeas", "Other",
]

ALL_CASH_CROPS = sorted(CASH_CROPS)
ALL_FOOD_CROPS = sorted(FOOD_CROPS)


# ─── REGIONS ───────────────────────────────────────────────────────────────────
REGIONS = {
    "SAVA":             {"specialties": ["Vanilla", "Cloves", "Coffee"],              "climate": "tropical_humid"},
    "Diana":            {"specialties": ["Cocoa", "Sugarcane", "Pepper"],             "climate": "tropical_dry"},
    "Analanjirofo":     {"specialties": ["Cloves", "Lychees"],                        "climate": "equatorial"},
    "Atsinanana":       {"specialties": ["Coffee", "Tropical Fruits"],                "climate": "tropical_humid"},
    "Vakinankaratra":   {"specialties": ["Potatoes", "Dairy Farming", "Maize"],       "climate": "temperate"},
    "Analamanga":       {"specialties": ["Vegetables", "Rice"],                       "climate": "temperate"},
    "Itasy":            {"specialties": ["Pineapple", "Avocado", "Tomatoes", "Rice"], "climate": "temperate"},
    "Alaotra-Mangoro":  {"specialties": ["Rice"],                                     "climate": "tropical_altitude"},
    "Boeny":            {"specialties": ["Rice", "Cashew Nuts"],                      "climate": "tropical_dry"},
    "Menabe":           {"specialties": ["Sugarcane", "Maize", "Cowpeas"],            "climate": "tropical_dry"},
    "Atsimo-Andrefana": {"specialties": ["Maize", "Cotton", "Cassava"],               "climate": "semi_arid"},
    "Androy":           {"specialties": ["Livestock", "Sisal", "Cassava"],            "climate": "arid"},
    "Anosy":            {"specialties": ["Livestock", "Sisal", "Cassava"],            "climate": "arid"},
}

CLIMATE_COMPATIBILITY = {
    "tropical_humid":    ["Coffee", "Cocoa", "Cloves", "Tropical Fruits", "Rice", "Vegetables", "Lychees"],
    "tropical_dry":      ["Maize", "Cassava", "Cashew Nuts", "Cowpeas", "Rice", "Cotton"],
    "equatorial":        ["Cloves", "Lychees", "Tropical Fruits", "Cocoa", "Vanilla", "Coffee"],
    "temperate":         ["Rice", "Vegetables", "Maize", "Potatoes", "Tomatoes", "Pineapple", "Avocado", "Cowpeas"],
    "tropical_altitude": ["Rice", "Maize", "Vegetables", "Potatoes"],
    "semi_arid":         ["Maize", "Cassava", "Cotton", "Livestock", "Cowpeas"],
    "arid":              ["Cassava", "Livestock", "Sisal"],
}

CROP_PRICES_AR = {
    "Rice": 1200, "Maize": 800, "Cassava": 400, "Vegetables": 1500,
    "Sweet Potato": 600, "Potatoes": 1000, "Tomatoes": 1200,
    "Cowpeas": 1000, "Other": 800,
    "Coffee": 8000, "Vanilla": 150000, "Cloves": 12000, "Cocoa": 5000,
    "Lychees": 2000, "Tropical Fruits": 1800,
    "Cashew Nuts": 6000, "Sugarcane": 300,
    "Pineapple": 1800, "Avocado": 2000,
    "Cotton": 2500, "Sisal": 900, "Pepper": 20000,
    "Livestock": 0, "Dairy Farming": 0,
}

# Cash crop — strong regional impact (repayment depends on harvest success)
CASH_REGION_MULTIPLIER = {
    "specialty":  1.00,
    "compatible": 0.75,
    "unsuited":   0.40,
}

# Food crop — light regional impact (food security role only)
FOOD_REGION_MULTIPLIER = {
    "specialty":  1.00,
    "compatible": 1.00,
    "unsuited":   0.80,
}


# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "farmers" not in st.session_state:
    st.session_state["farmers"] = [
        {
            "name": "Rakoto Jean-Pierre", "region": "Alaotra-Mangoro",
            "cash_crop": "Coffee",  "cash_area": 0.3, "cash_yield": 0.4,
            "food_crop": "Rice",    "food_area": 1.0, "food_yield": 2.5, "food_self_consumed": 70,
            "other_revenue": 0,
            "financial_access": "Mobile Money", "cooperative": True,
            "score": None, "segment": None, "loan": None,
        },
        {
            "name": "Rasoamanarivo Aina", "region": "Vakinankaratra",
            "cash_crop": "None",    "cash_area": 0.0, "cash_yield": 0.0,
            "food_crop": "Maize",   "food_area": 1.1, "food_yield": 1.3, "food_self_consumed": 80,
            "other_revenue": 0,
            "financial_access": "Mobile Money", "cooperative": False,
            "score": None, "segment": None, "loan": None,
        },
        {
            "name": "Randria Miora", "region": "Androy",
            "cash_crop": "Sisal",   "cash_area": 0.4, "cash_yield": 0.6,
            "food_crop": "Cassava", "food_area": 0.6, "food_yield": 7.0, "food_self_consumed": 90,
            "other_revenue": 0,
            "financial_access": "None", "cooperative": False,
            "score": None, "segment": None, "loan": None,
        },
    ]
if "current_farmer" not in st.session_state:
    st.session_state["current_farmer"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Registration"


# ─── HELPERS ───────────────────────────────────────────────────────────────────
def get_region_fit(region, crop):
    if region not in REGIONS or not crop or crop == "None":
        return "compatible"
    if crop in REGIONS[region]["specialties"]:
        return "specialty"
    climate = REGIONS[region]["climate"]
    if crop in CLIMATE_COMPATIBILITY.get(climate, []):
        return "compatible"
    return "unsuited"

FIT_LABEL = {
    "specialty":  "✅ Regional specialty",
    "compatible": "⚠️ Climate-compatible",
    "unsuited":   "❌ Poorly adapted",
}


# ─── SCORING ───────────────────────────────────────────────────────────────────
def calculate_score(
    cash_crop, cash_area, cash_yield,
    food_crop, food_area, food_yield, food_self_consumed,
    other_revenue, financial_access, cooperative, region
):
    """
    Scoring — 100 pts total
      Cash crop production     25 pts  (harvest value, calibrated for Madagascar)
      Cash crop region fit     20 pts  (strong: repayment depends on harvest success)
      Food security            10 pts  (self-consumed production volume)
      Food crop region fit      5 pts  (light: food role only)
      Financial Access         20 pts  (repayment channel & traceability)
      Cooperative Membership   10 pts  (collective guarantee)
      Other Revenues (opt.)    10 pts  (non-verifiable bonus)
    """
    score   = 0
    details = {}

    has_cash = cash_crop and cash_crop != "None" and cash_area > 0
    has_food = food_crop and food_crop != "None" and food_area > 0

    # 1 — Cash crop production (25 pts) — value-based, calibrated to Madagascar
    if has_cash:
        price      = CROP_PRICES_AR.get(cash_crop, 1000)
        cash_value = cash_area * cash_yield * 1000 * price
        if cash_value > 5_000_000:   p1 = 25
        elif cash_value > 1_000_000: p1 = 18
        elif cash_value > 300_000:   p1 = 10
        elif cash_value > 50_000:    p1 = 4
        else:                        p1 = 0
    else:
        p1 = 0
    score += p1
    details["Cash Crop Production (harvest value)"] = (p1, 25)

    # 2 — Cash crop region fit (20 pts)
    if has_cash:
        fit_cash = get_region_fit(region, cash_crop)
        if fit_cash == "specialty":    p2, fl = 20, FIT_LABEL["specialty"]
        elif fit_cash == "compatible": p2, fl = 13, FIT_LABEL["compatible"]
        else:                          p2, fl = 3,  FIT_LABEL["unsuited"]
    else:
        fit_cash, fl, p2 = "compatible", "—", 0
    score += p2
    details[f"Cash Crop Region Fit ({fl})"] = (p2, 20)

    # 3 — Food security (10 pts)
    if has_food:
        food_consumed = food_area * food_yield * (food_self_consumed / 100)
        if food_consumed > 3:     p3 = 10
        elif food_consumed > 1:   p3 = 7
        elif food_consumed > 0.3: p3 = 4
        else:                     p3 = 1
    else:
        p3 = 0
    score += p3
    details["Food Security (self-consumed production)"] = (p3, 10)

    # 4 — Food crop region fit (5 pts) — 2 levels only
    if has_food:
        fit_food = get_region_fit(region, food_crop)
        if fit_food in ("specialty", "compatible"): p4, fl4 = 5, FIT_LABEL.get(fit_food, "")
        else:                                       p4, fl4 = 1, FIT_LABEL["unsuited"]
    else:
        fit_food, fl4, p4 = "compatible", "—", 0
    score += p4
    details[f"Food Crop Region Fit ({fl4})"] = (p4, 5)

    # 5 — Financial Access (20 pts)
    if financial_access == "Bank Account":   p5 = 20
    elif financial_access == "Mobile Money": p5 = 12
    else:                                    p5 = 0
    score += p5
    details["Financial Access (bank / mobile)"] = (p5, 20)

    # 6 — Cooperative Membership (10 pts)
    p6 = 10 if cooperative else 0
    score += p6
    details["Cooperative Membership"] = (p6, 10)

    # 7 — Other Revenues (10 pts, optional)
    if other_revenue and other_revenue > 0:
        if other_revenue > 3_000_000:   p7 = 10
        elif other_revenue > 1_000_000: p7 = 7
        elif other_revenue > 300_000:   p7 = 4
        else:                           p7 = 1
    else:
        p7 = 0
    score += p7
    details["Other Revenues (optional bonus)"] = (p7, 10)

    extra = {"fit_cash": fit_cash, "fit_food": fit_food}
    return score, details, extra


def get_segment(score):
    if score >= 70:
        return "A — Eligible",               "#1D9E75", "#e0f7ee"
    elif score >= 45:
        return "B — Conditionally Eligible",  "#d4830a", "#fff3dc"
    else:
        return "C — Not Eligible",            "#c0392b", "#fdecea"


# ─── LOAN ESTIMATION ───────────────────────────────────────────────────────────
def estimate_loan(
    cash_crop, cash_area, cash_yield,
    food_crop, food_area, food_yield, food_self_consumed,
    other_revenue, financial_access, cooperative,
    segment_label, fit_cash, fit_food
):
    """
    Base = cash_component + food_component + other_component

    Cash:  (harvest value / 4) × cash_region_multiplier
    Food:  (harvest value × %sold / 4) × food_region_multiplier
         + (harvest value × %auto × 40% / 4)   ← indirect food savings
    Other: other_revenue × 20%
    """
    if "C" in segment_label:
        return None

    has_cash = cash_crop and cash_crop != "None" and cash_area > 0
    has_food = food_crop and food_crop != "None" and food_area > 0

    # Cash component
    cash_harvest_value = 0
    cash_component     = 0
    cash_mult          = 1.0
    if has_cash:
        price_cash         = CROP_PRICES_AR.get(cash_crop, 1000)
        cash_harvest_value = cash_area * cash_yield * 1000 * price_cash
        cash_mult          = CASH_REGION_MULTIPLIER[fit_cash]
        cash_component     = (cash_harvest_value / 4) * cash_mult

    # Food component
    food_harvest_value = 0
    food_sold_comp     = 0
    food_auto_comp     = 0
    food_mult          = 1.0
    if has_food:
        price_food         = CROP_PRICES_AR.get(food_crop, 800)
        food_harvest_value = food_area * food_yield * 1000 * price_food
        pct_sold           = (100 - food_self_consumed) / 100
        pct_auto           = food_self_consumed / 100
        food_mult          = FOOD_REGION_MULTIPLIER[fit_food]
        food_sold_comp     = (food_harvest_value * pct_sold / 4) * food_mult
        food_auto_comp     = (food_harvest_value * pct_auto * 0.40 / 4)

    food_component = food_sold_comp + food_auto_comp

    # Other revenues
    other_component = (other_revenue * 0.20) if (other_revenue and other_revenue > 0) else 0

    base = cash_component + food_component + other_component

    # Segment multiplier
    if "A" in segment_label:
        multiplier = 1.0
        rate       = "14%"
        duration   = "Up to 36 months"
        repayment  = "Flexible (end of harvest)"
    else:
        multiplier = 0.60
        rate       = "20%"
        duration   = "Up to 12 months"
        repayment  = "Monthly installments"

    amount = base * multiplier

    bonus           = 0
    bonus_breakdown = []
    if financial_access == "Bank Account":
        b = amount * 0.10; bonus += b
        bonus_breakdown.append(("Bank account bonus (+10%)", b))
    elif financial_access == "Mobile Money":
        b = amount * 0.05; bonus += b
        bonus_breakdown.append(("Mobile money bonus (+5%)", b))
    if cooperative:
        b = amount * 0.10; bonus += b
        bonus_breakdown.append(("Cooperative guarantee bonus (+10%)", b))

    final_amount = amount + bonus

    return {
        "cash_harvest_value":   cash_harvest_value,
        "cash_mult":            cash_mult,
        "cash_component":       cash_component,
        "fit_cash":             fit_cash,
        "food_harvest_value":   food_harvest_value,
        "food_mult":            food_mult,
        "food_sold_comp":       food_sold_comp,
        "food_auto_comp":       food_auto_comp,
        "food_component":       food_component,
        "fit_food":             fit_food,
        "other_component":      other_component,
        "base_amount":          base,
        "segment_multiplier":   multiplier,
        "amount_after_segment": amount,
        "bonus_breakdown":      bonus_breakdown,
        "total_bonus":          bonus,
        "final_amount":         final_amount,
        "rate":                 rate,
        "duration":             duration,
        "repayment":            repayment,
    }


def get_loan_offers(segment_label, final_amount):
    amt = int(final_amount)
    if "A" in segment_label:
        return [
            {"institution": "CECAM",         "product": "Input Credit",
             "amount": f"{amt:,} Ar",               "duration": "12 months", "rate": "14%", "repayment": "End of harvest"},
            {"institution": "BOA Madagascar", "product": "Equipment Loan",
             "amount": f"{min(amt*3,5000000):,} Ar", "duration": "36 months", "rate": "18%", "repayment": "Monthly"},
            {"institution": "MicroCred",      "product": "Working Capital",
             "amount": f"{int(amt*0.6):,} Ar",      "duration": "6 months",  "rate": "22%", "repayment": "Mobile money"},
        ]
    elif "B" in segment_label:
        return [
            {"institution": "MicroCred", "product": "Agricultural Micro-loan",
             "amount": f"{amt:,} Ar", "duration": "6 months", "rate": "24%", "repayment": "Monthly installments"},
        ]
    return []


def compute_farmer(f):
    if f.get("score") is None:
        score, details, extra = calculate_score(
            f.get("cash_crop", "None"), f.get("cash_area", 0), f.get("cash_yield", 0),
            f.get("food_crop", "None"), f.get("food_area", 0), f.get("food_yield", 0),
            f.get("food_self_consumed", 70),
            f.get("other_revenue", 0),
            f["financial_access"], f["cooperative"], f["region"]
        )
        f["score"]   = score
        f["details"] = details
        f["extra"]   = extra
        seg_label, _, _ = get_segment(score)
        f["segment"] = seg_label[0]
        f["loan"]    = estimate_loan(
            f.get("cash_crop", "None"), f.get("cash_area", 0), f.get("cash_yield", 0),
            f.get("food_crop", "None"), f.get("food_area", 0), f.get("food_yield", 0),
            f.get("food_self_consumed", 70),
            f.get("other_revenue", 0),
            f["financial_access"], f["cooperative"],
            seg_label, extra["fit_cash"], extra["fit_food"]
        )
    return f


# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="header-logo">🌱 CreditWorthy</div>', unsafe_allow_html=True)
    st.caption("Agricultural Credit Platform · Madagascar")
    st.divider()
    page = st.radio(
        "Navigation",
        ["Registration", "Credit Score", "Lender Portal"],
        index=["Registration", "Credit Score", "Lender Portal"].index(st.session_state["page"])
    )
    st.session_state["page"] = page
    st.divider()
    st.caption(f"👥 {len(st.session_state['farmers'])} farmers registered")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — REGISTRATION
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["page"] == "Registration":
    st.title("Farmer Registration")
    st.caption("Fill in the form to generate a credit score and estimated loan amount")

    with st.form("registration_form"):

        st.subheader("👤 Identity")
        col1, col2 = st.columns(2)
        with col1:
            name   = st.text_input("Full Name *", placeholder="e.g. Rakoto Jean-Pierre")
        with col2:
            region = st.selectbox("Region", list(REGIONS.keys()))

        st.divider()

        # Cash crop
        st.markdown(
            "<span class='section-tag' style='background:#e0f7ee;color:#1D9E75;'>"
            "💰 CASH CROP — main income source</span>", unsafe_allow_html=True
        )
        st.caption("The crop you sell on the market. Leave area at 0 if you have no cash crop.")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            cash_crop  = st.selectbox("Cash Crop", ["None"] + ALL_CASH_CROPS)
        with col_c2:
            cash_area  = st.number_input("Area (ha)", min_value=0.0, max_value=50.0, value=0.3, step=0.05, key="ca")
        with col_c3:
            cash_yield = st.number_input("Yield (t/ha)", min_value=0.0, max_value=20.0, value=0.25, step=0.05, key="cy")

        st.divider()

        # Food crop
        st.markdown(
            "<span class='section-tag' style='background:#fff3dc;color:#d4830a;'>"
            "🍚 FOOD CROP — subsistence / food security (optional)</span>", unsafe_allow_html=True
        )
        st.caption("The crop your family eats. Reduces your default risk and improves your score.")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            food_crop  = st.selectbox("Food Crop", ["None"] + ALL_FOOD_CROPS)
        with col_f2:
            food_area  = st.number_input("Area (ha)", min_value=0.0, max_value=50.0, value=1.0, step=0.05, key="fa")
        with col_f3:
            food_yield = st.number_input("Yield (t/ha)", min_value=0.0, max_value=20.0, value=2.5, step=0.1, key="fy")
        with col_f4:
            food_self_consumed = st.slider("Self-consumed (%)", min_value=0, max_value=100, value=70, step=5)

        st.divider()

        st.subheader("🏦 Financial Profile")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            financial_access = st.selectbox("Financial Access", ["Mobile Money", "Bank Account", "None"])
        with col_p2:
            cooperative = st.checkbox("Member of an agricultural cooperative")
        with col_p3:
            other_revenue = st.number_input(
                "Other Annual Revenues (Ar) — optional",
                min_value=0, max_value=50_000_000, value=0, step=100_000
            )

        submitted = st.form_submit_button(
            "🔍 Calculate Score & Loan Estimate",
            use_container_width=True, type="primary"
        )

    if submitted:
        if not name:
            st.error("Please enter a name.")
        elif (not cash_crop or cash_crop == "None") and (not food_crop or food_crop == "None"):
            st.error("Please enter at least one crop (cash or food).")
        else:
            score, details, extra = calculate_score(
                cash_crop, cash_area, cash_yield,
                food_crop, food_area, food_yield, food_self_consumed,
                other_revenue, financial_access, cooperative, region
            )
            segment_label, color, bg = get_segment(score)
            loan = estimate_loan(
                cash_crop, cash_area, cash_yield,
                food_crop, food_area, food_yield, food_self_consumed,
                other_revenue, financial_access, cooperative,
                segment_label, extra["fit_cash"], extra["fit_food"]
            )
            farmer = {
                "name": name, "region": region,
                "cash_crop": cash_crop, "cash_area": cash_area, "cash_yield": cash_yield,
                "food_crop": food_crop, "food_area": food_area, "food_yield": food_yield,
                "food_self_consumed": food_self_consumed,
                "other_revenue": other_revenue,
                "financial_access": financial_access, "cooperative": cooperative,
                "score": score, "segment": segment_label[0],
                "details": details, "extra": extra, "loan": loan,
            }
            if name not in [f["name"] for f in st.session_state["farmers"]]:
                st.session_state["farmers"].append(farmer)
            st.session_state["current_farmer"] = farmer
            st.success(f"✅ Profile created! Score: {score}/100 — {segment_label}")
            st.session_state["page"] = "Credit Score"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — CREDIT SCORE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state["page"] == "Credit Score":
    st.title("Credit Score")

    farmer = st.session_state.get("current_farmer")

    if farmer is None:
        st.info("No active profile. Select a farmer below or register a new one.")
        names  = [f["name"] for f in st.session_state["farmers"]]
        choice = st.selectbox("Select a farmer", names)
        if st.button("View Score"):
            farmer = next(f for f in st.session_state["farmers"] if f["name"] == choice)
            farmer = compute_farmer(farmer)
            st.session_state["current_farmer"] = farmer
            st.rerun()
    else:
        farmer        = compute_farmer(farmer)
        score         = farmer["score"]
        segment_label, color, bg = get_segment(score)
        details       = farmer.get("details", {})
        loan          = farmer.get("loan")
        extra         = farmer.get("extra", {})
        offers        = get_loan_offers(segment_label, loan["final_amount"]) if loan else []

        col_info, col_score = st.columns([2, 1])
        with col_info:
            st.markdown(f"### 👤 {farmer['name']}")
            st.caption(f"📍 {farmer['region']} · {farmer['financial_access']}")
            if farmer.get("cash_crop") and farmer["cash_crop"] != "None":
                st.caption(f"💰 Cash: {farmer['cash_crop']} — {farmer['cash_area']} ha @ {farmer['cash_yield']} t/ha")
            if farmer.get("food_crop") and farmer["food_crop"] != "None":
                st.caption(
                    f"🍚 Food: {farmer['food_crop']} — {farmer['food_area']} ha @ {farmer['food_yield']} t/ha "
                    f"({farmer['food_self_consumed']}% self-consumed)"
                )
        with col_score:
            st.markdown(f"<div class='score-big' style='color:{color}'>{score}</div>", unsafe_allow_html=True)
            st.markdown("<div class='score-label'>points out of 100</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='text-align:center;margin-top:8px;'>"
                f"<span style='background:{bg};color:{color};padding:6px 18px;border-radius:20px;"
                f"font-weight:600;font-size:15px;'>Segment {segment_label}</span></div>",
                unsafe_allow_html=True
            )

        st.divider()
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Score Breakdown")
            for criterion, (pts, max_pts) in details.items():
                st.markdown(f"**{criterion}** — {pts}/{max_pts} pts")
                st.progress(pts / max_pts if max_pts > 0 else 0)

            st.subheader("Score Gauge")
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=score,
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar":  {"color": color},
                    "steps": [
                        {"range": [0,  44],  "color": "#fdecea"},
                        {"range": [45, 69],  "color": "#fff3dc"},
                        {"range": [70, 100], "color": "#e0f7ee"},
                    ],
                },
                number={"suffix": "/100", "font": {"size": 32}}
            ))
            fig.update_layout(height=250, margin=dict(t=20, b=10, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("Estimated Loan Amount")
            if loan:
                st.markdown(f"""
                <div class='credit-box' style='background:{bg};'>
                    <div style='font-size:13px;color:{color};font-weight:600;margin-bottom:8px;'>
                        Estimated Loan · Segment {segment_label}
                    </div>
                    <div class='credit-amount' style='color:{color};'>
                        {int(loan['final_amount']):,} Ar
                    </div>
                    <div style='font-size:12px;color:#555;margin-top:6px;'>
                        📅 {loan['duration']} &nbsp;·&nbsp; 📊 Rate {loan['rate']} &nbsp;·&nbsp; 💳 {loan['repayment']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("📊 See calculation details"):
                    st.markdown("**Step 1 — Cash crop component (main repayment source):**")
                    if loan["cash_harvest_value"] > 0:
                        st.markdown(
                            f"- {farmer['cash_crop']} harvest = **{int(loan['cash_harvest_value']):,} Ar** "
                            f"→ ÷4 = **{int(loan['cash_harvest_value']/4):,} Ar**"
                        )
                        st.markdown(
                            f"- Region multiplier ({FIT_LABEL[loan['fit_cash']]}, ×{loan['cash_mult']}) "
                            f"→ **{int(loan['cash_component']):,} Ar**"
                        )
                    else:
                        st.markdown("- No cash crop → 0 Ar")

                    if loan["food_harvest_value"] > 0:
                        pct_sold = 100 - farmer["food_self_consumed"]
                        st.divider()
                        st.markdown("**Step 2 — Food crop component:**")
                        st.markdown(f"- {farmer['food_crop']} harvest = **{int(loan['food_harvest_value']):,} Ar**")
                        st.markdown(
                            f"- Sold ({pct_sold}%) → ÷4 × {loan['food_mult']} = **{int(loan['food_sold_comp']):,} Ar**"
                        )
                        st.markdown(
                            f"- Self-consumed ({farmer['food_self_consumed']}%) × 40% savings → ÷4 = **{int(loan['food_auto_comp']):,} Ar**"
                        )
                        st.markdown(f"- Food total → **{int(loan['food_component']):,} Ar**")

                    if loan["other_component"] > 0:
                        st.divider()
                        st.markdown("**Step 3 — Other revenues (20%):**")
                        st.markdown(f"- **+{int(loan['other_component']):,} Ar**")

                    st.divider()
                    st.markdown(f"**Base (cash + food + other) → {int(loan['base_amount']):,} Ar**")
                    st.divider()
                    st.markdown(f"**Step 4 — Segment multiplier ({int(loan['segment_multiplier']*100)}%):**")
                    st.markdown(f"- → **{int(loan['amount_after_segment']):,} Ar**")

                    if loan["bonus_breakdown"]:
                        st.divider()
                        st.markdown("**Step 5 — Bonuses:**")
                        for label, val in loan["bonus_breakdown"]:
                            st.markdown(f"- {label}: **+{int(val):,} Ar**")

                    st.divider()
                    st.markdown(f"**Final estimated loan: {int(loan['final_amount']):,} Ar**")
                    st.caption("⚠️ Indicative only. Final credit decision belongs to the lender.")

                st.subheader("Available Loan Offers")
                for offer in offers:
                    st.markdown(f"""
                    <div class='loan-card'>
                        <div style='font-size:13px;color:#555;font-weight:600;'>{offer['institution']} · {offer['product']}</div>
                        <div class='loan-amount'>{offer['amount']}</div>
                        <div style='font-size:13px;color:#444;margin-top:6px;'>
                            📅 {offer['duration']} &nbsp;·&nbsp; 📊 {offer['rate']} &nbsp;·&nbsp; 💳 {offer['repayment']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.error("❌ This farmer is not eligible for formal credit.")
                st.info("""
                **Recommendations to improve the score:**
                - Add a cash crop suited to your region (+up to 45 pts combined)
                - Increase food crop production for better food security (+up to 10 pts)
                - Open a mobile money account (+12 pts) or bank account (+20 pts)
                - Join an agricultural cooperative (+10 pts)
                """)

        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("➕ Register a new farmer", use_container_width=True):
                st.session_state["current_farmer"] = None
                st.session_state["page"] = "Registration"
                st.rerun()
        with col_b:
            if st.button("🏦 Go to Lender Portal", use_container_width=True):
                st.session_state["page"] = "Lender Portal"
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — LENDER PORTAL
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state["page"] == "Lender Portal":
    st.title("Lender Portal")
    st.caption("Overview of scored and pre-qualified farmers")

    farmers = [compute_farmer(f) for f in st.session_state["farmers"]]

    col1, col2, col3, col4 = st.columns(4)
    seg_a = len([f for f in farmers if f.get("segment") == "A"])
    seg_b = len([f for f in farmers if f.get("segment") == "B"])
    seg_c = len([f for f in farmers if f.get("segment") == "C"])
    col1.metric("Total Registered", len(farmers))
    col2.metric("Segment A — Eligible", seg_a)
    col3.metric("Segment B — Conditional", seg_b)
    col4.metric("Segment C — Not Eligible", seg_c)

    st.divider()

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_segment = st.multiselect("Filter by Segment", ["A", "B", "C"], default=["A", "B", "C"])
    with col_f2:
        available_regions = list(set(f["region"] for f in farmers))
        filter_region = st.multiselect("Filter by Region", available_regions, default=available_regions)

    filtered = [
        f for f in farmers
        if f.get("segment", "C") in filter_segment and f["region"] in filter_region
    ]

    def seg_badge(seg):
        return {"A": "🟢 A", "B": "🟡 B", "C": "🔴 C"}.get(seg, "⚪")

    def loan_display(f):
        l = f.get("loan")
        return f"{int(l['final_amount']):,} Ar" if l else "Not eligible"

    df = pd.DataFrame([{
        "Name":       f["name"],
        "Region":     f["region"],
        "Cash Crop":  f.get("cash_crop", "—") if f.get("cash_crop") != "None" else "—",
        "Food Crop":  f.get("food_crop",  "—") if f.get("food_crop")  != "None" else "—",
        "Score":      f["score"],
        "Segment":    seg_badge(f.get("segment", "C")),
        "Est. Loan":  loan_display(f),
    } for f in filtered])

    if df.empty:
        st.info("No farmers match the selected filters.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={"Score": st.column_config.ProgressColumn(
                         "Score", min_value=0, max_value=100, format="%d/100")})

    st.divider()
    st.subheader("Farmer Detail View")

    farmer_names = [f["name"] for f in filtered]
    if farmer_names:
        choice = st.selectbox("Select a farmer", farmer_names)
        fd     = next(f for f in filtered if f["name"] == choice)
        seg_d, color_d, bg_d = get_segment(fd["score"])
        loan_d = fd.get("loan")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown(f"**Name:** {fd['name']}")
            st.markdown(f"**Region:** {fd['region']}")
            if fd.get("cash_crop") and fd["cash_crop"] != "None":
                st.markdown(f"**Cash Crop:** {fd['cash_crop']} — {fd['cash_area']} ha @ {fd['cash_yield']} t/ha")
            if fd.get("food_crop") and fd["food_crop"] != "None":
                st.markdown(
                    f"**Food Crop:** {fd['food_crop']} — {fd['food_area']} ha @ {fd['food_yield']} t/ha "
                    f"({fd['food_self_consumed']}% self-consumed)"
                )
            st.markdown(f"**Financial Access:** {fd['financial_access']}")
            st.markdown(f"**Cooperative:** {'Yes' if fd['cooperative'] else 'No'}")
            if fd.get("other_revenue", 0) > 0:
                st.markdown(f"**Other Revenues:** {fd['other_revenue']:,} Ar".replace(",", " "))
        with col_d2:
            st.markdown(
                f"<div style='background:{bg_d};border-radius:12px;padding:20px;text-align:center;'>"
                f"<div style='font-size:48px;font-weight:700;color:{color_d};'>{fd['score']}</div>"
                f"<div style='font-size:14px;color:{color_d};font-weight:600;'>Segment {seg_d}</div>"
                f"</div>", unsafe_allow_html=True
            )
            if loan_d:
                st.success(f"💰 Estimated loan: **{int(loan_d['final_amount']):,} Ar**")
                for o in get_loan_offers(seg_d, loan_d["final_amount"]):
                    st.markdown(f"- **{o['institution']}** · {o['amount']} · {o['duration']} · {o['rate']}")
            else:
                st.error("Not eligible for formal credit.")

        if st.button("📊 View full credit score", use_container_width=True):
            st.session_state["current_farmer"] = fd
            st.session_state["page"] = "Credit Score"
            st.rerun()
