import streamlit as st
import pandas as pd
from services.config_service import listar, adicionar, editar, excluir
from services.email_service import (
    obter_config_smtp,
    salvar_config_smtp,
    listar_destinatarios,
    adicionar_destinatario,
    editar_destinatario,
    excluir_destinatario,
    enviar_email_teste,
)

TABELAS = {
    "🏢 Unidades":   "unidades",
    "🌿 Ramos":      "ramos",
    "📊 Segmentos":  "segmentos",
}

def _crud_tabela(label: str, tabela: str):
    sub1, sub2, sub3 = st.tabs(["📋 Listagem", "➕ Adicionar", "✏️ Editar / Excluir"])

    with sub1:
        rows = listar(tabela)
        if not rows:
            st.info(f"Nenhum(a) {label.split()[-1].lower()} cadastrado(a).")
        else:
            df = pd.DataFrame(rows)[["id", "nome"]]
            df.columns = ["ID", "Nome"]
            st.dataframe(df, use_container_width=True, hide_index=True)

    with sub2:
        with st.form(f"form_add_{tabela}", clear_on_submit=True):
            nome = st.text_input(f"Nome *")
            if st.form_submit_button("✅ Adicionar"):
                if not nome:
                    st.error("Informe um nome.")
                else:
                    adicionar(tabela, nome)
                    st.success(f"**{nome}** adicionado(a)!")
                    st.rerun()

    with sub3:
        rows = listar(tabela)
        if not rows:
            st.info("Nada para editar.")
        else:
            opcoes = {r["nome"]: r["id"] for r in rows}
            sel = st.selectbox("Selecione", list(opcoes.keys()), key=f"sel_{tabela}")
            id_ = opcoes[sel]

            with st.form(f"form_edit_{tabela}"):
                novo_nome = st.text_input("Novo nome", value=sel)
                col1, col2 = st.columns(2)
                salvar  = col1.form_submit_button("💾 Salvar")
                excluir_btn = col2.form_submit_button("🗑️ Excluir", type="secondary")

            if salvar:
                editar(tabela, id_, novo_nome)
                st.success("Atualizado!")
                st.rerun()
            if excluir_btn:
                excluir(tabela, id_)
                st.success("Excluído.")
                st.rerun()


