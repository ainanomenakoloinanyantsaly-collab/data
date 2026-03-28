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
        padding: 3px 10px; border-radius: 20px; margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)


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

# All crops — any crop can be primary or secondary
ALL_CROPS = sorted([
    "Rice", "Maize", "Cassava", "Potatoes", "Sweet Potato",
    "Tomatoes", "Vegetables", "Cowpeas",
    "Vanilla", "Cloves", "Coffee", "Cocoa", "Pepper",
    "Cashew Nuts", "Cotton", "Sisal", "Sugarcane",
    "Lychees", "Tropical Fruits", "Pineapple", "Avocado",
    "Livestock", "Dairy Farming", "Other",
])

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

# Regional multiplier for the SOLD portion (cash impact)
CASH_REGION_MULTIPLIER = {
    "specialty":  1.00,
    "compatible": 0.75,
    "unsuited":   0.40,
}

# Regional multiplier for the SELF-CONSUMED portion (food security)
# Light penalty only — food role doesn't require regional optimality
FOOD_REGION_MULTIPLIER = {
    "specialty":  1.00,
    "compatible": 1.00,
    "unsuited":   0.80,
}

FIT_LABEL = {
    "specialty":  "✅ Regional specialty",
    "compatible": "⚠️ Climate-compatible",
    "unsuited":   "❌ Poorly adapted",
}


# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "farmers" not in st.session_state:
    st.session_state["farmers"] = [
        {
            "name": "Rakoto Jean-Pierre", "region": "Alaotra-Mangoro",
            "main_crop": "Rice",    "main_area": 1.3,  "main_yield": 2.5, "main_self_consumed": 70,
            "sec_crop":  "None",    "sec_area":  0.0,  "sec_yield":  0.0, "sec_self_consumed": 20,
            "other_revenue": 0,
            "financial_access": "Mobile Money", "cooperative": True,
            "score": None, "segment": None, "loan": None,
        },
        {
            "name": "Rasoamanarivo Aina", "region": "SAVA",
            "main_crop": "Vanilla", "main_area": 0.3,  "main_yield": 0.25,"main_self_consumed": 0,
            "sec_crop":  "Rice",    "sec_area":  1.0,  "sec_yield":  2.5, "sec_self_consumed": 75,
            "other_revenue": 0,
            "financial_access": "Mobile Money", "cooperative": False,
            "score": None, "segment": None, "loan": None,
        },
        {
            "name": "Randria Miora", "region": "Androy",
            "main_crop": "Cassava", "main_area": 0.6,  "main_yield": 7.0, "main_self_consumed": 90,
            "sec_crop":  "None",    "sec_area":  0.0,  "sec_yield":  0.0, "sec_self_consumed": 0,
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
    """Return 'specialty', 'compatible', or 'unsuited'."""
    if region not in REGIONS or not crop or crop == "None":
        return "compatible"
    if crop in REGIONS[region]["specialties"]:
        return "specialty"
    climate = REGIONS[region]["climate"]
    if crop in CLIMATE_COMPATIBILITY.get(climate, []):
        return "compatible"
    return "unsuited"


def crop_components(crop, area, yield_t, self_consumed_pct, region):
    """
    Split a crop into its cash component and food security component.
    Any crop can be partially sold and partially eaten.

    cash_value  = area × yield × 1000 × price × (1 - self_consumed%) × region_cash_mult
    food_value  = area × yield × (self_consumed%) × region_food_mult   (in tonnes consumed)
    indirect_ar = food_value × 1000 × price × 0.40   (indirect savings, 40% weight)
    """
    if not crop or crop == "None" or area <= 0:
        return 0, 0, 0, "compatible"

    price     = CROP_PRICES_AR.get(crop, 800)
    fit       = get_region_fit(region, crop)
    cash_mult = CASH_REGION_MULTIPLIER[fit]
    food_mult = FOOD_REGION_MULTIPLIER[fit]

    pct_sold  = (100 - self_consumed_pct) / 100
    pct_auto  = self_consumed_pct / 100

    total_harvest_ar = area * yield_t * 1000 * price

    # Cash: sold portion, discounted by region fit
    cash_ar = total_harvest_ar * pct_sold * cash_mult

    # Food security: tonnes self-consumed (for scoring)
    food_tonnes = area * yield_t * pct_auto * food_mult

    # Indirect savings in Ar (for loan base)
    indirect_ar = total_harvest_ar * pct_auto * 0.40

    return cash_ar, food_tonnes, indirect_ar, fit


# ─── SCORING ───────────────────────────────────────────────────────────────────
def calculate_score(
    main_crop, main_area, main_yield, main_self_consumed,
    sec_crop,  sec_area,  sec_yield,  sec_self_consumed,
    other_revenue, financial_access, cooperative, region
):
    """
    Scoring — 100 pts total

      Cash production value    30 pts  — sold portion of all crops, calibrated to Madagascar
      Region fit (cash)        20 pts  — strong: repayment depends on harvest success
      Food security            10 pts  — self-consumed tonnes reduce default risk
      Financial Access         20 pts  — repayment channel & traceability
      Cooperative Membership   10 pts  — collective guarantee
      Other Revenues (opt.)    10 pts  — non-verifiable bonus
    """
    score   = 0
    details = {}

    # Compute components for both crops
    main_cash_ar, main_food_t, main_indirect_ar, main_fit = crop_components(
        main_crop, main_area, main_yield, main_self_consumed, region
    )
    sec_cash_ar, sec_food_t, sec_indirect_ar, sec_fit = crop_components(
        sec_crop, sec_area, sec_yield, sec_self_consumed, region
    )

    total_cash_ar  = main_cash_ar  + sec_cash_ar
    total_food_t   = main_food_t   + sec_food_t

    # Best fit among crops with a sold portion (drives region score)
    fits_ranked = {"specialty": 2, "compatible": 1, "unsuited": 0}
    main_has_cash = main_crop and main_crop != "None" and main_area > 0 and main_self_consumed < 100
    sec_has_cash  = sec_crop  and sec_crop  != "None" and sec_area  > 0 and sec_self_consumed  < 100
    if main_has_cash and sec_has_cash:
        best_fit = main_fit if fits_ranked[main_fit] >= fits_ranked[sec_fit] else sec_fit
    elif main_has_cash:
        best_fit = main_fit
    elif sec_has_cash:
        best_fit = sec_fit
    else:
        best_fit = "unsuited"

    # 1 — Cash production value (30 pts) — calibrated for Madagascar
    if total_cash_ar > 10_000_000:   p1 = 30
    elif total_cash_ar > 4_000_000:  p1 = 22
    elif total_cash_ar > 1_000_000:  p1 = 14
    elif total_cash_ar > 200_000:    p1 = 7
    elif total_cash_ar > 0:          p1 = 2
    else:                            p1 = 0
    score += p1
    details["Cash Production Value (sold portion)"] = (p1, 30)

    # 2 — Region fit for cash (20 pts)
    if main_has_cash or sec_has_cash:
        if best_fit == "specialty":    p2, fl = 20, FIT_LABEL["specialty"]
        elif best_fit == "compatible": p2, fl = 13, FIT_LABEL["compatible"]
        else:                          p2, fl = 3,  FIT_LABEL["unsuited"]
    else:
        p2, fl = 0, "—"
    score += p2
    details[f"Region Fit for Sold Crops ({fl})"] = (p2, 20)

    # 3 — Food security (10 pts) — tonnes self-consumed across all crops
    if total_food_t > 3:     p3 = 10
    elif total_food_t > 1:   p3 = 7
    elif total_food_t > 0.3: p3 = 4
    elif total_food_t > 0:   p3 = 1
    else:                    p3 = 0
    score += p3
    details["Food Security (self-consumed tonnes)"] = (p3, 10)

    # 4 — Financial Access (20 pts)
    if financial_access == "Bank Account":   p4 = 20
    elif financial_access == "Mobile Money": p4 = 12
    else:                                    p4 = 0
    score += p4
    details["Financial Access (bank / mobile)"] = (p4, 20)

    # 5 — Cooperative Membership (10 pts)
    p5 = 10 if cooperative else 0
    score += p5
    details["Cooperative Membership"] = (p5, 10)

    # 6 — Other Revenues (10 pts, optional)
    if other_revenue and other_revenue > 0:
        if other_revenue > 3_000_000:   p6 = 10
        elif other_revenue > 1_000_000: p6 = 7
        elif other_revenue > 300_000:   p6 = 4
        else:                           p6 = 1
    else:
        p6 = 0
    score += p6
    details["Other Revenues (optional bonus)"] = (p6, 10)

    extra = {
        "main_fit": main_fit, "sec_fit": sec_fit, "best_fit": best_fit,
        "total_cash_ar": total_cash_ar, "total_food_t": total_food_t,
        "main_cash_ar": main_cash_ar, "sec_cash_ar": sec_cash_ar,
        "main_food_t": main_food_t,   "sec_food_t": sec_food_t,
        "main_indirect_ar": main_indirect_ar, "sec_indirect_ar": sec_indirect_ar,
    }
    return score, details, extra


def get_segment(score):
    if score >= 70:
        return "A — Eligible",               "#1D9E75", "#e0f7ee"
    elif score >= 45:
        return "B — Conditionally Eligible",  "#d4830a", "#fff3dc"
    else:
        return "C — Not Eligible",            "#c0392b", "#fdecea"


# ─── LOAN ESTIMATION ───────────────────────────────────────────────────────────
def estimate_loan(extra, other_revenue, financial_access, cooperative, segment_label):
    """
    Base = (total sold cash / 4)
         + (total indirect food savings / 4)
         + (other_revenue × 20%)

    All region multipliers already baked into crop_components().
    """
    if "C" in segment_label:
        return None

    cash_component     = extra["total_cash_ar"] / 4
    indirect_component = (extra["main_indirect_ar"] + extra["sec_indirect_ar"]) / 4
    other_component    = (other_revenue * 0.20) if (other_revenue and other_revenue > 0) else 0

    base = cash_component + indirect_component + other_component

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
        "cash_component":       cash_component,
        "indirect_component":   indirect_component,
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
            f.get("main_crop", "None"), f.get("main_area", 0),
            f.get("main_yield", 0),    f.get("main_self_consumed", 70),
            f.get("sec_crop",  "None"), f.get("sec_area",  0),
            f.get("sec_yield", 0),     f.get("sec_self_consumed",  0),
            f.get("other_revenue", 0),
            f["financial_access"], f["cooperative"], f["region"]
        )
        f["score"]   = score
        f["details"] = details
        f["extra"]   = extra
        seg_label, _, _ = get_segment(score)
        f["segment"] = seg_label[0]
        f["loan"]    = estimate_loan(
            extra, f.get("other_revenue", 0),
            f["financial_access"], f["cooperative"], seg_label
        )
    return f


# ─── RECOMMENDATIONS — based on actual scoring gaps ────────────────────────────
def build_recommendations(score, details, extra, farmer):
    recs = []

    # Cash production gap
    cash_pts, cash_max = details.get("Cash Production Value (sold portion)", (0, 30))
    if cash_pts < cash_max:
        gap = cash_max - cash_pts
        if extra.get("total_cash_ar", 0) == 0:
            recs.append(f"🌾 You have no sold production — even selling a small portion of your harvest could add up to +{cash_max} pts")
        else:
            recs.append(f"🌾 Increase your sold production (area, yield, or % sold) to gain up to +{gap} pts")

    # Region fit gap
    fit_pts, fit_max = details.get(
        [k for k in details if "Region Fit" in k][0] if any("Region Fit" in k for k in details) else "x",
        (0, 20)
    )
    if fit_pts < fit_max:
        gap = fit_max - fit_pts
        region = farmer.get("region", "")
        specialties = REGIONS.get(region, {}).get("specialties", [])
        if specialties and fit_pts < 20:
            recs.append(f"📍 Growing a regional specialty in {region} ({', '.join(specialties[:2])}) could add up to +{gap} pts")

    # Food security gap
    food_pts, food_max = details.get("Food Security (self-consumed tonnes)", (0, 10))
    if food_pts < food_max:
        gap = food_max - food_pts
        if extra.get("total_food_t", 0) == 0:
            recs.append(f"🍚 Declaring a food crop (rice, cassava, maize…) reduces your default risk and adds up to +{food_max} pts")
        else:
            recs.append(f"🍚 Increasing your self-consumed production could add +{gap} pts")

    # Financial access gap
    fin_pts, fin_max = details.get("Financial Access (bank / mobile)", (0, 20))
    if fin_pts < fin_max:
        if fin_pts == 0:
            recs.append("📱 Opening a Mobile Money account would add +12 pts — a Bank Account adds +20 pts")
        elif fin_pts == 12:
            recs.append("🏦 Upgrading to a Bank Account would add +8 pts over Mobile Money")

    # Cooperative gap
    coop_pts, _ = details.get("Cooperative Membership", (0, 10))
    if coop_pts == 0:
        recs.append("🤝 Joining an agricultural cooperative adds +10 pts and strengthens your collective guarantee")

    # Other revenue gap
    other_pts, _ = details.get("Other Revenues (optional bonus)", (0, 10))
    if other_pts == 0:
        recs.append("💼 If you have other income (trade, seasonal work…), declaring it can add up to +10 pts")

    return recs


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

        # Identity
        st.subheader("👤 Identity")
        col1, col2 = st.columns(2)
        with col1:
            name   = st.text_input("Full Name *", placeholder="e.g. Rakoto Jean-Pierre")
        with col2:
            region = st.selectbox("Region", list(REGIONS.keys()))

        st.divider()

        # Main crop
        st.markdown(
            "<span class='section-tag' style='background:#e0f7ee;color:#1D9E75;'>"
            "🌾 MAIN CROP *</span>", unsafe_allow_html=True
        )
        st.caption(
            "Your primary crop — can be anything (rice, vanilla, cassava…). "
            "Use the slider to say how much you keep for your family vs sell."
        )
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            main_crop  = st.selectbox("Main Crop *", ALL_CROPS, key="mc")
        with col_m2:
            main_area  = st.number_input("Area (ha)", min_value=0.1, max_value=100.0, value=1.0, step=0.05, key="ma")
        with col_m3:
            main_yield = st.number_input("Yield (t/ha)", min_value=0.1, max_value=20.0, value=2.5, step=0.1, key="my")
        main_self_consumed = st.slider(
            "Share kept for family consumption (%)",
            min_value=0, max_value=100, value=70, step=5,
            help="0% = everything sold · 100% = nothing sold, family eats everything"
        )
        pct_sold_main = 100 - main_self_consumed
        st.caption(f"→ **{pct_sold_main}% sold** on the market · **{main_self_consumed}% kept** for the family")

        st.divider()

        # Secondary crop (optional)
        st.markdown(
            "<span class='section-tag' style='background:#f0f4ff;color:#3b5bdb;'>"
            "🌿 SECONDARY CROP (optional)</span>", unsafe_allow_html=True
        )
        st.caption("A second crop if you grow more than one. Leave area at 0 to skip.")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            sec_crop  = st.selectbox("Secondary Crop", ["None"] + ALL_CROPS, key="sc")
        with col_s2:
            sec_area  = st.number_input("Area (ha)", min_value=0.0, max_value=100.0, value=0.0, step=0.05, key="sa")
        with col_s3:
            sec_yield = st.number_input("Yield (t/ha)", min_value=0.0, max_value=20.0, value=0.0, step=0.1, key="sy")
        sec_self_consumed = st.slider(
            "Share kept for family consumption (%) — secondary",
            min_value=0, max_value=100, value=20, step=5, key="ssc"
        )

        st.divider()

        # Financial profile
        st.subheader("🏦 Financial Profile")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            financial_access = st.selectbox("Financial Access", ["Mobile Money", "Bank Account", "None"])
        with col_p2:
            cooperative = st.checkbox("Member of an agricultural cooperative")
        with col_p3:
            other_revenue = st.number_input(
                "Other Annual Revenues (Ar) — optional",
                min_value=0, max_value=50_000_000, value=0, step=100_000,
                help="Non-agricultural income: trade, seasonal work, family transfers…"
            )

        submitted = st.form_submit_button(
            "🔍 Calculate Score & Loan Estimate",
            use_container_width=True, type="primary"
        )

    if submitted:
        if not name:
            st.error("Please enter a name.")
        else:
            score, details, extra = calculate_score(
                main_crop, main_area, main_yield, main_self_consumed,
                sec_crop,  sec_area,  sec_yield,  sec_self_consumed,
                other_revenue, financial_access, cooperative, region
            )
            segment_label, color, bg = get_segment(score)
            loan = estimate_loan(extra, other_revenue, financial_access, cooperative, segment_label)
            farmer = {
                "name": name, "region": region,
                "main_crop": main_crop, "main_area": main_area,
                "main_yield": main_yield, "main_self_consumed": main_self_consumed,
                "sec_crop": sec_crop, "sec_area": sec_area,
                "sec_yield": sec_yield, "sec_self_consumed": sec_self_consumed,
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

        # Header
        col_info, col_score = st.columns([2, 1])
        with col_info:
            st.markdown(f"### 👤 {farmer['name']}")
            st.caption(f"📍 {farmer['region']} · {farmer['financial_access']}")
            pct_sold = 100 - farmer['main_self_consumed']
            st.caption(
                f"🌾 Main: {farmer['main_crop']} — {farmer['main_area']} ha @ {farmer['main_yield']} t/ha "
                f"({pct_sold}% sold · {farmer['main_self_consumed']}% family)"
            )
            if farmer.get("sec_crop") and farmer["sec_crop"] != "None" and farmer.get("sec_area", 0) > 0:
                pct_sold_s = 100 - farmer['sec_self_consumed']
                st.caption(
                    f"🌿 Secondary: {farmer['sec_crop']} — {farmer['sec_area']} ha @ {farmer['sec_yield']} t/ha "
                    f"({pct_sold_s}% sold · {farmer['sec_self_consumed']}% family)"
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

        # Score breakdown
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

        # Loan
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
                    st.markdown("**Step 1 — Sold production (cash repayment source):**")
                    if extra.get("main_cash_ar", 0) > 0:
                        st.markdown(
                            f"- {farmer['main_crop']} sold portion → **{int(extra['main_cash_ar']):,} Ar** "
                            f"(fit: {FIT_LABEL[extra['main_fit']]})"
                        )
                    if extra.get("sec_cash_ar", 0) > 0:
                        st.markdown(
                            f"- {farmer['sec_crop']} sold portion → **{int(extra['sec_cash_ar']):,} Ar** "
                            f"(fit: {FIT_LABEL[extra['sec_fit']]})"
                        )
                    st.markdown(f"- Total cash → **{int(extra['total_cash_ar']):,} Ar** → ÷4 = **{int(loan['cash_component']):,} Ar**")

                    if loan["indirect_component"] > 0:
                        st.divider()
                        st.markdown("**Step 2 — Self-consumed portion (indirect food savings × 40%):**")
                        if extra.get("main_indirect_ar", 0) > 0:
                            st.markdown(f"- {farmer['main_crop']} family share → {int(extra['main_indirect_ar']):,} Ar")
                        if extra.get("sec_indirect_ar", 0) > 0:
                            st.markdown(f"- {farmer['sec_crop']} family share → {int(extra['sec_indirect_ar']):,} Ar")
                        st.markdown(f"- → ÷4 = **{int(loan['indirect_component']):,} Ar**")

                    if loan["other_component"] > 0:
                        st.divider()
                        st.markdown("**Step 3 — Other revenues (20%):**")
                        st.markdown(f"- **+{int(loan['other_component']):,} Ar**")

                    st.divider()
                    st.markdown(f"**Base total → {int(loan['base_amount']):,} Ar**")
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
                # Not eligible — show personalised recommendations
                st.error("❌ This farmer is not currently eligible for formal credit.")
                recs = build_recommendations(score, details, extra, farmer)
                if recs:
                    st.markdown("**Here is what could improve the score:**")
                    for rec in recs:
                        st.markdown(f"- {rec}")
                st.caption(
                    f"Current score: **{score}/100**. "
                    f"Segment B requires 45 pts, Segment A requires 70 pts."
                )

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
        "Name":        f["name"],
        "Region":      f["region"],
        "Main Crop":   f.get("main_crop", "—"),
        "Sec. Crop":   f.get("sec_crop", "—") if f.get("sec_crop") != "None" else "—",
        "Score":       f["score"],
        "Segment":     seg_badge(f.get("segment", "C")),
        "Est. Loan":   loan_display(f),
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
            pct_s = 100 - fd['main_self_consumed']
            st.markdown(
                f"**Main Crop:** {fd['main_crop']} — {fd['main_area']} ha @ {fd['main_yield']} t/ha "
                f"({pct_s}% sold · {fd['main_self_consumed']}% family)"
            )
            if fd.get("sec_crop") and fd["sec_crop"] != "None" and fd.get("sec_area", 0) > 0:
                pct_ss = 100 - fd['sec_self_consumed']
                st.markdown(
                    f"**Secondary Crop:** {fd['sec_crop']} — {fd['sec_area']} ha @ {fd['sec_yield']} t/ha "
                    f"({pct_ss}% sold · {fd['sec_self_consumed']}% family)"
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
                recs = build_recommendations(fd["score"], fd.get("details", {}), fd.get("extra", {}), fd)
                for rec in recs:
                    st.markdown(f"- {rec}")

        if st.button("📊 View full credit score", use_container_width=True):
            st.session_state["current_farmer"] = fd
            st.session_state["page"] = "Credit Score"
            st.rerun()
