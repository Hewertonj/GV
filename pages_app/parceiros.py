import streamlit as st
import pandas as pd
from services.pessoas_service import (
    listar_lideres,   adicionar_lider,    editar_lider,    excluir_lider,
    listar_parceiros, adicionar_parceiro, editar_parceiro, excluir_parceiro,
    opcoes_lideres
)
from utils.export import df_para_csv, df_para_excel

def render():
    st.header("🤝 Parceiros Internos")
    tab_p, tab_l = st.tabs(["🤝 Parceiros", "🏅 Líderes de Parceiros"])

    # ── Parceiros Internos ─────────────────────────────────────────────────────
    with tab_p:
        sub1, sub2, sub3 = st.tabs(["📋 Listagem", "➕ Novo Parceiro", "✏️ Editar / Excluir"])

        with sub1:
            parceiros = listar_parceiros()
            if not parceiros:
                st.info("Nenhum parceiro interno cadastrado.")
            else:
                df = pd.DataFrame(parceiros)[["id","nome","email","lider_nome","lider_email"]]
                df.columns = ["ID","Nome","E-mail","Líder","E-mail Líder"]
                st.dataframe(df, use_container_width=True, hide_index=True)
                col1, col2 = st.columns(2)
                col1.download_button("⬇️ CSV",   df_para_csv(df),   "parceiros.csv",  "text/csv")
                col2.download_button("⬇️ Excel", df_para_excel(df), "parceiros.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with sub2:
            lideres_op = opcoes_lideres()
            if not lideres_op:
                st.warning("Cadastre ao menos um líder antes de adicionar parceiros.")
            else:
                with st.form("form_novo_parceiro", clear_on_submit=True):
                    nome     = st.text_input("Nome do Parceiro *")
                    email    = st.text_input("E-mail do Parceiro *")
                    lider_sel = st.selectbox("Líder *", list(lideres_op.keys()))
                    if st.form_submit_button("✅ Salvar"):
                        if not nome or not email:
                            st.error("Preencha todos os campos.")
                        else:
                            adicionar_parceiro(nome, email, lideres_op[lider_sel])
                            st.success(f"Parceiro **{nome}** cadastrado!")
                            st.rerun()

        with sub3:
            parceiros = listar_parceiros()
            if not parceiros:
                st.info("Nenhum parceiro para editar.")
            else:
                lideres_op = opcoes_lideres()
                opcoes = {f"{p['nome']} ({p['email']})": p for p in parceiros}
                sel = st.selectbox("Selecione o parceiro", list(opcoes.keys()), key="sel_parc_edit")
                p = opcoes[sel]

                lider_atual = next((k for k, v in lideres_op.items() if v == p.get("lider_id")), list(lideres_op.keys())[0] if lideres_op else None)

                with st.form("form_editar_parceiro"):
                    nome      = st.text_input("Nome",   value=p["nome"])
                    email     = st.text_input("E-mail", value=p["email"])
                    lider_sel = st.selectbox("Líder", list(lideres_op.keys()),
                                            index=list(lideres_op.keys()).index(lider_atual) if lider_atual in lideres_op else 0)
                    col1, col2 = st.columns(2)
                    salvar  = col1.form_submit_button("💾 Salvar")
                    excluir = col2.form_submit_button("🗑️ Excluir", type="secondary")

                if salvar:
                    editar_parceiro(p["id"], nome, email, lideres_op[lider_sel])
                    st.success("Parceiro atualizado!")
                    st.rerun()
                if excluir:
                    try:
                        excluir_parceiro(p["id"])
                        st.success("Parceiro excluído com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # ── Líderes ────────────────────────────────────────────────────────────────
    with tab_l:
        sub1, sub2, sub3 = st.tabs(["📋 Listagem", "➕ Novo Líder", "✏️ Editar / Excluir"])

        with sub1:
            lideres = listar_lideres()
            if not lideres:
                st.info("Nenhum líder cadastrado.")
            else:
                df = pd.DataFrame(lideres)[["id","nome","email"]]
                df.columns = ["ID","Nome","E-mail"]
                st.dataframe(df, use_container_width=True, hide_index=True)

        with sub2:
            with st.form("form_novo_lider", clear_on_submit=True):
                nome  = st.text_input("Nome do Líder *")
                email = st.text_input("E-mail do Líder *")
                if st.form_submit_button("✅ Salvar"):
                    if not nome or not email:
                        st.error("Preencha todos os campos.")
                    else:
                        adicionar_lider(nome, email)
                        st.success(f"Líder **{nome}** cadastrado!")
                        st.rerun()

        with sub3:
            lideres = listar_lideres()
            if not lideres:
                st.info("Nenhum líder para editar.")
            else:
                opcoes = {f"{l['nome']} ({l['email']})": l for l in lideres}
                sel = st.selectbox("Selecione o líder", list(opcoes.keys()), key="sel_lider_edit")
                l = opcoes[sel]

                with st.form("form_editar_lider"):
                    nome  = st.text_input("Nome",   value=l["nome"])
                    email = st.text_input("E-mail", value=l["email"])
                    col1, col2 = st.columns(2)
                    salvar  = col1.form_submit_button("💾 Salvar")
                    excluir = col2.form_submit_button("🗑️ Excluir", type="secondary")

                if salvar:
                    editar_lider(l["id"], nome, email)
                    st.success("Líder atualizado!")
                    st.rerun()
                if excluir:
                    try:
                        excluir_lider(l["id"])
                        st.success("Líder excluído com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

