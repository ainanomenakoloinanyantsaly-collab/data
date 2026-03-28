import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="CreditWorthy", page_icon="🌱", layout="wide")

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
    .loan-amount { font-size: 24px; font-weight: 700; color: #1D9E75; }
    .header-logo { font-size: 28px; font-weight: 800; color: #1D9E75; }
    .credit-box { border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; }
    .credit-amount { font-size: 36px; font-weight: 700; }
    .harvest-info { background: #f0faf5; border-radius: 8px; padding: 12px 16px;
                    border-left: 3px solid #1D9E75; margin-bottom: 12px; font-size: 13px; }
</style>
""", unsafe_allow_html=True)


# ─── REGIONS & CLIMATE COMPATIBILITY ──────────────────────────────────────────
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
    "tropical_humid":    ["Coffee", "Cocoa", "Cloves", "Tropical Fruits", "Rice", "Vegetables"],
    "tropical_dry":      ["Maize", "Cassava", "Cashew Nuts", "Cowpeas", "Rice"],
    "equatorial":        ["Cloves", "Lychees", "Tropical Fruits", "Cocoa"],
    "temperate":         ["Rice", "Vegetables", "Maize", "Potatoes", "Tomatoes", "Pineapple", "Avocado"],
    "tropical_altitude": ["Rice", "Maize", "Vegetables"],
    "semi_arid":         ["Maize", "Cassava", "Cotton", "Livestock"],
    "arid":              ["Cassava", "Livestock", "Sisal"],
}

# Market price per kg in Ariary
CROP_PRICES_AR = {
    "Avocado": 2000, "Cashew Nuts": 6000, "Cassava": 400,  "Cloves": 12000,
    "Cocoa": 5000,   "Coffee": 8000,      "Cotton": 2500,  "Cowpeas": 1000,
    "Dairy Farming": 800, "Lychees": 2000, "Livestock": 1500, "Maize": 800,
    "Other": 1000,   "Pepper": 20000,     "Pineapple": 1800, "Potatoes": 1000,
    "Rice": 1200,    "Sisal": 900,        "Sugarcane": 300,  "Tomatoes": 1200,
    "Tropical Fruits": 1800, "Vanilla": 150000, "Vegetables": 1500,
}

ALL_CROPS = sorted(CROP_PRICES_AR.keys())


# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "farmers" not in st.session_state:
    st.session_state["farmers"] = [
        {"name": "Rakoto Jean-Pierre", "region": "Alaotra-Mangoro", "crop": "Rice",
         "area": 2.4, "yield_t": 4.2,
         "financial_access": "Mobile Money", "cooperative": True},
        {"name": "Rasoamanarivo Aina", "region": "Vakinankaratra", "crop": "Maize",
         "area": 1.1, "yield_t": 2.8,
         "financial_access": "Mobile Money", "cooperative": False},
        {"name": "Randria Miora", "region": "Androy", "crop": "Rice",
         "area": 0.6, "yield_t": 1.5,
         "financial_access": "None", "cooperative": False},
    ]
if "current_farmer" not in st.session_state:
    st.session_state["current_farmer"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Registration"


# ─── HARVEST VALUE (calculated, not declared) ──────────────────────────────────
def harvest_value(area, yield_t, crop):
    """
    Objective estimate of harvest value:
    area (ha) x yield (t/ha) x 1000 (kg/t) x market price (Ar/kg)
    This replaces declared revenue — it is verifiable on the ground.
    """
    price = CROP_PRICES_AR.get(crop, 1000)
    return area * yield_t * 1000 * price


# ─── SCORING ───────────────────────────────────────────────────────────────────
def region_crop_score(region, crop):
    if region not in REGIONS:
        return 5
    specialties = REGIONS[region]["specialties"]
    climate     = REGIONS[region]["climate"]
    if crop in specialties:
        return 15
    if crop in CLIMATE_COMPATIBILITY.get(climate, []):
        return 10
    return 3


def calculate_score(area, yield_t, financial_access, cooperative, region, crop):
    """
    100 pts total — no declared revenue, everything derived from harvest

      Harvest Value (area x yield x price)   40 pts  — repayment capacity
      Production Volume (area x yield)       25 pts  — quantity produced
      Region / Crop Fit                      20 pts  — agricultural suitability
      Financial Access                       10 pts  — traceability & trust
      Cooperative Membership                  5 pts  — collective guarantee

    Note: financial access and cooperative membership have lower weight in the
    score because their main role is as BONUSES in the loan amount calculation.
    """
    details = {}

    # 1 — Harvest Value (40 pts)
    hv = harvest_value(area, yield_t, crop)
    if hv > 10_000_000:  p1 = 40
    elif hv > 5_000_000: p1 = 30
    elif hv > 1_000_000: p1 = 18
    elif hv > 300_000:   p1 = 8
    else:                p1 = 2
    details["Estimated Harvest Value"] = (p1, 40)

    # 2 — Production Volume (25 pts)
    production = area * yield_t
    if production > 10:   p2 = 25
    elif production > 5:  p2 = 18
    elif production > 2:  p2 = 10
    else:                 p2 = 3
    details["Production Volume (area x yield)"] = (p2, 25)

    # 3 — Region / Crop Fit (20 pts)
    raw = region_crop_score(region, crop)
    # remap 15/10/3 → 20/13/3
    if raw == 15:   p3 = 20
    elif raw == 10: p3 = 13
    else:           p3 = 3
    r_label = (
        "Regional specialty" if p3 == 20 else
        "Climate-compatible"  if p3 == 13 else
        "Poorly adapted"
    )
    details[f"Region / Crop Fit ({r_label})"] = (p3, 20)

    # 4 — Financial Access (10 pts)
    if financial_access == "Bank Account":   p4 = 10
    elif financial_access == "Mobile Money": p4 = 6
    else:                                    p4 = 0
    details["Financial Access (bank / mobile)"] = (p4, 10)

    # 5 — Cooperative Membership (5 pts)
    p5 = 5 if cooperative else 0
    details["Cooperative Membership"] = (p5, 5)

    total = p1 + p2 + p3 + p4 + p5
    return total, details


def get_segment(score):
    if score >= 70:   return "A", "Eligible",               "#1D9E75", "#e0f7ee"
    elif score >= 45: return "B", "Conditionally Eligible", "#d4830a", "#fff3dc"
    else:             return "C", "Not Eligible",           "#c0392b", "#fdecea"


# ─── LOAN ESTIMATION ───────────────────────────────────────────────────────────
def estimate_loan(area, yield_t, crop, financial_access, cooperative, segment):
    """
    Loan is based ONLY on harvest value — no declared revenue.

    Base     = 1/4 of estimated harvest value
               (conservative: protects lender against yield shortfall)
    x segment multiplier : A = 100%   B = 60%   C = not eligible
    + bank account bonus : +10% of amount after segment
    + mobile money bonus : +5%  of amount after segment
    + cooperative bonus  : +10% of amount after segment

    Why 1/4?
    Agricultural lending is inherently risky (weather, pests, prices).
    Lending only 25% of harvest value ensures the farmer can repay
    even with a 75% crop loss — making default very unlikely.
    """
    if segment == "C":
        return None

    hv   = harvest_value(area, yield_t, crop)
    base = hv / 4

    multiplier = 1.0 if segment == "A" else 0.60
    after_seg  = base * multiplier

    bonuses     = []
    bonus_total = 0
    if financial_access == "Bank Account":
        b = after_seg * 0.10
        bonuses.append(("Bank Account (+10%)", b))
        bonus_total += b
    elif financial_access == "Mobile Money":
        b = after_seg * 0.05
        bonuses.append(("Mobile Money (+5%)", b))
        bonus_total += b
    if cooperative:
        b = after_seg * 0.10
        bonuses.append(("Cooperative (+10%)", b))
        bonus_total += b

    final = after_seg + bonus_total

    conditions = {
        "A": {"duration": "6 – 36 months", "rate": "14%", "repayment": "End of harvest"},
        "B": {"duration": "3 – 12 months", "rate": "20%", "repayment": "Monthly instalments"},
    }
    cond = conditions[segment]

    return {
        "harvest_value":      hv,
        "price_per_kg":       CROP_PRICES_AR.get(crop, 1000),
        "base_amount":        base,
        "segment_multiplier": multiplier,
        "amount_after_seg":   after_seg,
        "bonus_breakdown":    bonuses,
        "final_amount":       final,
        "duration":           cond["duration"],
        "rate":               cond["rate"],
        "repayment":          cond["repayment"],
    }


def get_loan_offers(segment, final_amount):
    amt = int(final_amount)
    if segment == "A":
        return [
            {"institution": "CECAM",         "product": "Input Credit",
             "amount": f"{amt:,} Ar",          "duration": "12 months", "rate": "14%", "repayment": "End of harvest"},
            {"institution": "BOA Madagascar", "product": "Equipment Loan",
             "amount": f"{int(amt*1.5):,} Ar", "duration": "36 months", "rate": "18%", "repayment": "Monthly"},
            {"institution": "MicroCred",      "product": "Working Capital",
             "amount": f"{int(amt*0.6):,} Ar", "duration": "6 months",  "rate": "22%", "repayment": "Mobile Money"},
        ]
    elif segment == "B":
        return [
            {"institution": "MicroCred", "product": "Micro Agricultural Loan",
             "amount": f"{amt:,} Ar",    "duration": "6 months", "rate": "24%", "repayment": "Monthly"},
        ]
    return []


def compute_farmer(f):
    score, details = calculate_score(
        f["area"], f["yield_t"],
        f["financial_access"], f["cooperative"],
        f["region"], f["crop"]
    )
    seg, seg_label, color, bg = get_segment(score)
    loan = estimate_loan(
        f["area"], f["yield_t"], f["crop"],
        f["financial_access"], f["cooperative"], seg
    )
    return {**f, "score": score, "details": details,
            "segment": seg, "segment_label": seg_label,
            "color": color, "bg": bg, "loan": loan}


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
    st.caption("Fill in the form — the credit estimate is calculated automatically from your harvest data")

    with st.form("reg_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Identity")
            name   = st.text_input("Full Name *", placeholder="e.g. Rakoto Jean-Pierre")
            region = st.selectbox("Region", list(REGIONS.keys()))
            crop   = st.selectbox("Main Crop", ALL_CROPS)
        with col2:
            st.subheader("Farm Data")
            area    = st.number_input("Cultivated Area (hectares) *",
                                      min_value=0.1, max_value=100.0, value=1.0, step=0.1)
            yield_t = st.number_input("Estimated Yield (tonnes/ha)",
                                      min_value=0.1, max_value=20.0,  value=2.0, step=0.1)

        st.subheader("Financial Profile")
        col3, col4 = st.columns(2)
        with col3:
            financial_access = st.selectbox("Financial Access",
                                            ["Mobile Money", "Bank Account", "None"])
        with col4:
            cooperative = st.checkbox("Member of an agricultural cooperative")

        submitted = st.form_submit_button("Calculate Credit Score & Loan Estimate",
                                          use_container_width=True, type="primary")

    if submitted:
        if not name:
            st.error("Please enter a name.")
        else:
            farmer_raw = {
                "name": name, "region": region, "crop": crop,
                "area": area, "yield_t": yield_t,
                "financial_access": financial_access, "cooperative": cooperative,
            }
            farmer = compute_farmer(farmer_raw)
            existing = [f["name"] for f in st.session_state["farmers"]]
            if name not in existing:
                st.session_state["farmers"].append(farmer_raw)
            st.session_state["current_farmer"] = farmer
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
            raw = next(f for f in st.session_state["farmers"] if f["name"] == choice)
            st.session_state["current_farmer"] = compute_farmer(raw)
            st.rerun()

    else:
        score     = farmer["score"]
        details   = farmer["details"]
        segment   = farmer["segment"]
        seg_label = farmer["segment_label"]
        color     = farmer["color"]
        bg        = farmer["bg"]
        loan      = farmer["loan"]
        offers    = get_loan_offers(segment, loan["final_amount"]) if loan else []

        # ── Header
        col_info, col_score = st.columns([2, 1])
        with col_info:
            st.markdown(f"### {farmer['name']}")
            st.caption(
                f"Region: {farmer['region']}  |  "
                f"Crop: {farmer['crop']}  |  "
                f"Area: {farmer['area']} ha  |  "
                f"Yield: {farmer['yield_t']} t/ha"
            )

            )
        with col_score:
            st.markdown(f"<div class='score-big' style='color:{color}'>{score}</div>",
                        unsafe_allow_html=True)
            st.markdown("<div class='score-label'>points out of 100</div>",
                        unsafe_allow_html=True)
            st.markdown(
                f"<div style='text-align:center;margin-top:8px;'>"
                f"<span style='background:{bg};color:{color};padding:6px 18px;"
                f"border-radius:20px;font-weight:600;font-size:15px;'>"
                f"Segment {segment} — {seg_label}</span></div>",
                unsafe_allow_html=True
            )

        st.divider()
        col_left, col_right = st.columns(2)

        # ── Score breakdown
        with col_left:
            st.subheader("Score Breakdown")
            for criterion, (pts, max_pts) in details.items():
                st.markdown(f"**{criterion}** — {pts} / {max_pts} pts")
                st.progress(pts / max_pts)

            st.subheader("Score Gauge")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar":  {"color": color},
                    "steps": [
                        {"range": [0,  44], "color": "#fdecea"},
                        {"range": [45, 69], "color": "#fff3dc"},
                        {"range": [70,100], "color": "#e0f7ee"},
                    ],
                },
                number={"suffix": "/100", "font": {"size": 32}}
            ))
            fig.update_layout(height=250, margin=dict(t=20, b=10, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

        # ── Loan estimation
        with col_right:
            st.subheader("Estimated Loan Amount")

            if loan:
                st.markdown(
                    f"<div class='credit-box' style='background:{bg};'>"
                    f"<div style='font-size:13px;color:{color};font-weight:600;margin-bottom:8px;'>"
                    f"Estimated Loan · Segment {segment}</div>"
                    f"<div class='credit-amount' style='color:{color};'>"
                    f"{int(loan['final_amount']):,} Ar</div>"
                    f"<div style='font-size:12px;color:#555;margin-top:6px;'>"
                    f"Duration: {loan['duration']}  |  "
                    f"Rate: {loan['rate']}  |  "
                    f"{loan['repayment']}</div></div>",
                    unsafe_allow_html=True
                )

                with st.expander("See calculation details"):
                    st.markdown("**Harvest value (objective basis):**")
                    st.markdown(
                        f"- {farmer['area']} ha × {farmer['yield_t']} t/ha"
                        f" × {loan['price_per_kg']:,} Ar/kg"
                        f" = **{int(loan['harvest_value']):,} Ar**"
                    )
                    st.divider()
                    st.markdown("**Step 1 — Base loan (1/4 of harvest value):**")
                    st.markdown(
                        f"- {int(loan['harvest_value']):,} Ar ÷ 4"
                        f" = **{int(loan['base_amount']):,} Ar**"
                    )
                    st.caption(
                        "Why 1/4? This ensures repayment even with a 75% crop loss — "
                        "making default very unlikely."
                    )
                    st.divider()
                    st.markdown(f"**Step 2 — Segment multiplier ({int(loan['segment_multiplier']*100)}%):**")
                    st.markdown(f"- After segment → **{int(loan['amount_after_seg']):,} Ar**")
                    if loan["bonus_breakdown"]:
                        st.divider()
                        st.markdown("**Step 3 — Bonuses (financial access & cooperative):**")
                        for label, val in loan["bonus_breakdown"]:
                            st.markdown(f"- {label}: **+{int(val):,} Ar**")
                    st.divider()
                    st.markdown(f"### Final estimated loan: **{int(loan['final_amount']):,} Ar**")
                    st.caption("Indicative only. Final credit decision belongs to the lender.")

                st.subheader("Available Loan Offers")
                for offer in offers:
                    st.markdown(
                        f"<div class='loan-card'>"
                        f"<div style='font-size:13px;color:#555;font-weight:600;'>"
                        f"{offer['institution']} · {offer['product']}</div>"
                        f"<div class='loan-amount'>{offer['amount']}</div>"
                        f"<div style='font-size:13px;color:#444;margin-top:6px;'>"
                        f"{offer['duration']}  |  {offer['rate']}  |  {offer['repayment']}"
                        f"</div></div>",
                        unsafe_allow_html=True
                    )

            else:
                st.error("This farmer is not eligible for formal credit.")
                st.info("""
**Recommendations to improve the score:**
- Grow crops suited to your region — regional specialty gives up to +20 pts
- Increase cultivated area or improve yield — up to +65 pts combined
- Open a mobile money account (+6 pts) or bank account (+10 pts)
- Join an agricultural cooperative (+5 pts)
                """)

        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Register a new farmer", use_container_width=True):
                st.session_state["current_farmer"] = None
                st.session_state["page"] = "Registration"
                st.rerun()
        with col_b:
            if st.button("Go to Lender Portal", use_container_width=True):
                st.session_state["page"] = "Lender Portal"
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — LENDER PORTAL
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state["page"] == "Lender Portal":
    st.title("Lender Portal")
    st.caption("Overview of scored and pre-qualified farmers")

    farmers = [compute_farmer(f) for f in st.session_state["farmers"]]

    # ── Metrics
    col1, col2, col3, col4 = st.columns(4)
    seg_a = len([f for f in farmers if f["segment"] == "A"])
    seg_b = len([f for f in farmers if f["segment"] == "B"])
    seg_c = len([f for f in farmers if f["segment"] == "C"])
    col1.metric("Total Registered",         len(farmers))
    col2.metric("Segment A — Eligible",     seg_a)
    col3.metric("Segment B — Conditional",  seg_b)
    col4.metric("Segment C — Not Eligible", seg_c)

    st.divider()

    # ── Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_seg = st.multiselect("Filter by Segment", ["A", "B", "C"],
                                    default=["A", "B", "C"])
    with col_f2:
        all_regions = list(set(f["region"] for f in farmers))
        filter_reg  = st.multiselect("Filter by Region", all_regions, default=all_regions)

    filtered = [f for f in farmers
                if f["segment"] in filter_seg and f["region"] in filter_reg]

    seg_icon = {"A": "🟢 A", "B": "🟡 B", "C": "🔴 C"}

    df = pd.DataFrame([{
        "Name":              f["name"],
        "Region":            f["region"],
        "Crop":              f["crop"],
        "Area (ha)":         f["area"],
        "Yield (t/ha)":      f["yield_t"],
        "Harvest Value (Ar)":f"{int(harvest_value(f['area'],f['yield_t'],f['crop'])):,}".replace(",", " "),
        "Score":             f["score"],
        "Segment":           seg_icon.get(f["segment"], "⚪"),
        "Est. Loan (Ar)":    f"{int(f['loan']['final_amount']):,}".replace(",", " ")
                             if f["loan"] else "Not eligible",
    } for f in filtered])

    if df.empty:
        st.info("No farmers match the selected filters.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={"Score": st.column_config.ProgressColumn(
                         "Score", min_value=0, max_value=100, format="%d/100")})

    st.divider()
    st.subheader("Farmer Detail View")

    names = [f["name"] for f in filtered]
    if names:
        choice = st.selectbox("Select a farmer", names)
        fd     = next(f for f in filtered if f["name"] == choice)
        loan_d = fd["loan"]
        hv_d   = harvest_value(fd["area"], fd["yield_t"], fd["crop"])

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown(f"**Name:** {fd['name']}")
            st.markdown(f"**Region:** {fd['region']}")
            st.markdown(f"**Crop:** {fd['crop']}")
            st.markdown(f"**Area:** {fd['area']} ha")
            st.markdown(f"**Yield:** {fd['yield_t']} t/ha")
            st.markdown(f"**Harvest Value:** {int(hv_d):,} Ar".replace(",", " "))
            st.markdown(f"**Financial Access:** {fd['financial_access']}")
            st.markdown(f"**Cooperative:** {'Yes' if fd['cooperative'] else 'No'}")
        with col_d2:
            st.markdown(
                f"<div style='background:{fd['bg']};border-radius:12px;"
                f"padding:20px;text-align:center;'>"
                f"<div style='font-size:48px;font-weight:700;color:{fd['color']};'>"
                f"{fd['score']}</div>"
                f"<div style='font-size:14px;color:{fd['color']};font-weight:600;'>"
                f"Segment {fd['segment']} — {fd['segment_label']}</div></div>",
                unsafe_allow_html=True
            )
            if loan_d:
                st.success(f"Estimated loan: **{int(loan_d['final_amount']):,} Ar**")
                for o in get_loan_offers(fd["segment"], loan_d["final_amount"]):
                    st.markdown(
                        f"- **{o['institution']}** · {o['amount']}"
                        f" · {o['duration']} · {o['rate']}"
                    )
            else:
                st.error("Not eligible for formal credit.")

        if st.button("View full credit score", use_container_width=True):
            st.session_state["current_farmer"] = fd
            st.session_state["page"] = "Credit Score"
            st.rerun()
