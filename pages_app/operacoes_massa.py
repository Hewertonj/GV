"""
pages_app/operacoes_massa.py
Página de Operações em Massa — upload de planilha para atualização e substituição em lote.
"""

import streamlit as st
import pandas as pd

from services.config_service import listar as listar_config
from services.pessoas_service import listar_gerentes, listar_coordenadores, listar_parceiros
from utils.planilha_template import gerar_template_atualizacao, gerar_template_substituicao
from services.operacoes_massa_service import (
    validar_atualizacao, executar_atualizacao,
    validar_substituicao, executar_substituicao,
    gerar_relatorio,
    STATUS_OK, STATUS_AVISO, STATUS_ERRO, STATUS_SEM_ALTERACAO,
)


# ── Helpers de contexto ────────────────────────────────────────────────────────

def _nomes(lst):
    return [r["nome"] for r in lst]


def _listas_referencia():
    return {
        "gerentes":      _nomes(listar_gerentes()),
        "coordenadores": _nomes(listar_coordenadores()),
        "parceiros":     _nomes(listar_parceiros()),
        "unidades":      _nomes(listar_config("unidades")),
        "ramos":         _nomes(listar_config("ramos")),
        "segmentos":     _nomes(listar_config("segmentos")),
    }


# ── Componentes de UI ──────────────────────────────────────────────────────────

def _badge(status: str) -> str:
    return {
        STATUS_OK:            "🟢",
        STATUS_AVISO:         "🟡",
        STATUS_ERRO:          "🔴",
        STATUS_SEM_ALTERACAO: "⚪",
    }.get(status, "⚪")


def _resumo_contagens(resultados):
    ok      = sum(1 for r in resultados if r["status"] == STATUS_OK)
    aviso   = sum(1 for r in resultados if r["status"] == STATUS_AVISO)
    sem_alt = sum(1 for r in resultados if r["status"] == STATUS_SEM_ALTERACAO)
    erro    = sum(1 for r in resultados if r["status"] == STATUS_ERRO)
    return ok, aviso, sem_alt, erro


def _render_preview(resultados: list[dict], modo: str):
    """Renderiza tabela de preview com status de validação."""
    ok, aviso, sem_alt, erro = _resumo_contagens(resultados)
    total = len(resultados)
    alterados = ok + aviso

    # Métricas
    if modo == "atualizacao":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📄 Total na planilha", total)
        c2.metric("🟢 Com alterações",     alterados)
        c3.metric("⚪ Sem alterações",     sem_alt)
        c4.metric("🔴 Com erros",          erro)
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📄 Total de linhas",    total)
        c2.metric("🟢 Prontas",            ok)
        c3.metric("🟡 Com avisos",         aviso)
        c4.metric("🔴 Com erros",          erro)

    st.divider()

    if modo == "atualizacao":
        if alterados == 0 and erro == 0:
            st.info("ℹ️ **Nenhuma alteração detectada.** Todos os registros da planilha estão idênticos aos cadastrados no sistema.")
        elif alterados > 0:
            msg = f"🔍 **{alterados}** vendedor(es) com alterações detectadas prontos para atualização."
            if sem_alt > 0:
                msg += f" As **{sem_alt}** linhas sem modificações serão ignoradas na execução."
            st.success(msg)
    else:
        if erro == total:
            st.error("❌ Todas as linhas têm erros. Corrija a planilha antes de prosseguir.")
        elif erro > 0:
            st.warning(f"⚠️ {erro} linha(s) com erro serão **ignoradas** na execução. As demais ({ok + aviso}) serão processadas.")
        else:
            st.success(f"✅ Planilha válida! {total} linha(s) prontas para execução.")

    # Filtro opcional para exibir só o que mudou
    filtrar_apenas_modificados = False
    if modo == "atualizacao" and sem_alt > 0 and (alterados > 0 or erro > 0):
        filtrar_apenas_modificados = st.checkbox(
            f"Exibir apenas vendedores com alterações ou erros na tabela ({alterados + erro})",
            value=True,
            key=f"flt_mod_{modo}",
        )

    # Tabela de preview
    linhas_tabela = []
    for r in resultados:
        if filtrar_apenas_modificados and r["status"] == STATUS_SEM_ALTERACAO:
            continue

        raw = r["row_raw"]
        if modo == "atualizacao":
            vendedor = r["dados"].get("nome") or raw.get("vendedor_nome", "—")
            alts = r["dados"].get("alteracoes", [])
            if alts:
                detalhe = " | ".join([f"{a['campo']}: {a['de']} ➔ {a['para']}" for a in alts])
            elif r["status"] == STATUS_SEM_ALTERACAO:
                detalhe = "⚪ Sem alterações (idêntico ao sistema)"
            else:
                detalhe = "—"
        else:
            vendedor = r["dados"].get("vendedor_saindo_nome") or raw.get("vendedor_saindo", "—")
            detalhe  = f"→ {raw.get('novo_nome','—')} ({raw.get('novo_email','—')})"

        msgs = []
        if r["erros"]:
            msgs += [f"❌ {e}" for e in r["erros"]]
        if r["avisos"]:
            msgs += [f"⚠️ {a}" for a in r["avisos"]]

        status_nome = {
            STATUS_OK:            "Alterado",
            STATUS_AVISO:         "Aviso",
            STATUS_SEM_ALTERACAO: "Sem alteração",
            STATUS_ERRO:          "Erro",
        }.get(r["status"], r["status"].capitalize())

        linhas_tabela.append({
            "Linha":                 r["linha"],
            "Status":                f"{_badge(r['status'])} {status_nome}",
            "Vendedor":              vendedor,
            "Alterações / Detalhes": detalhe,
            "Mensagens":             " | ".join(msgs) if msgs else "—",
        })

    if linhas_tabela:
        df_prev = pd.DataFrame(linhas_tabela)
        st.dataframe(df_prev, use_container_width=True, hide_index=True)
    elif filtrar_apenas_modificados:
        st.caption("Nenhuma linha a exibir com o filtro atual.")


