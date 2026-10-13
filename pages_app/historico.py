import streamlit as st
import pandas as pd
from database.connection import get_connection
from utils.export import df_para_csv, df_para_excel

def render():
    st.header("📜 Histórico de Substituições")

    conn = get_connection()
    rows = conn.execute("""
        SELECT
            h.id,
            vs.nome  AS vendedor_saindo,
            vs.email AS email_saindo,
            ve.nome  AS vendedor_entrando,
            ve.email AS email_entrando,
            h.data_substituicao,
            h.motivo,
            u.nome   AS unidade,
            g.nome   AS gerente
        FROM historico_substituicoes h
        LEFT JOIN vendedores vs ON h.vendedor_saindo_id   = vs.id
        LEFT JOIN vendedores ve ON h.vendedor_entrando_id = ve.id
        LEFT JOIN unidades    u  ON ve.unidade_id          = u.id
        LEFT JOIN gerentes    g  ON ve.gerente_id          = g.id
        ORDER BY h.data_substituicao DESC
    """).fetchall()
    conn.close()

    if not rows:
        st.info("Nenhuma substituição registrada ainda.")
        return

    df = pd.DataFrame([dict(r) for r in rows])

    # ── Filtros ────────────────────────────────────────────────────────────────
    st.subheader("Filtros")
    col1, col2, col3 = st.columns(3)

    unidades = ["Todas"] + sorted(df["unidade"].dropna().unique().tolist())
    gerentes = ["Todos"] + sorted(df["gerente"].dropna().unique().tolist())
    uni_f = col1.selectbox("Unidade", unidades, key="hist_uni")
    ger_f = col2.selectbox("Gerente", gerentes, key="hist_ger")

    datas = pd.to_datetime(df["data_substituicao"], errors="coerce")
    min_d = datas.min().date() if not datas.isna().all() else None
    max_d = datas.max().date() if not datas.isna().all() else None

    if min_d and max_d:
        periodo = col3.date_input("Período", value=(min_d, max_d), key="hist_per")
        if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
            df = df[
                (pd.to_datetime(df["data_substituicao"]) >= pd.Timestamp(periodo[0])) &
                (pd.to_datetime(df["data_substituicao"]) <= pd.Timestamp(periodo[1]))
            ]

    if uni_f != "Todas":
        df = df[df["unidade"] == uni_f]
    if ger_f != "Todos":
        df = df[df["gerente"] == ger_f]

    st.divider()
    st.caption(f"**{len(df)}** substituição(ões) encontrada(s)")

    colunas = {
        "data_substituicao": "Data",
        "vendedor_saindo":   "Vendedor Saindo",
        "email_saindo":      "E-mail Saindo",
        "vendedor_entrando": "Vendedor Entrando",
        "email_entrando":    "E-mail Entrando",
        "unidade":           "Unidade",
        "gerente":           "Gerente",
        "motivo":            "Motivo",
    }
    df_show = df[[c for c in colunas if c in df.columns]].rename(columns=colunas)
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    col1.download_button("⬇️ Exportar CSV",   df_para_csv(df_show),   "historico.csv",  "text/csv")
    col2.download_button("⬇️ Exportar Excel", df_para_excel(df_show), "historico.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
