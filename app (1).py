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
    "Avocado": 2000, "Cashew Nuts": 6000, "Cassava": 400, "Cloves": 12000,
    "Cocoa": 5000, "Coffee": 8000, "Cotton": 2500, "Cowpeas": 1000,
    "Dairy Farming": 0, "Lychees": 2000, "Livestock": 0, "Maize": 800,
    "Other": 1000, "Pepper": 20000, "Pineapple": 1800, "Potatoes": 1000,
    "Rice": 1200, "Sisal": 900, "Sugarcane": 300, "Tomatoes": 1200,
    "Tropical Fruits": 1800, "Vanilla": 150000, "Vegetables": 1500,
}

ALL_CROPS = sorted(CROP_PRICES_AR.keys())


# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "farmers" not in st.session_state:
    st.session_state["farmers"] = [
        {"name": "Rakoto Jean-Pierre", "region": "Alaotra-Mangoro", "crop": "Rice",
         "area": 2.4, "yield_t": 4.2, "revenue": 3200000,
         "financial_access": "Mobile Money", "cooperative": True},
        {"name": "Rasoamanarivo Aina", "region": "Vakinankaratra", "crop": "Maize",
         "area": 1.1, "yield_t": 2.8, "revenue": 1100000,
         "financial_access": "Mobile Money", "cooperative": False},
        {"name": "Randria Miora", "region": "Androy", "crop": "Rice",
         "area": 0.6, "yield_t": 1.5, "revenue": 400000,
         "financial_access": "None", "cooperative": False},
    ]
if "current_farmer" not in st.session_state:
    st.session_state["current_farmer"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Registration"


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


def calculate_score(area, yield_t, revenue, financial_access, cooperative, region, crop=""):
    """
    100 pts total
      Annual Revenue          30 pts  — primary repayment capacity
      Production (area×yield) 30 pts  — harvest = natural collateral
      Region / Crop Fit       15 pts  — agricultural suitability
      Financial Access        15 pts  — traceability & trust
      Cooperative Membership  10 pts  — collective guarantee
    """
    details = {}

    # 1 — Annual Revenue (30 pts)
    if revenue > 5_000_000:   p1 = 30
    elif revenue > 2_000_000: p1 = 22
    elif revenue > 500_000:   p1 = 12
    else:                     p1 = 4
    details["Annual Revenue"] = (p1, 30)

    # 2 — Production (30 pts)
    production = area * yield_t
    if production > 10:   p2 = 30
    elif production > 5:  p2 = 22
    elif production > 2:  p2 = 12
    else:                 p2 = 4
    details["Production (area x yield)"] = (p2, 30)

    # 3 — Region / Crop Fit (15 pts)
    p3 = region_crop_score(region, crop)
    r_label = (
        "Regional specialty" if p3 == 15 else
        "Climate-compatible"  if p3 == 10 else
        "Poorly adapted"
    )
    details[f"Region / Crop Fit ({r_label})"] = (p3, 15)

    # 4 — Financial Access (15 pts)
    if financial_access == "Bank Account":   p4 = 15
    elif financial_access == "Mobile Money": p4 = 9
    else:                                    p4 = 0
    details["Financial Access (bank / mobile)"] = (p4, 15)

    # 5 — Cooperative Membership (10 pts)
    p5 = 10 if cooperative else 0
    details["Cooperative Membership"] = (p5, 10)

    total = p1 + p2 + p3 + p4 + p5
    return total, details


def get_segment(score):
    if score >= 70:   return "A", "Eligible",               "#1D9E75", "#e0f7ee"
    elif score >= 45: return "B", "Conditionally Eligible", "#d4830a", "#fff3dc"
    else:             return "C", "Not Eligible",           "#c0392b", "#fdecea"


# ─── LOAN ESTIMATION ───────────────────────────────────────────────────────────
def estimate_loan(area, yield_t, revenue, financial_access, cooperative, segment, crop):
    """
    Base     = MIN(30% of annual revenue, 1/4 of harvest value)
    x segment multiplier : A=100%  B=60%  C=not eligible
    + bank account bonus : +10% of amount after segment
    + mobile money bonus : +5%  of amount after segment
    + cooperative bonus  : +10% of amount after segment
    """
    if segment == "C":
        return None

    price_per_kg  = CROP_PRICES_AR.get(crop, 1000)
    approach_rev  = revenue * 0.30
    harvest_value = area * yield_t * price_per_kg * 1000  # tonnes -> kg
    approach_harv = harvest_value / 4 if price_per_kg > 0 else approach_rev
    base_amount   = min(approach_rev, approach_harv) if price_per_kg > 0 else approach_rev

    multiplier = 1.0 if segment == "A" else 0.60
    after_seg  = base_amount * multiplier

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
        "approach_revenue":  approach_rev,
        "harvest_value":     harvest_value,
        "approach_harvest":  approach_harv,
        "price_per_kg":      price_per_kg,
        "base_amount":       base_amount,
        "segment_multiplier":multiplier,
        "amount_after_seg":  after_seg,
        "bonus_breakdown":   bonuses,
        "final_amount":      final,
        "duration":          cond["duration"],
        "rate":              cond["rate"],
        "repayment":         cond["repayment"],
    }


