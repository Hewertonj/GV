import streamlit as st
import pandas as pd
from datetime import date

from services.vendedor_service import (
    listar_vendedores, buscar_vendedor,
    adicionar_vendedor, editar_vendedor,
    desativar_vendedor, excluir_vendedor,
    registrar_substituicao, _update_status_datas
)
from services.pessoas_service import (
    opcoes_gerentes, opcoes_coordenadores, opcoes_parceiros
)
from services.config_service import opcoes
from utils.export import df_para_csv, df_para_excel

STATUS_CORES = {
    "ativo":        "🟢",
    "inativo":      "🔴",
    "substituído":  "🟡",
}

def _select_or_none(label, opcoes_dict, key=None, index=0):
    """Selectbox que retorna None se não houver opções."""
    if not opcoes_dict:
        st.warning(f"Nenhum(a) {label} cadastrado(a). Acesse Configurações.")
        return None, None
    sel = st.selectbox(label, list(opcoes_dict.keys()), key=key, index=index)
    return sel, opcoes_dict[sel]


def _formulario_vendedor(prefix: str, defaults: dict = None):
    """Formulário reutilizável para cadastro e edição de vendedor."""
    d = defaults or {}

    ger_op   = opcoes_gerentes()
    coo_op   = opcoes_coordenadores()
    par_op   = opcoes_parceiros()
    uni_op   = opcoes("unidades")
    ram_op   = opcoes("ramos")
    seg_op   = opcoes("segmentos")

    nome  = st.text_input("Nome do Vendedor *",  value=d.get("nome", ""),  key=f"{prefix}_nome")
    email = st.text_input("E-mail do Vendedor *", value=d.get("email", ""), key=f"{prefix}_email")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        ger_keys = list(ger_op.keys())
        ger_idx  = ger_keys.index(d["gerente_nome"]) if d.get("gerente_nome") in ger_keys else 0
        ger_sel  = st.selectbox("Gerente *", ger_keys, index=ger_idx, key=f"{prefix}_ger") if ger_keys else None

        coo_keys = list(coo_op.keys())
        coo_idx  = coo_keys.index(d["coordenador_nome"]) if d.get("coordenador_nome") in coo_keys else 0
        coo_sel  = st.selectbox("Coordenador *", coo_keys, index=coo_idx, key=f"{prefix}_coo") if coo_keys else None

        par_keys = list(par_op.keys())
        par_idx  = par_keys.index(d["parceiro_nome"]) if d.get("parceiro_nome") in par_keys else 0
        par_sel  = st.selectbox("Parceiro Interno *", par_keys, index=par_idx, key=f"{prefix}_par") if par_keys else None

    with col2:
        uni_keys = list(uni_op.keys())
        uni_idx  = uni_keys.index(d["unidade_nome"]) if d.get("unidade_nome") in uni_keys else 0
        uni_sel  = st.selectbox("Unidade *", uni_keys, index=uni_idx, key=f"{prefix}_uni") if uni_keys else None

        ram_keys = list(ram_op.keys())
        ram_idx  = ram_keys.index(d["ramo_nome"]) if d.get("ramo_nome") in ram_keys else 0
        ram_sel  = st.selectbox("Ramo *", ram_keys, index=ram_idx, key=f"{prefix}_ram") if ram_keys else None

        seg_keys = list(seg_op.keys())
        seg_idx  = seg_keys.index(d["segmento_nome"]) if d.get("segmento_nome") in seg_keys else 0
        seg_sel  = st.selectbox("Segmento *", seg_keys, index=seg_idx, key=f"{prefix}_seg") if seg_keys else None

    return {
        "nome":  nome,  "email": email,
        "ger_sel": ger_sel,  "ger_op": ger_op,
        "coo_sel": coo_sel,  "coo_op": coo_op,
        "par_sel": par_sel,  "par_op": par_op,
        "uni_sel": uni_sel,  "uni_op": uni_op,
        "ram_sel": ram_sel,  "ram_op": ram_op,
        "seg_sel": seg_sel,  "seg_op": seg_op,
    }


