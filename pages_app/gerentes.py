import streamlit as st
from services.pessoas_service import (
    listar_gerentes, adicionar_gerente, editar_gerente, excluir_gerente
)

def render():
    st.header("👔 Gerentes")
    tab1, tab2, tab3 = st.tabs(["📋 Listagem", "➕ Novo Gerente", "✏️ Editar / Excluir"])

    # ── Listagem ───────────────────────────────────────────────────────────────
    with tab1:
        gerentes = listar_gerentes()
        if not gerentes:
            st.info("Nenhum gerente cadastrado.")
        else:
            import pandas as pd
            from utils.export import df_para_csv, df_para_excel
            df = pd.DataFrame(gerentes)[["id", "nome", "email"]]
            df.columns = ["ID", "Nome", "E-mail"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            col1, col2 = st.columns(2)
            col1.download_button("⬇️ Exportar CSV",   df_para_csv(df),   "gerentes.csv",   "text/csv")
            col2.download_button("⬇️ Exportar Excel", df_para_excel(df), "gerentes.xlsx",  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ── Novo ───────────────────────────────────────────────────────────────────
    with tab2:
        with st.form("form_novo_gerente", clear_on_submit=True):
            nome  = st.text_input("Nome *")
            email = st.text_input("E-mail *")
            if st.form_submit_button("✅ Salvar"):
                if not nome or not email:
                    st.error("Preencha todos os campos obrigatórios.")
                else:
                    adicionar_gerente(nome, email)
                    st.success(f"Gerente **{nome}** cadastrado com sucesso!")
                    st.rerun()

    # ── Editar / Excluir ───────────────────────────────────────────────────────
    with tab3:
        gerentes = listar_gerentes()
        if not gerentes:
            st.info("Nenhum gerente para editar.")
        else:
            opcoes = {f"{g['nome']} ({g['email']})": g for g in gerentes}
            sel = st.selectbox("Selecione o gerente", list(opcoes.keys()))
            g = opcoes[sel]

            with st.form("form_editar_gerente"):
                nome  = st.text_input("Nome",   value=g["nome"])
                email = st.text_input("E-mail", value=g["email"])
                col1, col2 = st.columns(2)
                salvar  = col1.form_submit_button("💾 Salvar Alterações")
                excluir = col2.form_submit_button("🗑️ Excluir", type="secondary")

            if salvar:
                if not nome or not email:
                    st.error("Preencha todos os campos.")
                else:
                    editar_gerente(g["id"], nome, email)
                    st.success("Gerente atualizado!")
                    st.rerun()
            if excluir:
                try:
                    excluir_gerente(g["id"])
                    st.success("Gerente excluído com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