def get_loan_offers(segment, final_amount):
    amt = int(final_amount)
    if segment == "A":
        return [
            {"institution": "CECAM",          "product": "Input Credit",
             "amount": f"{amt:,} Ar",          "duration": "12 months", "rate": "14%", "repayment": "End of harvest"},
            {"institution": "BOA Madagascar",  "product": "Equipment Loan",
             "amount": f"{int(amt*1.5):,} Ar", "duration": "36 months", "rate": "18%", "repayment": "Monthly"},
            {"institution": "MicroCred",       "product": "Working Capital",
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
        f["area"], f["yield_t"], f["revenue"],
        f["financial_access"], f["cooperative"],
        f["region"], f["crop"]
    )
    seg, seg_label, color, bg = get_segment(score)
    loan = estimate_loan(
        f["area"], f["yield_t"], f["revenue"],
        f["financial_access"], f["cooperative"],
        seg, f["crop"]
    )
    return {**f, "score": score, "details": details,
            "segment": seg, "segment_label": seg_label,
            "color": color, "bg": bg, "loan": loan}


# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="header-logo">🌱 CreditWorthy</div>', unsafe_allow_html=True)
    st.caption("Agricultural Credit Platform")
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
    st.caption("Fill in the form to generate a credit score")

    with st.form("reg_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Identity")
            name   = st.text_input("Full Name *", placeholder="e.g. Rakoto Jean-Pierre")
            region = st.selectbox("Region", list(REGIONS.keys()))
            crop   = st.selectbox("Main Crop", ALL_CROPS)
        with col2:
            st.subheader("Farm Data")
            area    = st.number_input("Cultivated Area (hectares) *", min_value=0.1,
                                      max_value=100.0, value=1.0, step=0.1)
            yield_t = st.number_input("Estimated Yield (tonnes/ha)", min_value=0.1,
                                      max_value=20.0, value=2.0, step=0.1)
            revenue = st.number_input("Estimated Annual Revenue (Ariary)", min_value=0,
                                      max_value=50_000_000, value=1_000_000, step=100_000)

        st.subheader("Financial Profile")
        col3, col4 = st.columns(2)
        with col3:
            financial_access = st.selectbox("Financial Access", ["Mobile Money", "Bank Account", "None"])
        with col4:
            cooperative = st.checkbox("Member of an agricultural cooperative")

        submitted = st.form_submit_button("Calculate Credit Score",
                                          use_container_width=True, type="primary")

    if submitted:
        if not name:
            st.error("Please enter a name.")
        else:
            farmer = {
                "name": name, "region": region, "crop": crop,
                "area": area, "yield_t": yield_t, "revenue": revenue,
                "financial_access": financial_access, "cooperative": cooperative,
            }
            existing = [f["name"] for f in st.session_state["farmers"]]
            if name not in existing:
                st.session_state["farmers"].append(farmer)
            st.session_state["current_farmer"] = compute_farmer(farmer)
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

        # Header
        col_info, col_score = st.columns([2, 1])
        with col_info:
            st.markdown(f"### {farmer['name']}")
            st.caption(f"Region: {farmer['region']}  |  Crop: {farmer['crop']}  |  Area: {farmer['area']} ha")
        with col_score:
            st.markdown(f"<div class='score-big' style='color:{color}'>{score}</div>",
                        unsafe_allow_html=True)
            st.markdown("<div class='score-label'>points out of 100</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='text-align:center;margin-top:8px;'>"
                f"<span style='background:{bg};color:{color};padding:6px 18px;"
                f"border-radius:20px;font-weight:600;font-size:15px;'>"
                f"Segment {segment} — {seg_label}</span></div>",
                unsafe_allow_html=True
            )

        st.divider()
        col_left, col_right = st.columns(2)

        # Score breakdown
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

        # Loan estimation
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
                    f"Duration: {loan['duration']}  |  Rate: {loan['rate']}  |  {loan['repayment']}"
                    f"</div></div>",
                    unsafe_allow_html=True
                )

                with st.expander("See calculation details"):
                    st.markdown("**Step 1 — Two base approaches (we keep the lower):**")
                    st.markdown(f"- 30% of annual revenue → **{int(loan['approach_revenue']):,} Ar**")
                    if loan["price_per_kg"] > 0:
                        st.markdown(
                            f"- Harvest value ({farmer['crop']} @ {loan['price_per_kg']:,} Ar/kg)"
                            f" = **{int(loan['harvest_value']):,} Ar**"
                            f" → 1/4 = **{int(loan['approach_harvest']):,} Ar**"
                        )
                    st.markdown(f"- Base = MIN of both → **{int(loan['base_amount']):,} Ar**")
                    st.divider()
                    st.markdown(f"**Step 2 — Segment multiplier ({int(loan['segment_multiplier']*100)}%):**")
                    st.markdown(f"- After segment → **{int(loan['amount_after_seg']):,} Ar**")
                    if loan["bonus_breakdown"]:
                        st.divider()
                        st.markdown("**Step 3 — Bonuses:**")
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
- Join an agricultural cooperative (+10 pts)
- Open a mobile money account (+9 pts) or bank account (+15 pts)
- Increase cultivated area or improve yield (up to +30 pts)
- Grow crops suited to your region (up to +15 pts)
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

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    seg_a = len([f for f in farmers if f["segment"] == "A"])
    seg_b = len([f for f in farmers if f["segment"] == "B"])
    seg_c = len([f for f in farmers if f["segment"] == "C"])
    col1.metric("Total Registered",         len(farmers))
    col2.metric("Segment A — Eligible",     seg_a)
    col3.metric("Segment B — Conditional",  seg_b)
    col4.metric("Segment C — Not Eligible", seg_c)

    st.divider()

    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_seg = st.multiselect("Filter by Segment", ["A", "B", "C"], default=["A", "B", "C"])
    with col_f2:
        all_regions = list(set(f["region"] for f in farmers))
        filter_reg  = st.multiselect("Filter by Region", all_regions, default=all_regions)

    filtered = [f for f in farmers
                if f["segment"] in filter_seg and f["region"] in filter_reg]

    seg_icon = {"A": "🟢 A", "B": "🟡 B", "C": "🔴 C"}

    df = pd.DataFrame([{
        "Name":           f["name"],
        "Region":         f["region"],
        "Crop":           f["crop"],
        "Area (ha)":      f["area"],
        "Score":          f["score"],
        "Segment":        seg_icon.get(f["segment"], "⚪"),
        "Revenue (Ar)":   f"{f['revenue']:,}".replace(",", " "),
        "Est. Loan (Ar)": f"{int(f['loan']['final_amount']):,}".replace(",", " ")
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

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown(f"**Name:** {fd['name']}")
            st.markdown(f"**Region:** {fd['region']}")
            st.markdown(f"**Crop:** {fd['crop']}")
            st.markdown(f"**Area:** {fd['area']} ha")
            st.markdown(f"**Annual Revenue:** {fd['revenue']:,} Ar".replace(",", " "))
            st.markdown(f"**Financial Access:** {fd['financial_access']}")
            st.markdown(f"**Cooperative:** {'Yes' if fd['cooperative'] else 'No'}")
        with col_d2:
            st.markdown(
                f"<div style='background:{fd['bg']};border-radius:12px;"
                f"padding:20px;text-align:center;'>"
                f"<div style='font-size:48px;font-weight:700;color:{fd['color']};'>{fd['score']}</div>"
                f"<div style='font-size:14px;color:{fd['color']};font-weight:600;'>"
                f"Segment {fd['segment']} — {fd['segment_label']}</div></div>",
                unsafe_allow_html=True
            )
            if loan_d:
                st.success(f"Estimated loan: **{int(loan_d['final_amount']):,} Ar**")
                for o in get_loan_offers(fd["segment"], loan_d["final_amount"]):
                    st.markdown(f"- **{o['institution']}** · {o['amount']} · {o['duration']} · {o['rate']}")
            else:
                st.error("Not eligible for formal credit.")

        if st.button("View full credit score", use_container_width=True):
            st.session_state["current_farmer"] = fd
            st.session_state["page"] = "Credit Score"
            st.rerun()
