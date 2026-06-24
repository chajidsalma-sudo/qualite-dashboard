import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Contrôle Qualité",
    page_icon="🔬",
    layout="wide"
)

# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
USERS = {"salma.qualite": "Qualite@2026"}

def login():
    st.markdown("""
        <style>
        .login-box {
            max-width: 400px;
            margin: auto;
            padding: 2rem;
            background: #f8f9fa;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align:center;color:#1a3c5e;'>🔬 Contrôle Qualité IA</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;color:#555;'>Connexion au Dashboard</h4>", unsafe_allow_html=True)
    st.markdown("---")

    username = st.text_input("👤 Identifiant")
    password = st.text_input("🔒 Mot de passe", type="password")

    if st.button("Se connecter", use_container_width=True):
        if username in USERS and USERS[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["user"] = username
            st.rerun()
        else:
            st.error("Identifiant ou mot de passe incorrect.")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

# ─────────────────────────────────────────────
# CHARGEMENT DONNÉES
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("Chajid_Salma_Dashboard_Controle_Qualite_Defauts_IA.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["mois"] = df["timestamp"].dt.to_period("M").astype(str)
    return df

df = load_data()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/microscope.png", width=80)
st.sidebar.title("🔬 Contrôle Qualité")
st.sidebar.markdown(f"👤 Connecté : **{st.session_state['user']}**")
st.sidebar.markdown("---")

page = st.sidebar.radio("📂 Navigation", [
    "🏠 Vue Globale",
    "📊 Analyse Détaillée",
    "🔍 Qualité des Données",
    "📋 Tableau Filtrable",
    "📥 Export CSV",
    "💡 Recommandations"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Filtres")
lignes = st.sidebar.multiselect("Ligne de production", df["ligne"].unique(), default=list(df["ligne"].unique()))
shifts = st.sidebar.multiselect("Shift", df["shift"].unique(), default=list(df["shift"].unique()))
produits = st.sidebar.multiselect("Produit", df["produit"].unique(), default=list(df["produit"].unique()))

df_f = df[df["ligne"].isin(lignes) & df["shift"].isin(shifts) & df["produit"].isin(produits)]

if df_f.empty:
    st.warning("⚠️ Aucun résultat disponible pour les filtres sélectionnés.")
    st.stop()

if st.sidebar.button("🚪 Déconnexion"):
    st.session_state["logged_in"] = False
    st.rerun()

# ─────────────────────────────────────────────
# PAGE 1 : VUE GLOBALE
# ─────────────────────────────────────────────
if page == "🏠 Vue Globale":
    st.title("🏠 Vue Globale – KPIs Principaux")
    st.markdown("---")

    total = len(df_f)
    defauts = df_f["defaut_detecte"].sum()
    taux_defaut = round(defauts / total * 100, 2) if total > 0 else 0
    precision_ia = round(df_f["confiance_ia_pct"].mean(), 2)
    taux_rejet = round(df_f[df_f["decision"] == "Rejet"].shape[0] / total * 100, 2)
    cout_total = round(df_f["cout_non_qualite_mad"].sum(), 2)
    defauts_par_ligne = df_f.groupby("ligne")["defaut_detecte"].sum().max()

    col1, col2, col3 = st.columns(3)
    col1.metric("🔩 Pièces inspectées", f"{total:,}")
    col2.metric("❌ Taux de défaut", f"{taux_defaut} %")
    col3.metric("🤖 Précision IA moyenne", f"{precision_ia} %")

    col4, col5, col6 = st.columns(3)
    col4.metric("🚫 Taux de rejet", f"{taux_rejet} %")
    col5.metric("💰 Coût non qualité (MAD)", f"{cout_total:,.2f}")
    col6.metric("📍 Max défauts / ligne", f"{int(defauts_par_ligne)}")

    st.markdown("---")

    # Évolution temporelle
    st.subheader("📈 Évolution temporelle du taux de défaut")
    evo = df_f.groupby("mois").apply(lambda x: round(x["defaut_detecte"].sum() / len(x) * 100, 2)).reset_index()
    evo.columns = ["Mois", "Taux de défaut (%)"]
    fig = px.line(evo, x="Mois", y="Taux de défaut (%)", markers=True, color_discrete_sequence=["#e63946"])
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# PAGE 2 : ANALYSE DÉTAILLÉE
# ─────────────────────────────────────────────
elif page == "📊 Analyse Détaillée":
    st.title("📊 Analyse Détaillée")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏭 Top 10 lignes par défauts")
        top_lignes = df_f.groupby("ligne")["defaut_detecte"].sum().nlargest(10).reset_index()
        fig = px.bar(top_lignes, x="defaut_detecte", y="ligne", orientation="h",
                     color="defaut_detecte", color_continuous_scale="Reds")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📦 Défauts par produit")
        prod = df_f.groupby("produit")["defaut_detecte"].sum().reset_index()
        fig = px.pie(prod, names="produit", values="defaut_detecte", hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("🔄 Défauts par shift")
        shift_data = df_f.groupby("shift")["defaut_detecte"].sum().reset_index()
        fig = px.bar(shift_data, x="shift", y="defaut_detecte",
                     color="shift", color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.subheader("🔬 Type de défaut")
        type_def = df_f[df_f["defaut_detecte"] == True]["type_defaut"].value_counts().reset_index()
        type_def.columns = ["Type", "Nombre"]
        fig = px.bar(type_def, x="Type", y="Nombre", color="Type",
                     color_discrete_sequence=px.colors.qualitative.Bold)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🔗 Relation Score Qualité vs Confiance IA")
    fig = px.scatter(df_f.sample(min(500, len(df_f))), x="confiance_ia_pct", y="score_qualite",
                     color="decision", opacity=0.6,
                     color_discrete_map={"Accepté": "#2ecc71", "Rejet": "#e74c3c"})
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# PAGE 3 : QUALITÉ DES DONNÉES
# ─────────────────────────────────────────────
elif page == "🔍 Qualité des Données":
    st.title("🔍 Qualité des Données")
    st.markdown("---")

    st.subheader("🕳️ Valeurs manquantes")
    missing = df_f.isnull().sum().reset_index()
    missing.columns = ["Colonne", "Valeurs manquantes"]
    st.dataframe(missing, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Doublons")
    doublons = df_f.duplicated().sum()
    st.metric("Nombre de doublons", doublons)

    st.markdown("---")
    st.subheader("🌡️ Heatmap de corrélation")
    num_cols = df_f.select_dtypes(include=np.number).columns.tolist()
    corr = df_f[num_cols].corr()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    st.pyplot(fig)

# ─────────────────────────────────────────────
# PAGE 4 : TABLEAU FILTRABLE
# ─────────────────────────────────────────────
elif page == "📋 Tableau Filtrable":
    st.title("📋 Tableau Détaillé Filtrable")
    st.markdown("---")

    decision_filter = st.selectbox("Filtrer par décision", ["Tous", "Accepté", "Rejet"])
    if decision_filter != "Tous":
        df_show = df_f[df_f["decision"] == decision_filter]
    else:
        df_show = df_f

    st.dataframe(df_show.reset_index(drop=True), use_container_width=True)
    st.info(f"📊 {len(df_show)} lignes affichées")

# ─────────────────────────────────────────────
# PAGE 5 : EXPORT CSV
# ─────────────────────────────────────────────
elif page == "📥 Export CSV":
    st.title("📥 Export des Données Filtrées")
    st.markdown("---")

    st.dataframe(df_f.head(20), use_container_width=True)

    csv = df_f.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Télécharger le CSV filtré",
        data=csv,
        file_name="export_qualite_filtré.csv",
        mime="text/csv"
    )

# ─────────────────────────────────────────────
# PAGE 6 : RECOMMANDATIONS
# ─────────────────────────────────────────────
elif page == "💡 Recommandations":
    st.title("💡 Recommandations Métier")
    st.markdown("---")

    taux_defaut = round(df_f["defaut_detecte"].sum() / len(df_f) * 100, 2)
    precision_ia = round(df_f["confiance_ia_pct"].mean(), 2)
    ligne_critique = df_f.groupby("ligne")["defaut_detecte"].sum().idxmax()
    cout_total = round(df_f["cout_non_qualite_mad"].sum(), 2)

    st.markdown(f"""
    ### 📌 Analyse automatique

    - 🔴 Le taux de défaut global est de **{taux_defaut}%**.
      {"⚠️ Ce taux est élevé, une révision du processus est recommandée." if taux_defaut > 10 else "✅ Ce taux est acceptable."}

    - 🤖 La précision moyenne de l'IA est de **{precision_ia}%**.
      {"✅ L'IA performe bien." if precision_ia > 80 else "⚠️ La précision de l'IA nécessite une amélioration."}

    - 🏭 La ligne la plus critique est : **{ligne_critique}**
      → Priorité d'intervention recommandée.

    - 💰 Le coût total de non-qualité est de **{cout_total:,.2f} MAD**
      → Réduire les rejets permettrait d'économiser significativement.

    ### 🛠️ Actions recommandées
    1. Auditer la ligne **{ligne_critique}** en priorité.
    2. Renforcer la calibration des caméras IA.
    3. Analyser les shifts avec le plus haut taux de rejet.
    4. Mettre en place un suivi hebdomadaire des KPIs.
    """)