def _render_resultado_execucao(sucesso: int, erros: int, msgs_erro: list[str], modo: str):
    """Exibe resumo pós-execução."""
    st.markdown("---")
    st.markdown("### 📊 Resultado da Execução")

    c1, c2 = st.columns(2)
    c1.metric("✅ Processados com sucesso", sucesso)
    c2.metric("❌ Erros na execução",       erros)

    if sucesso > 0:
        label = "atualizações" if modo == "atualizacao" else "substituições"
        st.success(f"✅ {sucesso} {label} realizadas com sucesso!")

    if msgs_erro:
        with st.expander(f"⚠️ Detalhes dos {len(msgs_erro)} erro(s)"):
            for m in msgs_erro:
                st.write(f"- {m}")


# ── Aba de Atualização ─────────────────────────────────────────────────────────

def _tab_atualizacao():
    st.markdown("#### 📝 Atualização em Massa de Vendedores")
    st.caption(
        "Baixe a planilha com toda a base de vendedores, edite os campos desejados e reenvie. "
        "O sistema identificará automaticamente apenas os vendedores e campos que foram modificados."
    )

    listas = _listas_referencia()

    # ── Download do template ───────────────────────────────────────────────
    with st.expander("📥 1. Baixar Template com Toda a Base de Vendedores", expanded=True):
        st.markdown(
            "O arquivo gerado abaixo já vem preenchido com **todos os vendedores cadastrados no sistema**. "
            "Altere apenas as células que deseja atualizar e salve o arquivo. "
            "A aba **Referência** lista todos os valores válidos para cada campo."
        )
        template_bytes = gerar_template_atualizacao(**listas)
        st.download_button(
            label="⬇️ Baixar Base de Vendedores (.xlsx)",
            data=template_bytes,
            file_name="base_vendedores_atualizacao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_template_att",
        )

    st.markdown("---")

    # ── Upload ─────────────────────────────────────────────────────────────
    with st.expander("📤 2. Enviar Planilha Editada", expanded=True):
        arquivo = st.file_uploader(
            "Selecione o arquivo (.xlsx ou .csv)",
            type=["xlsx", "csv"],
            key="upload_att",
        )

    if not arquivo:
        return

    # ── Leitura ────────────────────────────────────────────────────
    try:
        if arquivo.name.endswith(".csv"):
            df = pd.read_csv(arquivo, dtype=str, keep_default_na=False)
        else:
            df = pd.read_excel(arquivo, dtype=str, keep_default_na=False)

        # Normaliza nomes de colunas: remove asteriscos, termos entre parenteses e espaços
        cols_limpas = []
        for c in df.columns:
            c_limpa = str(c).lower().replace("*", "")
            for termo in ["(opcional)", "(não alterar)", "(ativo/inativo)", "(aaaa-mm-dd)"]:
                c_limpa = c_limpa.replace(termo, "")
            cols_limpas.append(c_limpa.strip())
        df.columns = cols_limpas

        # Ignora linhas completamente vazias
        df = df.dropna(how="all").reset_index(drop=True)

    except Exception as e:
        st.error(f"❌ Erro ao ler o arquivo: {e}")
        return

    if df.empty:
        st.warning("A planilha está vazia.")
        return

    st.markdown("---")
    st.markdown("#### 🔍 3. Preview e Validação")

    resultados = validar_atualizacao(df)
    _render_preview(resultados, "atualizacao")

    ok, aviso, sem_alt, erro = _resumo_contagens(resultados)
    executaveis = ok + aviso

    if executaveis == 0 and erro == 0:
        st.info("💡 Não há alterações a serem salvas. Todos os registros estão idênticos.")
        return

    if executaveis == 0:
        st.error("Nenhuma alteração válida encontrada. Corrija os erros e tente novamente.")
        return

    st.markdown("---")
    st.markdown("#### ▶️ 4. Executar")

    col1, col2 = st.columns([1, 3])
    with col1:
        txt_conf = f"Confirmo a atualização de **{executaveis}** vendedor(es)"
        if sem_alt > 0:
            txt_conf += f" ({sem_alt} sem alteração serão ignorados)"
        confirmar = st.checkbox(txt_conf, key="conf_att")

    if confirmar:
        if st.button("🚀 Executar Atualização em Massa", type="primary", key="btn_exec_att"):
            with st.spinner("Processando alterações e enviando notificações..."):
                sucesso, erros_exec, msgs = executar_atualizacao(resultados)

            _render_resultado_execucao(sucesso, erros_exec, msgs, "atualizacao")

            # Download do relatório
            rel = gerar_relatorio(resultados, "atualizacao")
            st.download_button(
                "📄 Baixar Relatório de Resultados",
                data=rel,
                file_name="relatorio_atualizacao.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_rel_att",
            )



