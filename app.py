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
    .segment-badge {
        display: inline-block;
        padding: 6px 20px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 16px;
        margin: 8px auto;
    }
    .card {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        border: 1px solid #e8f0e8;
        margin-bottom: 16px;
    }
    .offre-card {
        background: #f0faf5;
        border-radius: 10px;
        padding: 16px 20px;
        border: 1px solid #1D9E75;
        margin-bottom: 12px;
    }
    .offre-montant { font-size: 24px; font-weight: 700; color: #1D9E75; }
    .critere-row { display: flex; justify-content: space-between; margin-bottom: 6px; }
    .header-logo { font-size: 28px; font-weight: 800; color: #1D9E75; }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "agriculteurs" not in st.session_state:
    st.session_state["agriculteurs"] = [
        {"nom": "Rakoto Jean-Pierre", "region": "Analamanga", "culture": "Maïs",
         "surface": 2.4, "rendement": 4.2, "revenu": 3200000,
         "mobile_money": "Mobile money", "cooperative": True, "score": 74, "segment": "A"},
        {"nom": "Rasoamanarivo Aina", "region": "Vakinankaratra", "culture": "Riz",
         "surface": 1.1, "rendement": 2.8, "revenu": 1100000,
         "mobile_money": "Mobile money", "cooperative": False, "score": 51, "segment": "B"},
        {"nom": "Randria Miora", "region": "Atsimo-Andrefana", "culture": "Manioc",
         "surface": 0.6, "rendement": 1.5, "revenu": 400000,
         "mobile_money": "Aucun", "cooperative": False, "score": 28, "segment": "C"},
    ]
if "profil_actuel" not in st.session_state:
    st.session_state["profil_actuel"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Inscription"


# ─── LOGIQUE SCORING ───────────────────────────────────────────────────────────
def calculer_score(surface, rendement, revenu, mobile_money, cooperative, region):
    score = 0
    details = {}

    # Critère 1 — Production (25 pts)
    production = surface * rendement
    if production > 10:   p1 = 25
    elif production > 5:  p1 = 18
    elif production > 2:  p1 = 10
    else:                 p1 = 4
    score += p1
    details["Production (surface × rendement)"] = (p1, 25)

    # Critère 2 — Revenu annuel (25 pts)
    if revenu > 5_000_000:   p2 = 25
    elif revenu > 2_000_000: p2 = 18
    elif revenu > 500_000:   p2 = 10
    else:                    p2 = 4
    score += p2
    details["Revenu annuel déclaré"] = (p2, 25)

    # Critère 3 — Accès financier (20 pts)
    if mobile_money == "Compte bancaire": p3 = 20
    elif mobile_money == "Mobile money":  p3 = 12
    else:                                 p3 = 0
    score += p3
    details["Accès financier (mobile/banque)"] = (p3, 20)

    # Critère 4 — Coopérative (15 pts)
    p4 = 15 if cooperative else 0
    score += p4
    details["Membre d'une coopérative"] = (p4, 15)

    # Critère 5 — Bonus région (15 pts)
    bonus_region = {
        "Analamanga": 14, "Vakinankaratra": 13, "Itasy": 12,
        "Bongolava": 11, "Atsimo-Andrefana": 8, "Autre": 9
    }
    p5 = bonus_region.get(region, 10)
    score += p5
    details["Contexte régional (infrastructure, marché)"] = (p5, 15)

    return score, details


def get_segment(score):
    if score >= 70:
        return "A — Éligible", "#1D9E75", "#e0f7ee"
    elif score >= 45:
        return "B — Éligible sous conditions", "#d4830a", "#fff3dc"
    else:
        return "C — Non éligible", "#c0392b", "#fdecea"


def get_offres(segment):
    if "A" in segment:
        return [
            {"institution": "CECAM", "produit": "Crédit intrant",
             "montant": "1 500 000 Ar", "duree": "12 mois", "taux": "14%", "remb": "Fin de récolte"},
            {"institution": "BOA Madagascar", "produit": "Crédit équipement",
             "montant": "5 000 000 Ar", "duree": "36 mois", "taux": "18%", "remb": "Mensualités"},
            {"institution": "MicroCred", "produit": "Fonds de roulement",
             "montant": "800 000 Ar", "duree": "6 mois", "taux": "22%", "remb": "Mobile money"},
        ]
    elif "B" in segment:
        return [
            {"institution": "MicroCred", "produit": "Micro-crédit agricole",
             "montant": "500 000 Ar", "duree": "6 mois", "taux": "24%", "remb": "Mensualités"},
        ]
    else:
        return []


# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="header-logo">🌱 CreditWorthy</div>', unsafe_allow_html=True)
    st.caption("Plateforme de crédit agricole")
    st.divider()
    page = st.radio("Navigation", ["Inscription", "Score de crédit", "Portail prêteur"],
                    index=["Inscription", "Score de crédit", "Portail prêteur"].index(st.session_state["page"]))
    st.session_state["page"] = page
    st.divider()
    st.caption(f"👥 {len(st.session_state['agriculteurs'])} agriculteurs enregistrés")
    scored = [a for a in st.session_state["agriculteurs"] if a.get("score")]
    st.caption(f"✅ {len(scored)} profils scorés")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — INSCRIPTION
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["page"] == "Inscription":
    st.title("Inscription Agriculteur")
    st.caption("Remplissez le formulaire pour générer votre score de crédit")

    with st.form("inscription_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Identité")
            nom = st.text_input("Nom complet *", placeholder="Ex: Rakoto Jean-Pierre")
            region = st.selectbox("Région", [
                "Analamanga", "Vakinankaratra", "Itasy",
                "Bongolava", "Atsimo-Andrefana", "Autre"
            ])
            culture = st.selectbox("Culture principale", [
                "Maïs", "Riz", "Légumes", "Manioc", "Élevage", "Autre"
            ])

        with col2:
            st.subheader("Exploitation")
            surface = st.number_input("Surface cultivée (hectares) *", min_value=0.1, max_value=100.0,
                                       value=1.0, step=0.1)
            rendement = st.number_input("Rendement estimé (tonnes/ha)", min_value=0.1, max_value=20.0,
                                         value=2.0, step=0.1)
            revenu = st.number_input("Revenu annuel estimé (Ariary)", min_value=0,
                                      max_value=50_000_000, value=1_000_000, step=100_000)

        st.subheader("Situation financière")
        col3, col4 = st.columns(2)
        with col3:
            mobile_money = st.selectbox("Accès financier", ["Mobile money", "Compte bancaire", "Aucun"])
        with col4:
            cooperative = st.checkbox("Membre d'une coopérative agricole")

        submitted = st.form_submit_button("🔍 Calculer mon score de crédit", use_container_width=True,
                                           type="primary")

    if submitted:
        if not nom:
            st.error("Veuillez entrer un nom.")
        else:
            score, details = calculer_score(surface, rendement, revenu, mobile_money, cooperative, region)
            segment_label, color, bg = get_segment(score)
            profil = {
                "nom": nom, "region": region, "culture": culture,
                "surface": surface, "rendement": rendement, "revenu": revenu,
                "mobile_money": mobile_money, "cooperative": cooperative,
                "score": score, "segment": segment_label[0], "details": details
            }
            st.session_state["profil_actuel"] = profil
            # Ajouter à la liste si pas déjà présent
            noms_existants = [a["nom"] for a in st.session_state["agriculteurs"]]
            if nom not in noms_existants:
                st.session_state["agriculteurs"].append(profil)
            st.success(f"✅ Profil créé ! Score calculé : {score}/100")
            st.session_state["page"] = "Score de crédit"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — SCORE DE CRÉDIT
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state["page"] == "Score de crédit":
    st.title("Score de Crédit")

    profil = st.session_state.get("profil_actuel")

    if profil is None:
        # Permettre de choisir un profil existant
        st.info("Aucun profil actif. Choisissez un agriculteur ou inscrivez-en un nouveau.")
        noms = [a["nom"] for a in st.session_state["agriculteurs"]]
        choix = st.selectbox("Sélectionner un agriculteur", noms)
        if st.button("Voir le score"):
            profil = next(a for a in st.session_state["agriculteurs"] if a["nom"] == choix)
            if "details" not in profil:
                score, details = calculer_score(
                    profil["surface"], profil["rendement"], profil["revenu"],
                    profil["mobile_money"], profil["cooperative"], profil["region"]
                )
                profil["score"] = score
                profil["details"] = details
            st.session_state["profil_actuel"] = profil
            st.rerun()
    else:
        score = profil["score"]
        segment_label, color, bg = get_segment(score)
        details = profil.get("details", {})
        offres = get_offres(segment_label)

        # ── Entête profil
        col_info, col_score = st.columns([2, 1])
        with col_info:
            st.markdown(f"### 👤 {profil['nom']}")
            st.caption(f"📍 {profil['region']} · 🌾 {profil['culture']} · {profil['surface']} ha")

        with col_score:
            st.markdown(f"<div class='score-big' style='color:{color}'>{score}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='score-label'>points sur 100</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='text-align:center;margin-top:8px;'>"
                f"<span style='background:{bg};color:{color};padding:6px 18px;border-radius:20px;"
                f"font-weight:600;font-size:15px;'>Segment {segment_label}</span></div>",
                unsafe_allow_html=True
            )

        st.divider()

        col_left, col_right = st.columns(2)

        # ── Détail des critères
        with col_left:
            st.subheader("Détail du score")
            if details:
                for critere, (pts, max_pts) in details.items():
                    pct = pts / max_pts
                    st.markdown(f"**{critere}** — {pts}/{max_pts} pts")
                    st.progress(pct)
            else:
                st.caption("Détails non disponibles pour ce profil.")

            # Jauge globale
            st.subheader("Jauge globale")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": color},
                    "steps": [
                        {"range": [0, 44], "color": "#fdecea"},
                        {"range": [45, 69], "color": "#fff3dc"},
                        {"range": [70, 100], "color": "#e0f7ee"},
                    ],
                    "threshold": {"line": {"color": color, "width": 4}, "value": score}
                },
                number={"suffix": "/100", "font": {"size": 32}}
            ))
            fig.update_layout(height=250, margin=dict(t=20, b=10, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

        # ── Offres de crédit
        with col_right:
            st.subheader("Offres de crédit disponibles")
            if offres:
                for offre in offres:
                    st.markdown(f"""
                    <div class='offre-card'>
                        <div style='font-size:13px;color:#555;font-weight:600'>{offre['institution']} · {offre['produit']}</div>
                        <div class='offre-montant'>{offre['montant']}</div>
                        <div style='font-size:13px;color:#444;margin-top:6px;'>
                            📅 {offre['duree']} &nbsp;·&nbsp; 📊 Taux {offre['taux']} &nbsp;·&nbsp; 💳 {offre['remb']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ Ce profil n'est pas encore éligible au crédit formel.")
                st.info("""
                **Recommandations pour améliorer le score :**
                - Rejoindre une coopérative agricole
                - Ouvrir un compte mobile money
                - Augmenter la surface cultivée
                - Documenter les ventes via un acheteur formel
                """)

        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("➕ Inscrire un nouvel agriculteur", use_container_width=True):
                st.session_state["profil_actuel"] = None
                st.session_state["page"] = "Inscription"
                st.rerun()
        with col_b:
            if st.button("🏦 Voir le portail prêteur", use_container_width=True):
                st.session_state["page"] = "Portail prêteur"
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — PORTAIL PRÊTEUR
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state["page"] == "Portail prêteur":
    st.title("Portail Prêteur")
    st.caption("Vue des agriculteurs scorés et préqualifiés")

    agriculteurs = st.session_state["agriculteurs"]

    # Recalculer les scores si manquants
    for a in agriculteurs:
        if "score" not in a or a["score"] is None:
            score, details = calculer_score(
                a["surface"], a["rendement"], a["revenu"],
                a["mobile_money"], a["cooperative"], a["region"]
            )
            a["score"] = score
            a["segment"] = get_segment(score)[0][0]

    # ── Métriques
    col1, col2, col3, col4 = st.columns(4)
    total = len(agriculteurs)
    seg_a = len([a for a in agriculteurs if a.get("segment") == "A"])
    seg_b = len([a for a in agriculteurs if a.get("segment") == "B"])
    seg_c = len([a for a in agriculteurs if a.get("segment") == "C"])
    col1.metric("Total inscrits", total)
    col2.metric("Segment A — Éligibles", seg_a)
    col3.metric("Segment B — Conditionnel", seg_b)
    col4.metric("Segment C — Non éligibles", seg_c)

    st.divider()

    # ── Filtres
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtre_segment = st.multiselect("Filtrer par segment", ["A", "B", "C"], default=["A", "B", "C"])
    with col_f2:
        regions_dispo = list(set(a["region"] for a in agriculteurs))
        filtre_region = st.multiselect("Filtrer par région", regions_dispo, default=regions_dispo)

    # ── Tableau
    data_filtree = [
        a for a in agriculteurs
        if a.get("segment", "C") in filtre_segment and a["region"] in filtre_region
    ]

    def badge_segment(seg):
        colors = {"A": "🟢", "B": "🟡", "C": "🔴"}
        return f"{colors.get(seg, '⚪')} Segment {seg}"

    df = pd.DataFrame([{
        "Nom": a["nom"],
        "Région": a["region"],
        "Culture": a["culture"],
        "Surface (ha)": a["surface"],
        "Score": a["score"],
        "Segment": badge_segment(a.get("segment", "C")),
        "Revenu (Ar)": f"{a['revenu']:,}".replace(",", " "),
    } for a in data_filtree])

    if df.empty:
        st.info("Aucun agriculteur ne correspond aux filtres sélectionnés.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={"Score": st.column_config.ProgressColumn(
                         "Score", min_value=0, max_value=100, format="%d/100")})

    st.divider()

    # ── Fiche détaillée
    st.subheader("Fiche détaillée")
    noms_filtres = [a["nom"] for a in data_filtree]
    if noms_filtres:
        choix = st.selectbox("Sélectionner un agriculteur", noms_filtres)
        profil_detail = next(a for a in data_filtree if a["nom"] == choix)
        score_d = profil_detail["score"]
        seg_label, color_d, bg_d = get_segment(score_d)
        offres_d = get_offres(seg_label)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown(f"**Nom :** {profil_detail['nom']}")
            st.markdown(f"**Région :** {profil_detail['region']}")
            st.markdown(f"**Culture :** {profil_detail['culture']}")
            st.markdown(f"**Surface :** {profil_detail['surface']} ha")
            st.markdown(f"**Revenu annuel :** {profil_detail['revenu']:,} Ar".replace(",", " "))
            st.markdown(f"**Mobile money :** {profil_detail['mobile_money']}")
            st.markdown(f"**Coopérative :** {'Oui' if profil_detail['cooperative'] else 'Non'}")
        with col_d2:
            st.markdown(
                f"<div style='background:{bg_d};border-radius:12px;padding:20px;text-align:center;'>"
                f"<div style='font-size:48px;font-weight:700;color:{color_d};'>{score_d}</div>"
                f"<div style='font-size:14px;color:{color_d};font-weight:600;'>Segment {seg_label}</div>"
                f"</div>", unsafe_allow_html=True
            )
            if offres_d:
                st.success(f"✅ {len(offres_d)} offre(s) disponible(s)")
                for o in offres_d:
                    st.markdown(f"- **{o['institution']}** · {o['montant']} · {o['duree']} · {o['taux']}")
            else:
                st.error("Aucune offre disponible pour ce profil.")

        if st.button("📊 Voir le score complet de cet agriculteur", use_container_width=True):
            st.session_state["profil_actuel"] = profil_detail
            st.session_state["page"] = "Score de crédit"
            st.rerun()