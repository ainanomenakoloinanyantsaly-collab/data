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
    .loan-amount { font-size: 24px; font-weight: 700; color: #1D9E75; }
    .header-logo { font-size: 28px; font-weight: 800; color: #1D9E75; }
    .credit-box { border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; }
    .credit-amount { font-size: 36px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# ─── REGIONS & CROPS ───────────────────────────────────────────────────────────
REGIONS = {
    "SAVA":             {"specialties": ["Vanilla", "Cloves", "Coffee"],           "climate": "tropical_humid"},
    "Diana":            {"specialties": ["Cocoa", "Sugarcane", "Pepper"],          "climate": "tropical_dry"},
    "Analanjirofo":     {"specialties": ["Cloves", "Lychees"],                     "climate": "equatorial"},
    "Atsinanana":       {"specialties": ["Coffee", "Tropical Fruits"],             "climate": "tropical_humid"},
    "Vakinankaratra":   {"specialties": ["Potatoes", "Dairy Farming", "Maize"],    "climate": "temperate"},
    "Analamanga":       {"specialties": ["Vegetables", "Rice"],                    "climate": "temperate"},
    "Itasy":            {"specialties": ["Pineapple", "Avocado", "Tomatoes", "Rice"], "climate": "temperate"},
    "Alaotra-Mangoro":  {"specialties": ["Rice"],                                  "climate": "tropical_altitude"},
    "Boeny":            {"specialties": ["Rice", "Cashew Nuts"],                   "climate": "tropical_dry"},
    "Menabe":           {"specialties": ["Sugarcane", "Maize", "Cowpeas"],         "climate": "tropical_dry"},
    "Atsimo-Andrefana": {"specialties": ["Maize", "Cotton", "Cassava"],            "climate": "semi_arid"},
    "Androy":           {"specialties": ["Livestock", "Sisal", "Cassava"],         "climate": "arid"},
    "Anosy":            {"specialties": ["Livestock", "Sisal", "Cassava"],         "climate": "arid"},
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
    "Rice": 1200, "Maize": 800, "Cassava": 400, "Vegetables": 1500,
    "Coffee": 8000, "Vanilla": 150000, "Cloves": 12000, "Cocoa": 5000,
    "Lychees": 2000, "Tropical Fruits": 1800, "Potatoes": 1000,
    "Tomatoes": 1200, "Cashew Nuts": 6000, "Sugarcane": 300,
    "Pineapple": 1800, "Avocado": 2000, "Cowpeas": 1000,
    "Cotton": 2500, "Sisal": 900, "Pepper": 20000,
    "Livestock": 0, "Dairy Farming": 0, "Other": 1000,
}

ALL_CROPS = sorted(CROP_PRICES_AR.keys())


# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "farmers" not in st.session_state:
    st.session_state["farmers"] = [
        {"name": "Rakoto Jean-Pierre",   "region": "Alaotra-Mangoro", "crop": "Rice",
         "area": 2.4, "yield_t": 4.2, "revenue": 3200000,
         "financial_access": "Mobile Money", "cooperative": True,  "score": None, "segment": None, "loan": None},
        {"name": "Rasoamanarivo Aina",   "region": "Vakinankaratra", "crop": "Maize",
         "area": 1.1, "yield_t": 2.8, "revenue": 1100000,
         "financial_access": "Mobile Money", "cooperative": False, "score": None, "segment": None, "loan": None},
        {"name": "Randria Miora",        "region": "Androy",         "crop": "Rice",
         "area": 0.6, "yield_t": 1.5, "revenue": 400000,
         "financial_access": "None",         "cooperative": False, "score": None, "segment": None, "loan": None},
    ]
if "current_farmer" not in st.session_state:
    st.session_state["current_farmer"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Registration"


# ─── SCORING LOGIC ─────────────────────────────────────────────────────────────
def region_score(region, crop):
    if region not in REGIONS:
        return 5
    specialties = REGIONS[region]["specialties"]
    climate = REGIONS[region]["climate"]
    if crop in specialties:
        return 15
    compatible = CLIMATE_COMPATIBILITY.get(climate, [])
    if crop in compatible:
        return 10
    return 3


def calculate_score(area, yield_t, revenue, financial_access, cooperative, region, crop=""):
    """
    Scoring — 100 pts total:
      Annual Revenue         30 pts  (main repayment capacity)
      Production (area×yield)30 pts  (harvest = natural guarantee)
      Region / Crop Fit      15 pts  (agricultural context)
      Financial Access       15 pts  (traceability & trust)
      Cooperative Membership 10 pts  (collective guarantee)
    """
    score = 0
    details = {}

    # 1 — Annual Revenue (30 pts)
    if revenue > 5_000_000:   p1 = 30
    elif revenue > 2_000_000: p1 = 22
    elif revenue > 500_000:   p1 = 12
    else:                     p1 = 4
    score += p1
    details["Annual Revenue"] = (p1, 30)

    # 2 — Production (30 pts)
    production = area * yield_t
    if production > 10:   p2 = 30
    elif production > 5:  p2 = 22
    elif production > 2:  p2 = 12
    else:                 p2 = 4
    score += p2
    details["Production (area × yield)"] = (p2, 30)

    # 3 — Region / Crop Fit (15 pts)
    p3 = region_score(region, crop)
    r_label = "✅ Regional specialty" if p3 == 15 else ("⚠️ Climate-compatible" if p3 == 10 else "❌ Poorly adapted")
    score += p3
    details[f"Region / Crop Fit ({r_label})"] = (p3, 15)

    # 4 — Financial Access (15 pts)
    if financial_access == "Bank Account":  p4 = 15
    elif financial_access == "Mobile Money": p4 = 9
    else:                                    p4 = 0
    score += p4
    details["Financial Access (bank/mobile)"] = (p4, 15)

    # 5 — Cooperative Membership (10 pts)
    p5 = 10 if cooperative else 0
    score += p5
    details["Cooperative Membership"] = (p5, 10)

    return score, details


def get_segment(score):
    if score >= 70:
        return "A — Eligible", "#1D9E75", "#e0f7ee"
    elif score >= 45:
        return "B — Conditionally Eligible", "#d4830a", "#fff3dc"
    else:
        return "C — Not Eligible", "#c0392b", "#fdecea"


# ─── LOAN ESTIMATION ───────────────────────────────────────────────────────────
def estimate_loan(area, yield_t, revenue, financial_access, cooperative, segment_label, crop):
    """
    Loan estimation:
      Base = MIN(30% of annual revenue, 1/4 of harvest value)
      x segment multiplier (A=100%, B=60%, C=not eligible)
      + bonuses: bank account +10%, mobile money +5%, cooperative +10%
    """
    price_per_kg = CROP_PRICES_AR.get(crop, 1000)

    approach_revenue = revenue * 0.30

    if price_per_kg > 0:
        harvest_value = area * yield_t * 1000 * price_per_kg
        approach_harvest = harvest_value / 4
    else:
        harvest_value = 0
        approach_harvest = approach_revenue  # livestock/dairy: use revenue only

    base = min(approach_revenue, approach_harvest)

    if "A" in segment_label:
        multiplier = 1.0
        rate = "14%"
        duration = "Up to 36 months"
        repayment = "Flexible (end of harvest)"
    elif "B" in segment_label:
        multiplier = 0.60
        rate = "20%"
        duration = "Up to 12 months"
        repayment = "Monthly installments"
    else:
        return None  # Segment C: not eligible

    amount = base * multiplier

    bonus = 0
    bonus_breakdown = []
    if financial_access == "Bank Account":
        b = amount * 0.10
        bonus += b
        bonus_breakdown.append(("Bank account bonus (+10%)", b))
    elif financial_access == "Mobile Money":
        b = amount * 0.05
        bonus += b
        bonus_breakdown.append(("Mobile money bonus (+5%)", b))
    if cooperative:
        b = amount * 0.10
        bonus += b
        bonus_breakdown.append(("Cooperative guarantee bonus (+10%)", b))

    final_amount = amount + bonus

    return {
        "approach_revenue": approach_revenue,
        "approach_harvest": approach_harvest,
        "harvest_value": harvest_value,
        "price_per_kg": price_per_kg,
        "base_amount": base,
        "segment_multiplier": multiplier,
        "amount_after_segment": amount,
        "bonus_breakdown": bonus_breakdown,
        "total_bonus": bonus,
        "final_amount": final_amount,
        "rate": rate,
        "duration": duration,
        "repayment": repayment,
    }


def get_loan_offers(segment_label, final_amount):
    amt = int(final_amount)
    if "A" in segment_label:
        return [
            {"institution": "CECAM",         "product": "Input Credit",
             "amount": f"{amt:,} Ar",              "duration": "12 months", "rate": "14%", "repayment": "End of harvest"},
            {"institution": "BOA Madagascar", "product": "Equipment Loan",
             "amount": f"{min(amt*3,5000000):,} Ar","duration": "36 months", "rate": "18%", "repayment": "Monthly"},
            {"institution": "MicroCred",      "product": "Working Capital",
             "amount": f"{int(amt*0.6):,} Ar",     "duration": "6 months",  "rate": "22%", "repayment": "Mobile money"},
        ]
    elif "B" in segment_label:
        return [
            {"institution": "MicroCred", "product": "Agricultural Micro-loan",
             "amount": f"{amt:,} Ar", "duration": "6 months", "rate": "24%", "repayment": "Monthly installments"},
        ]
    return []


def compute_farmer(f):
    """Compute score, segment, and loan for a farmer if not already done."""
    if f.get("score") is None:
        score, details = calculate_score(f["area"], f["yield_t"], f["revenue"],
                                         f["financial_access"], f["cooperative"],
                                         f["region"], f.get("crop", ""))
        f["score"] = score
        f["details"] = details
        seg_label, _, _ = get_segment(score)
        f["segment"] = seg_label[0]
        f["loan"] = estimate_loan(f["area"], f["yield_t"], f["revenue"],
                                  f["financial_access"], f["cooperative"],
                                  seg_label, f.get("crop", ""))
    return f


# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="header-logo">🌱 CreditWorthy</div>', unsafe_allow_html=True)
    st.caption("Agricultural Credit Platform · Madagascar")
    st.divider()
    page = st.radio("Navigation",
                    ["Registration", "Credit Score", "Lender Portal"],
                    index=["Registration", "Credit Score", "Lender Portal"].index(st.session_state["page"]))
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
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Identity")
            name = st.text_input("Full Name *", placeholder="e.g. Rakoto Jean-Pierre")
            region = st.selectbox("Region", list(REGIONS.keys()))
            crop = st.selectbox("Main Crop", ALL_CROPS)
        with col2:
            st.subheader("Farm Data")
            area = st.number_input("Cultivated Area (hectares) *", min_value=0.1, max_value=100.0, value=1.0, step=0.1)
            yield_t = st.number_input("Estimated Yield (tonnes/ha)", min_value=0.1, max_value=20.0, value=2.0, step=0.1)
            revenue = st.number_input("Estimated Annual Revenue (Ariary)", min_value=0, max_value=50_000_000, value=1_000_000, step=100_000)

        st.subheader("Financial Profile")
        col3, col4 = st.columns(2)
        with col3:
            financial_access = st.selectbox("Financial Access", ["Mobile Money", "Bank Account", "None"])
        with col4:
            cooperative = st.checkbox("Member of an agricultural cooperative")

        submitted = st.form_submit_button("🔍 Calculate Score & Loan Estimate",
                                          use_container_width=True, type="primary")

    if submitted:
        if not name:
            st.error("Please enter a name.")
        else:
            score, details = calculate_score(area, yield_t, revenue, financial_access,
                                             cooperative, region, crop)
            segment_label, color, bg = get_segment(score)
            loan = estimate_loan(area, yield_t, revenue, financial_access,
                                 cooperative, segment_label, crop)
            farmer = {
                "name": name, "region": region, "crop": crop,
                "area": area, "yield_t": yield_t, "revenue": revenue,
                "financial_access": financial_access, "cooperative": cooperative,
                "score": score, "segment": segment_label[0],
                "details": details, "loan": loan,
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
        names = [f["name"] for f in st.session_state["farmers"]]
        choice = st.selectbox("Select a farmer", names)
        if st.button("View Score"):
            farmer = next(f for f in st.session_state["farmers"] if f["name"] == choice)
            farmer = compute_farmer(farmer)
            st.session_state["current_farmer"] = farmer
            st.rerun()
    else:
        farmer = compute_farmer(farmer)
        score = farmer["score"]
        segment_label, color, bg = get_segment(score)
        details = farmer.get("details", {})
        loan = farmer.get("loan")
        offers = get_loan_offers(segment_label, loan["final_amount"]) if loan else []

        # ── Header
        col_info, col_score = st.columns([2, 1])
        with col_info:
            st.markdown(f"### 👤 {farmer['name']}")
            st.caption(f"📍 {farmer['region']} · 🌾 {farmer['crop']} · {farmer['area']} ha · {farmer['financial_access']}")
        with col_score:
            st.markdown(f"<div class='score-big' style='color:{color}'>{score}</div>", unsafe_allow_html=True)
            st.markdown("<div class='score-label'>points out of 100</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='text-align:center;margin-top:8px;'>"
                f"<span style='background:{bg};color:{color};padding:6px 18px;border-radius:20px;"
                f"font-weight:600;font-size:15px;'>Segment {segment_label}</span></div>",
                unsafe_allow_html=True)

        st.divider()
        col_left, col_right = st.columns(2)

        # ── Score breakdown
        with col_left:
            st.subheader("Score Breakdown")
            for criterion, (pts, max_pts) in details.items():
                st.markdown(f"**{criterion}** — {pts}/{max_pts} pts")
                st.progress(pts / max_pts)

            st.subheader("Score Gauge")
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=score,
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": color},
                    "steps": [
                        {"range": [0, 44],  "color": "#fdecea"},
                        {"range": [45, 69], "color": "#fff3dc"},
                        {"range": [70, 100],"color": "#e0f7ee"},
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
                    st.markdown("**Step 1 — Two base approaches (we take the lower):**")
                    st.markdown(f"- 30% of annual revenue → **{int(loan['approach_revenue']):,} Ar**")
                    if loan["harvest_value"] > 0:
                        st.markdown(
                            f"- Harvest value ({farmer['crop']} @ {loan['price_per_kg']:,} Ar/kg) = "
                            f"**{int(loan['harvest_value']):,} Ar** → ¼ = **{int(loan['approach_harvest']):,} Ar**"
                        )
                    st.markdown(f"- ✅ Base = MIN of both → **{int(loan['base_amount']):,} Ar**")
                    st.divider()
                    st.markdown(f"**Step 2 — Segment multiplier ({int(loan['segment_multiplier']*100)}%):**")
                    st.markdown(f"- Amount after segment → **{int(loan['amount_after_segment']):,} Ar**")
                    if loan["bonus_breakdown"]:
                        st.divider()
                        st.markdown("**Step 3 — Bonuses (financial access & cooperative):**")
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
                - Join an agricultural cooperative (+10 pts)
                - Open a mobile money account (+9 pts) or bank account (+15 pts)
                - Increase cultivated area or yield (+up to 30 pts)
                - Grow crops suited to your region (+up to 15 pts)
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

    # Compute all farmers
    farmers = [compute_farmer(f) for f in st.session_state["farmers"]]

    # ── Metrics
    col1, col2, col3, col4 = st.columns(4)
    seg_a = len([f for f in farmers if f.get("segment") == "A"])
    seg_b = len([f for f in farmers if f.get("segment") == "B"])
    seg_c = len([f for f in farmers if f.get("segment") == "C"])
    col1.metric("Total Registered", len(farmers))
    col2.metric("Segment A — Eligible", seg_a)
    col3.metric("Segment B — Conditional", seg_b)
    col4.metric("Segment C — Not Eligible", seg_c)

    st.divider()

    # ── Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_segment = st.multiselect("Filter by Segment", ["A", "B", "C"], default=["A", "B", "C"])
    with col_f2:
        available_regions = list(set(f["region"] for f in farmers))
        filter_region = st.multiselect("Filter by Region", available_regions, default=available_regions)

    filtered = [f for f in farmers
                if f.get("segment", "C") in filter_segment and f["region"] in filter_region]

    def seg_badge(seg):
        return {"A": "🟢 A", "B": "🟡 B", "C": "🔴 C"}.get(seg, "⚪")

    def loan_display(f):
        l = f.get("loan")
        return f"{int(l['final_amount']):,} Ar" if l else "Not eligible"

    df = pd.DataFrame([{
        "Name": f["name"],
        "Region": f["region"],
        "Crop": f["crop"],
        "Area (ha)": f["area"],
        "Score": f["score"],
        "Segment": seg_badge(f.get("segment", "C")),
        "Revenue (Ar)": f"{f['revenue']:,}".replace(",", " "),
        "Est. Loan": loan_display(f),
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
        fd = next(f for f in filtered if f["name"] == choice)
        seg_d, color_d, bg_d = get_segment(fd["score"])
        loan_d = fd.get("loan")

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
                f"<div style='background:{bg_d};border-radius:12px;padding:20px;text-align:center;'>"
                f"<div style='font-size:48px;font-weight:700;color:{color_d};'>{fd['score']}</div>"
                f"<div style='font-size:14px;color:{color_d};font-weight:600;'>Segment {seg_d}</div>"
                f"</div>", unsafe_allow_html=True)
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
