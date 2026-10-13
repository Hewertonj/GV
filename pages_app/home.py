import streamlit as st
from services.vendedor_service import listar_vendedores
from services.pessoas_service import listar_gerentes, listar_coordenadores, listar_parceiros
from services.config_service import listar


# ── Helpers ───────────────────────────────────────────────────────────────────

def _contar(lista, valor=None):
    if valor is None:
        return len(lista)
    return sum(1 for r in lista if r.get("status") == valor)


# ── Render ────────────────────────────────────────────────────────────────────

def render():

    # ── Dados ─────────────────────────────────────────────────────────────────
    todos_v      = listar_vendedores()
    ativos       = _contar(todos_v, "ativo")
    inativos     = _contar(todos_v, "inativo")
    substituidos = _contar(todos_v, "substituído")
    total_v      = _contar(todos_v)
    total_g  = len(listar_gerentes())
    total_c  = len(listar_coordenadores())
    total_p  = len(listar_parceiros())
    total_u  = len(listar("unidades"))

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0E5BB3 0%, #094082 60%, #088012 100%);
        border-radius: 16px;
        padding: 36px 40px 32px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    ">
        <div style="position:absolute;top:-50px;right:-50px;width:240px;height:240px;
                    background:rgba(255,255,255,0.05);border-radius:50%;"></div>
        <div style="position:absolute;bottom:-70px;right:100px;width:180px;height:180px;
                    background:rgba(255,255,255,0.04);border-radius:50%;"></div>
        <div style="color:rgba(255,255,255,0.78);font-size:2.5rem;font-weight:800!important;
                   margin:0 0 10px!important;line-height:1.15;letter-spacing:0.5px;">
            Gestão de Vendedores
        </div>
        <p style="color:rgba(255,255,255,0.78);font-size:1rem;margin:0;">
            Gerencie equipes, vínculos e histórico de vendedores em um só lugar.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Métricas ──────────────────────────────────────────────────────────────
    st.markdown("#### 📊 Visão Geral")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("👥 Vendedores",    total_v)
    m2.metric("🟢 Ativos",        ativos)
    m3.metric("🔴 Inativos",      inativos)
    m4.metric("🟡 Substituídos",  substituidos)
    m5.metric("🏢 Unidades",      total_u)

    st.divider()

    # ── Cards de Módulos ──────────────────────────────────────────────────────
    st.markdown("#### 🧩 Módulos do Sistema")

    modulos = [
        {
            "icon": "👥", "titulo": "Vendedores",
            "desc":  "Cadastro, edição, desativação e substituição de vendedores.",
            "stat":  f"{total_v} cadastrado(s)",
        },
        {
            "icon": "👔", "titulo": "Gerentes",
            "desc":  "Gerencie os gerentes vinculados às equipes de venda.",
            "stat":  f"{total_g} cadastrado(s)",
        },
        {
            "icon": "🧭", "titulo": "Coordenadores",
            "desc":  "Controle os coordenadores responsáveis pelos vendedores.",
            "stat":  f"{total_c} cadastrado(s)",
        },
        {
            "icon": "🤝", "titulo": "Parceiros Internos",
            "desc":  "Gerencie os parceiros internos e seus líderes.",
            "stat":  f"{total_p} cadastrado(s)",
        },
        {
            "icon": "📜", "titulo": "Histórico",
            "desc":  "Consulte o histórico completo de substituições registradas.",
            "stat":  f"{substituidos} substituição(ões)",
        },
        {
            "icon": "⚙️", "titulo": "Configurações",
            "desc":  "Gerencie unidades, ramos e segmentos do sistema.",
            "stat":  f"{total_u} unidade(s)",
        },
    ]

    for i in range(0, len(modulos), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j >= len(modulos):
                break
            m = modulos[i + j]
            with col:
                st.markdown(f"""
                <div style="
                    background:#FFFFFF;
                    border:1px solid #E2E8F0;
                    border-top:4px solid #0E5BB3;
                    border-radius:14px;
                    padding:22px 22px 18px;
                    margin-bottom:12px;
                    height:100%;
                ">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                        <div style="
                            font-size:1.5rem;
                            width:42px;height:42px;
                            background:#0E5BB315;
                            border-radius:10px;
                            display:flex;align-items:center;justify-content:center;
                        ">{m['icon']}</div>
                        <div>
                            <div style="font-weight:700;font-size:0.98rem;color:#0E5BB3;">{m['titulo']}</div>
                            <div style="font-size:0.73rem;color:#888;font-weight:500;">{m['stat']}</div>
                        </div>
                    </div>
                    <p style="font-size:0.84rem;color:#475569;margin:0;line-height:1.55;">{m['desc']}</p>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # ── Distribuição de Status ────────────────────────────────────────────────
    st.markdown("#### 🔍 Distribuição de Status dos Vendedores")

    if total_v > 0:
        col_a, col_b = st.columns([3, 1])

        def _barra(label, valor, total, cor):
            pct = (valor / total * 100) if total > 0 else 0
            return f"""
            <div style="margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;
                            font-size:0.85rem;margin-bottom:5px;
                            color:#374151;font-weight:500;">
                    <span>{label}</span>
                    <span>{valor} &nbsp;({pct:.0f}%)</span>
                </div>
                <div style="background:#E2E8F0;border-radius:99px;height:10px;overflow:hidden;">
                    <div style="width:{pct:.1f}%;height:100%;
                                background:{cor};border-radius:99px;"></div>
                </div>
            </div>"""

        with col_a:
            st.markdown(
                _barra("🟢 Ativos",       ativos,       total_v, "#088012") +
                _barra("🔴 Inativos",     inativos,     total_v, "#EF4444") +
                _barra("🟡 Substituídos", substituidos, total_v, "#F59E0B"),
                unsafe_allow_html=True,
            )

        with col_b:
            st.markdown(f"""
            <div style="
                background:linear-gradient(135deg,#0E5BB3,#2179D9);
                border-radius:12px;padding:24px 20px;
                text-align:center;color:white;
            ">
                <div style="font-size:2.6rem;font-weight:800;">{total_v}</div>
                <div style="font-size:0.82rem;opacity:0.85;margin-top:4px;">Vendedores cadastrados</div>
                <div style="font-size:0.72rem;opacity:0.65;margin-top:10px;line-height:1.7;">
                    {ativos} ativos<br>{inativos} inativos<br>{substituidos} substit.
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhum vendedor cadastrado. Use o módulo **Vendedores** para começar.")

    # ── Rodapé ────────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;color:#94A3B8;font-size:0.75rem;
                padding:14px 0 2px;border-top:1px solid #E2E8F0;">
        v3 · Gestão de Vendedores ·
    </div>
    """, unsafe_allow_html=True)