def render():
    st.header("👥 Vendedores")
    tab_list, tab_new, tab_edit, tab_sub = st.tabs([
        "📋 Listagem", "➕ Novo Vendedor", "✏️ Editar", "🔄 Substituição"
    ])

    # ── Listagem ───────────────────────────────────────────────────────────────
    with tab_list:
        st.subheader("Filtros")
        fc1, fc2, fc3, fc4, fc5 = st.columns(5)

        status_f   = fc1.selectbox("Status",    ["Todos", "ativo", "inativo", "substituído"], key="f_status")
        uni_f_op   = {"Todos": None, **opcoes("unidades")}
        ram_f_op   = {"Todos": None, **opcoes("ramos")}
        seg_f_op   = {"Todos": None, **opcoes("segmentos")}
        ger_f_op   = {"Todos": None, **opcoes_gerentes()}

        uni_f  = fc2.selectbox("Unidade",   list(uni_f_op.keys()), key="f_uni")
        ram_f  = fc3.selectbox("Ramo",      list(ram_f_op.keys()), key="f_ram")
        seg_f  = fc4.selectbox("Segmento",  list(seg_f_op.keys()), key="f_seg")
        ger_f  = fc5.selectbox("Gerente",   list(ger_f_op.keys()), key="f_ger")

        vendedores = listar_vendedores(
            status      = None if status_f == "Todos" else status_f,
            unidade_id  = uni_f_op[uni_f],
            gerente_id  = ger_f_op[ger_f],
            ramo_id     = ram_f_op[ram_f],
            segmento_id = seg_f_op[seg_f],
        )

        st.divider()
        if not vendedores:
            st.info("Nenhum vendedor encontrado com os filtros selecionados.")
        else:
            df = pd.DataFrame(vendedores)
            df["Status"] = df["status"].map(lambda s: f"{STATUS_CORES.get(s,'')} {s.capitalize()}")
            colunas = {
                "nome": "Vendedor", "email": "E-mail",
                "gerente": "Gerente", "coordenador": "Coordenador",
                "parceiro": "Parceiro Interno",
                "unidade": "Unidade", "ramo": "Ramo", "segmento": "Segmento",
                "Status": "Status", "data_entrada": "Entrada", "data_saida": "Saída"
            }
            df_show = df[[c for c in colunas if c in df.columns]].rename(columns=colunas)
            st.dataframe(df_show, use_container_width=True, hide_index=True)

            st.caption(f"Total: **{len(vendedores)}** vendedor(es)")
            col1, col2 = st.columns(2)
            col1.download_button("⬇️ Exportar CSV",   df_para_csv(df_show),   "vendedores.csv",  "text/csv")
            col2.download_button("⬇️ Exportar Excel", df_para_excel(df_show), "vendedores.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ── Novo Vendedor ──────────────────────────────────────────────────────────
    with tab_new:
        st.subheader("Cadastrar Novo Vendedor")
        with st.form("form_novo_vendedor"):
            campos = _formulario_vendedor("new")
            data_e = st.date_input("Data de Entrada", value=date.today(), key="new_data")
            if st.form_submit_button("✅ Cadastrar Vendedor"):
                if not campos["nome"] or not campos["email"]:
                    st.error("Nome e e-mail são obrigatórios.")
                elif not all([campos["ger_sel"], campos["coo_sel"], campos["par_sel"],
                              campos["uni_sel"], campos["ram_sel"], campos["seg_sel"]]):
                    st.error("Preencha todos os campos relacionais.")
                else:
                    adicionar_vendedor(
                        nome         = campos["nome"],
                        email        = campos["email"],
                        gerente_id   = campos["ger_op"][campos["ger_sel"]],
                        coordenador_id = campos["coo_op"][campos["coo_sel"]],
                        parceiro_id  = campos["par_op"][campos["par_sel"]],
                        unidade_id   = campos["uni_op"][campos["uni_sel"]],
                        ramo_id      = campos["ram_op"][campos["ram_sel"]],
                        segmento_id  = campos["seg_op"][campos["seg_sel"]],
                        data_entrada = str(data_e),
                    )
                    st.success(f"✅ Vendedor **{campos['nome']}** cadastrado com sucesso!")
                    st.rerun()

    # ── Editar ─────────────────────────────────────────────────────────────────
    with tab_edit:
        st.subheader("Editar Vendedor")

        # Exibe feedback persistente (evita sumir com st.rerun())
        if st.session_state.get("_edit_msg"):
            kind, msg = st.session_state.pop("_edit_msg")
            if kind == "success":
                st.success(msg)
            elif kind == "error":
                st.error(msg)
            elif kind == "warning":
                st.warning(msg)

        todos = listar_vendedores()
        if not todos:
            st.info("Nenhum vendedor cadastrado.")
        else:
            from datetime import datetime as _dt

            opcoes_v = {f"{v['nome']} ({v['status']})": v["id"] for v in todos}
            chaves_v = list(opcoes_v.keys())

            # Selectbox controlado unicamente pela key — sem manipular index
            sel_v = st.selectbox(
                "Selecione o vendedor",
                chaves_v,
                key="edit_sel",
            )

            vid = opcoes_v[sel_v]
            vd  = buscar_vendedor(vid)

            if vd is None:
                st.error("Vendedor não encontrado. Selecione outro.")
                st.stop()

            # Chave dinâmica por vendedor — garante reset dos campos ao trocar
            fk = f"e{vid}"   # prefixo único por vendedor

            # ── Card informativo ────────────────────────────────────────────
            status_icon = STATUS_CORES.get(vd.get("status", ""), "⚪")
            saida_html  = (
                f"&nbsp;·&nbsp; Saída: <b>{vd['data_saida']}</b>"
                if vd.get("data_saida") else ""
            )
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg,#F8FAFC,#EEF2FF);
                border: 1px solid #C7D2FE;
                border-left: 4px solid #05014F;
                border-radius: 10px;
                padding: 14px 18px;
                margin-bottom: 8px;
            ">
                <span style="font-weight:700;font-size:1.05rem;color:#05014F;">{vd.get('nome','')}</span>
                &nbsp;&nbsp;
                <span style="font-size:0.85rem;color:#64748B;">{vd.get('email','')}</span>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <span style="font-size:0.85rem;">{status_icon} <b>{vd.get('status','').capitalize()}</b></span>
                <br/>
                <span style="font-size:0.82rem;color:#64748B;">
                    Gerente: <b>{vd.get('gerente_nome') or '—'}</b>
                    &nbsp;·&nbsp; Coordenador: <b>{vd.get('coordenador_nome') or '—'}</b>
                    &nbsp;·&nbsp; Unidade: <b>{vd.get('unidade_nome') or '—'}</b>
                    &nbsp;·&nbsp; Entrada: <b>{vd.get('data_entrada') or '—'}</b>
                    {saida_html}
                </span>
            </div>
            """, unsafe_allow_html=True)

            # ── Formulário de edição ────────────────────────────────────────
            defaults = {
                "nome":             vd.get("nome", ""),
                "email":            vd.get("email", ""),
                "gerente_nome":     vd.get("gerente_nome", ""),
                "coordenador_nome": vd.get("coordenador_nome", ""),
                "parceiro_nome":    vd.get("parceiro_nome", ""),
                "unidade_nome":     vd.get("unidade_nome", ""),
                "ramo_nome":        vd.get("ramo_nome", ""),
                "segmento_nome":    vd.get("segmento_nome", ""),
            }

            with st.form(f"form_editar_vendedor_{fk}"):
                campos = _formulario_vendedor(fk, defaults)

                st.divider()
                st.markdown("**Informações Adicionais**")
                ec1, ec2, ec3 = st.columns(3)

                # Status editável — permite reativar vendedor inativo
                status_opcoes = ["ativo", "inativo", "substituído"]
                status_atual  = vd.get("status", "ativo")
                status_idx    = status_opcoes.index(status_atual) if status_atual in status_opcoes else 0
                novo_status   = ec1.selectbox(
                    "Status", status_opcoes, index=status_idx, key=f"{fk}_status"
                )

                # Data de entrada editável
                _de_str = vd.get("data_entrada") or str(date.today())
                try:
                    _de_val = _dt.strptime(_de_str, "%Y-%m-%d").date()
                except ValueError:
                    _de_val = date.today()
                nova_data_entrada = ec2.date_input(
                    "Data de Entrada", value=_de_val, key=f"{fk}_data_entrada"
                )

                # Data de saída editável (útil ao reativar ou corrigir)
                _ds_str = vd.get("data_saida")
                _ds_val = None
                if _ds_str:
                    try:
                        _ds_val = _dt.strptime(_ds_str, "%Y-%m-%d").date()
                    except ValueError:
                        pass
                nova_data_saida = ec3.date_input(
                    "Data de Saída (opcional)",
                    value=_ds_val,
                    key=f"{fk}_data_saida",
                )

                st.divider()
                col1, col2, col3 = st.columns(3)
                salvar    = col1.form_submit_button("💾 Salvar Alterações", type="primary")
                desativar = col2.form_submit_button("⏸️ Desativar",          type="secondary")
                excluir_b = col3.form_submit_button("🗑️ Excluir",            type="secondary")

            # ── Processamento fora do form ──────────────────────────────────
            if salvar:
                if not campos["nome"] or not campos["email"]:
                    st.session_state["_edit_msg"] = ("error", "Nome e e-mail são obrigatórios.")
                    st.rerun()
                else:
                    editar_vendedor(
                        id_            = vd["id"],
                        nome           = campos["nome"],
                        email          = campos["email"],
                        gerente_id     = campos["ger_op"].get(campos["ger_sel"]),
                        coordenador_id = campos["coo_op"].get(campos["coo_sel"]),
                        parceiro_id    = campos["par_op"].get(campos["par_sel"]),
                        unidade_id     = campos["uni_op"].get(campos["uni_sel"]),
                        ramo_id        = campos["ram_op"].get(campos["ram_sel"]),
                        segmento_id    = campos["seg_op"].get(campos["seg_sel"]),
                    )
                    _update_status_datas(
                        vd["id"], novo_status,
                        str(nova_data_entrada),
                        str(nova_data_saida) if nova_data_saida else None,
                    )
                    st.session_state["_edit_msg"] = (
                        "success", f"✅ Vendedor **{campos['nome']}** atualizado com sucesso!"
                    )
                    st.rerun()

            # Desativar com confirmação
            if desativar:
                if vd.get("status") == "inativo":
                    st.session_state["_edit_msg"] = ("warning", "Este vendedor já está inativo.")
                    st.rerun()
                else:
                    st.session_state["_confirm_desativar"] = vd["id"]

            if st.session_state.get("_confirm_desativar") == vd["id"]:
                st.warning(
                    f"⚠️ Tem certeza que deseja **desativar** o vendedor **{vd['nome']}**? "
                    "A data de saída será registrada como hoje."
                )
                cc1, cc2, _ = st.columns([1, 1, 4])
                if cc1.button("✅ Confirmar", key="btn_confirm_des", type="primary"):
                    desativar_vendedor(vd["id"])
                    st.session_state.pop("_confirm_desativar", None)
                    st.session_state["_edit_msg"] = ("success", f"✅ Vendedor **{vd['nome']}** desativado.")
                    st.rerun()
                if cc2.button("❌ Cancelar", key="btn_cancel_des"):
                    st.session_state.pop("_confirm_desativar", None)
                    st.rerun()

            # Excluir com confirmação
            if excluir_b:
                st.session_state["_confirm_excluir"] = vd["id"]

            if st.session_state.get("_confirm_excluir") == vd["id"]:
                st.error(
                    f"🗑️ Tem certeza que deseja **excluir permanentemente** o vendedor **{vd['nome']}**? "
                    "Esta ação **não pode ser desfeita**."
                )
                xc1, xc2, _ = st.columns([1, 1, 4])
                if xc1.button("🗑️ Sim, excluir", key="btn_confirm_exc", type="primary"):
                    nome_excluido = vd["nome"]
                    excluir_vendedor(vd["id"])
                    st.session_state.pop("_confirm_excluir", None)
                    st.session_state["_edit_msg"] = ("success", f"🗑️ Vendedor **{nome_excluido}** excluído.")
                    st.rerun()
                if xc2.button("❌ Cancelar", key="btn_cancel_exc"):
                    st.session_state.pop("_confirm_excluir", None)
                    st.rerun()


    # ── Substituição ───────────────────────────────────────────────────────────
    with tab_sub:
        st.subheader("🔄 Registrar Substituição de Vendedor")
        st.caption("O vendedor atual será marcado como **substituído** e o novo será cadastrado com os mesmos vínculos.")

        ativos = listar_vendedores(status="ativo")
        if not ativos:
            st.warning("Não há vendedores ativos para substituir.")
        else:
            opcoes_a = {f"{v['nome']} — {v['unidade'] or 'S/U'} | {v['gerente'] or 'S/G'}": v for v in ativos}
            sel_a = st.selectbox("Vendedor que está saindo *", list(opcoes_a.keys()), key="sub_sel")
            v_saindo = opcoes_a[sel_a]
            vd_saindo = buscar_vendedor(v_saindo["id"])

            # Chave dinâmica por vendedor — garante reset do form e do card ao trocar seleção
            sid = vd_saindo["id"]

            # ── Card informativo do vendedor saindo ─────────────────────────
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg,#FFF7ED,#FEF2F2);
                border: 1px solid #FCA5A5;
                border-left: 4px solid #EF4444;
                border-radius: 10px;
                padding: 14px 18px;
                margin-bottom: 8px;
            ">
                <span style="font-size:0.78rem;font-weight:600;color:#EF4444;text-transform:uppercase;
                             letter-spacing:0.8px;">⬅️ Vendedor Saindo</span><br/>
                <span style="font-weight:700;font-size:1.05rem;color:#7F1D1D;">{vd_saindo['nome']}</span>
                &nbsp;&nbsp;
                <span style="font-size:0.85rem;color:#64748B;">{vd_saindo.get('email','')}</span>
                <br/>
                <span style="font-size:0.82rem;color:#64748B;">
                    Gerente: <b>{vd_saindo.get('gerente_nome') or '—'}</b>
                    &nbsp;·&nbsp; Coordenador: <b>{vd_saindo.get('coordenador_nome') or '—'}</b>
                    &nbsp;·&nbsp; Unidade: <b>{vd_saindo.get('unidade_nome') or '—'}</b>
                    &nbsp;·&nbsp; Ramo: <b>{vd_saindo.get('ramo_nome') or '—'}</b>
                    &nbsp;·&nbsp; Segmento: <b>{vd_saindo.get('segmento_nome') or '—'}</b>
                </span>
            </div>
            """, unsafe_allow_html=True)

            st.divider()

            # Chaves únicas por vendedor — ao trocar vendedor, o form reseta completamente
            def idx_de(d, val):
                keys = list(d.keys())
                return keys.index(val) if val in keys else 0

            ger_op = opcoes_gerentes()
            coo_op = opcoes_coordenadores()
            par_op = opcoes_parceiros()
            uni_op = opcoes("unidades")
            ram_op = opcoes("ramos")
            seg_op = opcoes("segmentos")

            with st.form(f"form_substituicao_{sid}"):
                st.markdown("**Dados do Novo Vendedor**")
                novo_nome  = st.text_input("Nome *",   key=f"sub_nome_{sid}")
                novo_email = st.text_input("E-mail *", key=f"sub_email_{sid}")

                st.markdown("**Vínculos** *(pré-preenchidos com os do vendedor saindo — ajuste se necessário)*")

                col1, col2 = st.columns(2)
                with col1:
                    ger_sel = st.selectbox("Gerente",     list(ger_op.keys()), index=idx_de(ger_op, vd_saindo.get("gerente_nome","")),     key=f"sub_ger_{sid}")
                    coo_sel = st.selectbox("Coordenador", list(coo_op.keys()), index=idx_de(coo_op, vd_saindo.get("coordenador_nome","")), key=f"sub_coo_{sid}")
                    par_sel = st.selectbox("Parceiro",    list(par_op.keys()), index=idx_de(par_op, vd_saindo.get("parceiro_nome","")),    key=f"sub_par_{sid}")
                with col2:
                    uni_sel = st.selectbox("Unidade",  list(uni_op.keys()), index=idx_de(uni_op, vd_saindo.get("unidade_nome","")),  key=f"sub_uni_{sid}")
                    ram_sel = st.selectbox("Ramo",     list(ram_op.keys()), index=idx_de(ram_op, vd_saindo.get("ramo_nome","")),     key=f"sub_ram_{sid}")
                    seg_sel = st.selectbox("Segmento", list(seg_op.keys()), index=idx_de(seg_op, vd_saindo.get("segmento_nome","")), key=f"sub_seg_{sid}")

                st.divider()
                motivo   = st.text_area("Motivo da substituição", key=f"sub_motivo_{sid}")
                data_sub = st.date_input("Data da substituição", value=date.today(), key=f"sub_data_{sid}")

                if st.form_submit_button("✅ Confirmar Substituição", type="primary"):
                    if not novo_nome or not novo_email:
                        st.error("Informe nome e e-mail do novo vendedor.")
                    else:
                        novo_id = registrar_substituicao(
                            vendedor_saindo_id = vd_saindo["id"],
                            novo_nome          = novo_nome,
                            novo_email         = novo_email,
                            gerente_id         = ger_op.get(ger_sel),
                            coordenador_id     = coo_op.get(coo_sel),
                            parceiro_id        = par_op.get(par_sel),
                            unidade_id         = uni_op.get(uni_sel),
                            ramo_id            = ram_op.get(ram_sel),
                            segmento_id        = seg_op.get(seg_sel),
                            motivo             = motivo,
                            data_sub           = str(data_sub),
                        )
                        st.success(f"✅ Substituição registrada! **{vd_saindo['nome']}** → **{novo_nome}** (ID #{novo_id})")
                        st.rerun()