def _tab_notificacoes():
    st.subheader("📧 Notificações Automáticas por E-mail")
    st.caption("Configure os destinatários de alertas e os parâmetros de envio SMTP para movimentações do sistema.")

    tab_dest, tab_smtp, tab_teste = st.tabs([
        "👥 Destinatários de Alertas",
        "⚙️ Servidor SMTP",
        "📨 Testar Envio"
    ])

    # ── Subaba 1: Destinatários ───────────────────────────────────────────────
    with tab_dest:
        dest_list, dest_add, dest_edit = st.tabs([
            "📋 Destinatários Cadastrados",
            "➕ Adicionar Destinatário",
            "✏️ Editar / Remover"
        ])

        with dest_list:
            destinatarios = listar_destinatarios()
            if not destinatarios:
                st.info("Nenhum destinatário de e-mail cadastrado. Use a aba **➕ Adicionar Destinatário** para cadastrar.")
            else:
                dados_tabela = []
                for d in destinatarios:
                    dados_tabela.append({
                        "ID": d["id"],
                        "Nome": d["nome"],
                        "E-mail": d["email"],
                        "Status": "✅ Ativo" if d["ativo"] else "❌ Inativo",
                        "Vendedores": "Sim" if d["recebe_vendedor"] else "Não",
                        "Gerentes": "Sim" if d["recebe_gerente"] else "Não",
                        "Coordenadores": "Sim" if d["recebe_coordenador"] else "Não",
                        "Parceiros": "Sim" if d["recebe_parceiro"] else "Não",
                    })
                df_dest = pd.DataFrame(dados_tabela)
                st.dataframe(df_dest, use_container_width=True, hide_index=True)

        with dest_add:
            with st.form("form_add_destinatario", clear_on_submit=True):
                st.write("**Novo Destinatário de Alertas**")
                col_n, col_e = st.columns(2)
                nome = col_n.text_input("Nome Completo *", placeholder="Ex: Diretor Comercial")
                email = col_e.text_input("E-mail *", placeholder="diretoria@empresa.com")

                st.write("##### Eventos a Receber:")
                c1, c2 = st.columns(2)
                rec_vend = c1.checkbox("Vendedores (Cadastros, Inativações, Substituições, Troca de Vínculo)", value=True)
                rec_ger  = c1.checkbox("Gerentes (Cadastros, Edições e Exclusões)", value=True)
                rec_coord = c2.checkbox("Coordenadores (Cadastros, Edições e Exclusões)", value=True)
                rec_parc = c2.checkbox("Parceiros Internos e Líderes (Cadastros, Edições e Exclusões)", value=True)

                if st.form_submit_button("✅ Cadastrar Destinatário"):
                    sucesso, msg = adicionar_destinatario(
                        nome=nome,
                        email=email,
                        recebe_vendedor=rec_vend,
                        recebe_gerente=rec_ger,
                        recebe_coordenador=rec_coord,
                        recebe_parceiro=rec_parc
                    )
                    if sucesso:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        with dest_edit:
            destinatarios = listar_destinatarios()
            if not destinatarios:
                st.info("Nenhum destinatário disponível para edição.")
            else:
                opcoes = {f"{d['nome']} ({d['email']})": d for d in destinatarios}
                sel_label = st.selectbox("Selecione o destinatário", list(opcoes.keys()))
                d_sel = opcoes[sel_label]

                with st.form("form_edit_destinatario"):
                    st.write(f"**Editando: {d_sel['nome']}**")
                    col_en, col_ee = st.columns(2)
                    edit_nome = col_en.text_input("Nome", value=d_sel["nome"])
                    edit_email = col_ee.text_input("E-mail", value=d_sel["email"])

                    edit_ativo = st.checkbox("Destinatário Ativo (recebe notificações)", value=bool(d_sel["ativo"]))

                    st.write("##### Notificações Habilitadas:")
                    ec1, ec2 = st.columns(2)
                    edit_vend = ec1.checkbox("Vendedores (Movimentações e cadastros)", value=bool(d_sel["recebe_vendedor"]))
                    edit_ger  = ec1.checkbox("Gerentes (Cadastros, edições e exclusões)", value=bool(d_sel["recebe_gerente"]))
                    edit_coord = ec2.checkbox("Coordenadores (Cadastros, edições e exclusões)", value=bool(d_sel["recebe_coordenador"]))
                    edit_parc = ec2.checkbox("Parceiros Internos e Líderes (Cadastros, edições e exclusões)", value=bool(d_sel["recebe_parceiro"]))

                    col_b1, col_b2 = st.columns(2)
                    btn_salvar = col_b1.form_submit_button("💾 Salvar Alterações")
                    btn_excluir = col_b2.form_submit_button("🗑️ Excluir Destinatário", type="secondary")

                if btn_salvar:
                    sucesso, msg = editar_destinatario(
                        id_=d_sel["id"],
                        nome=edit_nome,
                        email=edit_email,
                        ativo=edit_ativo,
                        recebe_vendedor=edit_vend,
                        recebe_gerente=edit_ger,
                        recebe_coordenador=edit_coord,
                        recebe_parceiro=edit_parc
                    )
                    if sucesso:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

                if btn_excluir:
                    sucesso, msg = excluir_destinatario(d_sel["id"])
                    if sucesso:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    # ── Subaba 2: Configuração SMTP ───────────────────────────────────────────
    with tab_smtp:
        config_atual = obter_config_smtp()

        with st.form("form_config_smtp"):
            st.write("##### Parâmetros do Servidor SMTP")
            col_srv, col_prt = st.columns([3, 1])
            smtp_server = col_srv.text_input("Servidor SMTP *", value=config_atual.get("smtp_server", ""), placeholder="Ex: smtp.gmail.com")
            smtp_port   = col_prt.number_input("Porta *", min_value=1, max_value=65535, value=int(config_atual.get("smtp_port") or 587))

            col_usr, col_pwd = st.columns(2)
            remetente = col_usr.text_input("E-mail Remetente *", value=config_atual.get("remetente", ""), placeholder="seu-email@gmail.com")
            senha     = col_pwd.text_input("Senha / Senha de App *", value=config_atual.get("senha", ""), type="password", help="Para contas Gmail, utilize uma 'Senha de Aplicativo'.")

            usar_tls  = st.checkbox("Habilitar STARTTLS (Obrigatório para porta 587)", value=bool(config_atual.get("usar_tls", True)), help="Necessário para Gmail, Outlook e outros provedores modernos na porta 587.")

            btn_salvar_smtp = st.form_submit_button("💾 Salvar Configurações SMTP")

        if btn_salvar_smtp:
            sucesso, msg = salvar_config_smtp(smtp_server, smtp_port, remetente, senha, usar_tls)
            if sucesso:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

        with st.expander("ℹ️ Como configurar para Gmail / Google Workspace"):
            st.markdown("""
            O Gmail **não aceita** a senha pessoal da sua conta para envio por SMTP. É obrigatório usar uma **Senha de Aplicativo**:
            
            1. Acesse sua Conta Google: [myaccount.google.com/security](https://myaccount.google.com/security) com a mesma conta do remetente.
            2. Certifique-se de que a **Verificação em duas etapas** está ativada.
            3. Acesse diretamente a página de [Senhas de Aplicativo](https://myaccount.google.com/apppasswords).
            4. Dê um nome ao aplicativo (ex: `Gestão de Vendedores`) e clique em **Criar**.
            5. Copie o código de 16 letras gerado (ex: `abcd efgh ijkl mnop`).
            6. Cole no campo **Senha / Senha de App** acima e clique em **Salvar Configurações SMTP**.
            
            > **Porta e Segurança:**
            > - Para **Porta 587**, mantenha **Habilitar STARTTLS** marcado.
            > - Para **Porta 465**, utiliza-se SSL direto.
            """)

    # ── Subaba 3: Testar Envio ────────────────────────────────────────────────
    with tab_teste:
        st.write("##### Enviar E-mail de Teste")
        st.caption("Verifique se as credenciais e a conectividade com o servidor SMTP estão funcionando corretamente.")

        config_atual = obter_config_smtp()
        email_padrao = config_atual.get("remetente", "")

        with st.form("form_teste_email"):
            email_teste = st.text_input("E-mail de Destino para o Teste *", value=email_padrao, placeholder="destinatario@empresa.com")
            btn_testar = st.form_submit_button("📨 Enviar E-mail de Teste")

        if btn_testar:
            if not email_teste:
                st.error("Informe um e-mail de destino para o teste.")
            else:
                with st.spinner("Conectando ao servidor SMTP e disparando e-mail de teste..."):
                    sucesso, msg = enviar_email_teste(email_teste)
                    if sucesso:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")


def render():
    st.header("⚙️ Configurações")
    st.caption("Gerencie as tabelas auxiliares e as preferências de notificações do sistema.")

    tabs = st.tabs(list(TABELAS.keys()) + ["📧 Notificações"])

    # Renderiza abas das tabelas auxiliares
    for tab, (label, tabela) in zip(tabs[:len(TABELAS)], TABELAS.items()):
        with tab:
            _crud_tabela(label, tabela)

    # Renderiza aba de notificações
    with tabs[-1]:
        _tab_notificacoes()
