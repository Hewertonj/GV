import streamlit as st
import pandas as pd
from services.pessoas_service import (
    listar_coordenadores, adicionar_coordenador, editar_coordenador, excluir_coordenador
)
from utils.export import df_para_csv, df_para_excel

def render():
    st.header("🧭 Coordenadores")
    tab1, tab2, tab3 = st.tabs(["📋 Listagem", "➕ Novo Coordenador", "✏️ Editar / Excluir"])

    with tab1:
        coords = listar_coordenadores()
        if not coords:
            st.info("Nenhum coordenador cadastrado.")
        else:
            df = pd.DataFrame(coords)[["id", "nome", "email"]]
            df.columns = ["ID", "Nome", "E-mail"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            col1, col2 = st.columns(2)
            col1.download_button("⬇️ Exportar CSV",   df_para_csv(df),   "coordenadores.csv",  "text/csv")
            col2.download_button("⬇️ Exportar Excel", df_para_excel(df), "coordenadores.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with tab2:
        with st.form("form_novo_coord", clear_on_submit=True):
            nome  = st.text_input("Nome *")
            email = st.text_input("E-mail *")
            if st.form_submit_button("✅ Salvar"):
                if not nome or not email:
                    st.error("Preencha todos os campos obrigatórios.")
                else:
                    adicionar_coordenador(nome, email)
                    st.success(f"Coordenador **{nome}** cadastrado!")
                    st.rerun()

    with tab3:
        coords = listar_coordenadores()
        if not coords:
            st.info("Nenhum coordenador para editar.")
        else:
            opcoes = {f"{c['nome']} ({c['email']})": c for c in coords}
            sel = st.selectbox("Selecione o coordenador", list(opcoes.keys()))
            c = opcoes[sel]

            with st.form("form_editar_coord"):
                nome  = st.text_input("Nome",   value=c["nome"])
                email = st.text_input("E-mail", value=c["email"])
                col1, col2 = st.columns(2)
                salvar  = col1.form_submit_button("💾 Salvar Alterações")
                excluir = col2.form_submit_button("🗑️ Excluir", type="secondary")

            if salvar:
                if not nome or not email:
                    st.error("Preencha todos os campos.")
                else:
                    editar_coordenador(c["id"], nome, email)
                    st.success("Coordenador atualizado!")
                    st.rerun()
            if excluir:
                try:
                    excluir_coordenador(c["id"])
                    st.success("Coordenador excluído com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