# ── Aba de Substituição ────────────────────────────────────────────────────────

def _tab_substituicao():
    st.markdown("#### 🔄 Substituição em Massa de Vendedores")
    st.caption(
        "Registre múltiplas substituições de uma vez: o vendedor saindo será marcado como "
        "**substituído** e o novo será cadastrado com os vínculos informados (ou herdados)."
    )

    listas = _listas_referencia()

    # ── Download do template ───────────────────────────────────────────────
    with st.expander("📥 1. Baixar Template de Substituição", expanded=True):
        st.markdown(
            "Os campos de vínculo são **opcionais** — se deixados em branco, "
            "o novo vendedor herdará os mesmos vínculos do vendedor saindo."
        )
        template_bytes = gerar_template_substituicao(**listas)
        st.download_button(
            label="⬇️ Baixar Template (.xlsx)",
            data=template_bytes,
            file_name="template_substituicao_vendedores.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_template_sub",
        )

    st.markdown("---")

    # ── Upload ─────────────────────────────────────────────────────────────
    with st.expander("📤 2. Enviar Planilha Preenchida", expanded=True):
        arquivo = st.file_uploader(
            "Selecione o arquivo (.xlsx ou .csv)",
            type=["xlsx", "csv"],
            key="upload_sub",
        )

    if not arquivo:
        return

    # ── Leitura ────────────────────────────────────────────────────────────
    try:
        if arquivo.name.endswith(".csv"):
            df = pd.read_csv(arquivo, dtype=str, keep_default_na=False)
        else:
            df = pd.read_excel(arquivo, dtype=str, keep_default_na=False)

        df.columns = [c.lower().replace("*","").replace("(opcional)","").replace("(aaaa-mm-dd)","").strip() for c in df.columns]
        df = df.dropna(how="all").reset_index(drop=True)

    except Exception as e:
        st.error(f"❌ Erro ao ler o arquivo: {e}")
        return

    if df.empty:
        st.warning("A planilha está vazia.")
        return

    st.markdown("---")
    st.markdown("#### 🔍 3. Preview e Validação")

    resultados = validar_substituicao(df)
    _render_preview(resultados, "substituicao")

    ok, aviso, erro = _resumo_contagens(resultados)
    executaveis = ok + aviso

    if executaveis == 0:
        st.error("Nenhuma linha pode ser processada. Corrija os erros e tente novamente.")
        return

    st.markdown("---")
    st.markdown("#### ▶️ 4. Executar")

    col1, col2 = st.columns([1, 3])
    with col1:
        confirmar = st.checkbox(
            f"Confirmo a substituição de **{executaveis}** vendedor(es)",
            key="conf_sub",
        )

    if confirmar:
        st.error(
            "⚠️ **Atenção:** Esta operação é **irreversível**. "
            "Os vendedores saindo serão marcados como **substituídos** permanentemente."
        )
        if st.button("🚀 Executar Substituição em Massa", type="primary", key="btn_exec_sub"):
            with st.spinner("Processando substituições..."):
                sucesso, erros_exec, msgs = executar_substituicao(resultados)

            _render_resultado_execucao(sucesso, erros_exec, msgs, "substituicao")

            rel = gerar_relatorio(resultados, "substituicao")
            st.download_button(
                "📄 Baixar Relatório de Resultados",
                data=rel,
                file_name="relatorio_substituicao.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_rel_sub",
            )



# ── Render principal ───────────────────────────────────────────────────────────

def render():
    st.header("📦 Operações em Massa")
    st.caption(
        "Realize atualizações e substituições de múltiplos vendedores via planilha Excel/CSV."
    )

    # Card explicativo
    st.markdown("""
    <div style="
        background: linear-gradient(135deg,#F0F7FF,#E8F0FE);
        border: 1px solid #BFDBFE;
        border-left: 4px solid #0E5BB3;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 20px;
    ">
        <b style="color:#0E5BB3;">Como funciona:</b>
        <ol style="margin:8px 0 0 0;padding-left:20px;color:#374151;font-size:0.9rem;line-height:1.8;">
            <li>Baixe o <b>template</b> da operação desejada</li>
            <li>Preencha com os dados (a aba <i>Referência</i> lista os valores válidos)</li>
            <li>Faça o <b>upload</b> da planilha preenchida</li>
            <li>Revise o <b>preview</b> com as validações</li>
            <li>Confirme e clique em <b>Executar</b></li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    tab_att, tab_sub = st.tabs(["📝 Atualização em Massa", "🔄 Substituição em Massa"])

    with tab_att:
        _tab_atualizacao()

    with tab_sub:
        _tab_substituicao()
