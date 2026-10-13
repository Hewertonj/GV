import streamlit as st
from database.connection import init_db

# ── Inicialização do banco de dados ───────────────────────────────────────────
init_db()

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Gestão de Vendedores",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Customizado ───────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Importação de Fonte ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Variáveis de Cor (Tema Claro) ── */
:root {
    --primary:      #0E5BB3;
    --primary-light:#2179D9;
    --accent:       #088012;
    --accent-glow:  rgba(14, 91, 179, 0.15);
    --bg:           #EDF7F6;
    --surface:      #FFFFFF;
    --surface2:     #E0EFEF;
    --border:       #C1DFDE;
    --text:         #0F172A;
    --text-muted:   #64748B;
    --success:      #088012;
    --warning:      #F59E0B;
    --danger:       #EF4444;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0E5BB3 0%, #094082 100%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}
[data-testid="stSidebar"] * {
    color: #F8FAFC !important;
}
[data-testid="stSidebar"] .stRadio label {
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 10px;
    padding: 12px 16px;
    margin: 6px 0;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
    font-size: 0.95rem;
}
[data-testid="stSidebar"] .stRadio label > div:first-child {
    display: none !important;
}
[data-testid="stSidebar"] .stRadio label p {
    margin: 0 !important;
    padding: 0 !important;
    font-size: 0.95rem !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255, 255, 255, 0.18);
    border-color: rgba(255, 255, 255, 0.35);
    transform: translateX(4px);
}
[data-testid="stSidebar"] .stRadio [data-checked="true"] + label,
[data-testid="stSidebar"] .stRadio label[data-checked="true"] {
    background: #088012 !important;
    border-color: #0A9E17 !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

/* ── Conteúdo principal ── */
.main .block-container {
    padding: 2rem 2.5rem 3rem;
    max-width: 1400px;
}

/* ── Cabeçalhos ── */
h1 { font-size: 1.8rem !important; font-weight: 700 !important; color: var(--primary) !important; }
h2 { font-size: 1.4rem !important; font-weight: 600 !important; color: #1E293B !important; }
h3 { font-size: 1.1rem !important; font-weight: 500 !important; color: var(--text-muted) !important; }

/* ── Botões primários ── */
.stButton > button[kind="primary"],
.stDownloadButton > button {
    background: linear-gradient(135deg, var(--primary), var(--primary-light)) !important;
    border: none !important;
    border-radius: 8px !important;
    color: #fff !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px var(--accent-glow) !important;
}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 18px rgba(5, 1, 79, 0.3) !important;
}

/* ── Botões secundários ── */
.stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-muted) !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--danger) !important;
    color: var(--danger) !important;
    background: #FEF2F2 !important;
}

/* ── Inputs ── */
.stTextInput input, .stSelectbox select, .stTextArea textarea, .stDateInput input {
    background: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface2) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stTabs [aria-selected="true"] {
    background: var(--primary) !important;
    color: white !important;
}

/* ── Métricas ── */
[data-testid="stMetric"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem 1.5rem !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px) !important;
    border-color: var(--primary) !important;
    box-shadow: 0 4px 12px rgba(5, 1, 79, 0.08) !important;
}
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 0.85rem !important; }
[data-testid="stMetricValue"] { color: var(--primary) !important; font-weight: 700 !important; }

/* ── Alertas ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left-width: 4px !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Sidebar title ── */
.sidebar-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #fff;
    padding: 0.5rem 0 1rem;
    letter-spacing: 0.5px;
}
.sidebar-version {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.6);
    margin-top: 1rem;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ── Importação das páginas ─────────────────────────────────────────────────────
from pages_app import (
    home, vendedores, gerentes, coordenadores,
    parceiros, configuracoes, historico, operacoes_massa
)

# ── Navegação Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">👥 Gestão de Vendedores</div>', unsafe_allow_html=True)
    st.divider()

    pagina = st.radio(
        "Navegação",
        options=[
            "🏠  Início",
            "👥  Vendedores",
            "👔  Gerentes",
            "🧭  Coordenadores",
            "🤝  Parceiros Internos",
            "📜  Histórico",
            "📦  Operações em Massa",
            "⚙️  Configurações",
        ],
        label_visibility="collapsed",
        key="nav_radio",
    )

    st.markdown('<div class="sidebar-version">v1.0 · SQLite + Streamlit</div>', unsafe_allow_html=True)

# ── Roteamento ─────────────────────────────────────────────────────────────────
if   "Início"              in pagina: home.render()
elif "Vendedores"          in pagina: vendedores.render()
elif "Gerentes"            in pagina: gerentes.render()
elif "Coordenadores"       in pagina: coordenadores.render()
elif "Parceiros"           in pagina: parceiros.render()
elif "Histórico"           in pagina: historico.render()
elif "Operações em Massa"  in pagina: operacoes_massa.render()
elif "Configurações"       in pagina: configuracoes.render()
