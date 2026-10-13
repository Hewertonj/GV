"""
services/operacoes_massa_service.py
Lógica de validação e execução de operações em massa (atualização e substituição).
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

import pandas as pd

from database.connection import get_connection
from services.config_service import listar as listar_config
from services.pessoas_service import listar_gerentes, listar_coordenadores, listar_parceiros
from services.vendedor_service import listar_vendedores, buscar_vendedor


# ── Status de linha ────────────────────────────────────────────────────────────
STATUS_OK             = "ok"
STATUS_AVISO          = "aviso"
STATUS_ERRO           = "erro"
STATUS_SEM_ALTERACAO  = "sem_alteracao"


# ── Helpers de lookup ──────────────────────────────────────────────────────────

def _mapas_referencia():
    """
    Retorna dicts {nome_lower: id} para cada entidade relacional.
    Permite matching case-insensitive.
    """
    def _nome_id(lst):
        return {r["nome"].strip().lower(): r["id"] for r in lst}

    return {
        "gerentes":      _nome_id(listar_gerentes()),
        "coordenadores": _nome_id(listar_coordenadores()),
        "parceiros":     _nome_id(listar_parceiros()),
        "unidades":      _nome_id(listar_config("unidades")),
        "ramos":         _nome_id(listar_config("ramos")),
        "segmentos":     _nome_id(listar_config("segmentos")),
    }


def _vendedores_por_nome_e_id():
    """Retorna dois dicts: {nome_lower: vendedor_dict} e {id: vendedor_dict}."""
    todos = listar_vendedores()
    por_nome = {}
    por_id   = {}
    for v in todos:
        por_nome[v["nome"].strip().lower()] = v
        por_id[v["id"]] = v
    return por_nome, por_id


def _buscar_id(mapa: dict, valor: str | None) -> int | None:
    """Faz lookup case-insensitive; retorna None se valor vazio/não encontrado."""
    if not valor or str(valor).strip() == "":
        return None
    return mapa.get(str(valor).strip().lower())


def _valor_str(val) -> str:
    """Converte para string limpa; trata NaN/None como string vazia."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


def _validar_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def _validar_data(data_str: str) -> bool:
    try:
        datetime.strptime(data_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


# ══════════════════════════════════════════════════════════════════════════════
# MODO 1 — ATUALIZAÇÃO EM MASSA
# ══════════════════════════════════════════════════════════════════════════════

def validar_atualizacao(df: pd.DataFrame) -> list[dict]:
    """
    Valida cada linha do DataFrame de atualização contra o estado atual do banco.
    Identifica com precisão se a linha sofreu alteração (campo a campo).
    Retorna lista de dicts com: linha, status, erros, avisos, dados, row_raw.
    """
    mapas    = _mapas_referencia()
    por_nome, por_id = _vendedores_por_nome_e_id()
    resultados = []

    status_validos = {"ativo", "inativo", "substituído"}

    for idx, row in df.iterrows():
        linha_num  = idx + 2   # linha 1 = cabeçalho no Excel
        msgs_erro  = []
        msgs_aviso = []
        dados      = {}
        alteracoes = []

        # ── Identificar vendedor ─────────────────────────────────────────────
        vid_raw   = _valor_str(row.get("vendedor_id") or row.get("id") or "")
        vnome_raw = _valor_str(row.get("vendedor_nome") or row.get("nome") or "")

        vendedor = None
        if vid_raw.isdigit():
            vendedor = por_id.get(int(vid_raw))
            if not vendedor and vnome_raw:
                vendedor = por_nome.get(vnome_raw.lower())
        elif vnome_raw:
            matches = [v for k, v in por_nome.items() if vnome_raw.lower() in k or k in vnome_raw.lower()]
            if len(matches) == 1:
                vendedor = matches[0]
            elif len(matches) > 1:
                exato = por_nome.get(vnome_raw.lower())
                if exato:
                    vendedor = exato
                else:
                    msgs_aviso.append(f"Nome '{vnome_raw}' corresponde a {len(matches)} vendedores. Use vendedor_id para precisão.")

        if not vendedor:
            msgs_erro.append(f"Vendedor '{vnome_raw or vid_raw}' não encontrado no sistema.")
            resultados.append({
                "linha":    linha_num,
                "status":   STATUS_ERRO,
                "erros":    msgs_erro,
                "avisos":   msgs_aviso,
                "dados":    dados,
                "row_raw":  row.to_dict(),
            })
            continue

        dados["id"]   = vendedor["id"]
        dados["nome"] = vendedor["nome"]

        # ── Comparar campos relacionais ───────────────────────────────────────
        campo_map = [
            ("gerente",          "gerente",     mapas["gerentes"],      "gerente_id",   "Gerente"),
            ("coordenador",      "coordenador", mapas["coordenadores"], "coordenador_id", "Coordenador"),
            ("parceiro_interno", "parceiro",    mapas["parceiros"],     "parceiro_id",   "Parceiro Interno"),
            ("unidade",          "unidade",     mapas["unidades"],      "unidade_id",   "Unidade"),
            ("ramo",             "ramo",        mapas["ramos"],         "ramo_id",      "Ramo"),
            ("segmento",         "segmento",    mapas["segmentos"],     "segmento_id",  "Segmento"),
        ]

        for col_planilha, chave_db, mapa_lookup, chave_dados, label_campo in campo_map:
            val_planilha = _valor_str(row.get(col_planilha) or (row.get("parceiro") if col_planilha == "parceiro_interno" else "") or "")
            val_atual    = _valor_str(vendedor.get(chave_db) or "")

            # Se informado e diferente do atual no banco -> alteração detectada
            if val_planilha and (val_planilha.lower() != val_atual.lower()):
                id_val = _buscar_id(mapa_lookup, val_planilha)
                if id_val is None:
                    msgs_aviso.append(f"'{val_planilha}' não encontrado para '{label_campo}'. Campo será ignorado.")
                else:
                    dados[chave_dados] = id_val
                    dados[f"_{col_planilha}_nome"] = val_planilha
                    alteracoes.append({
                        "campo": label_campo,
                        "de":    val_atual or "(não definido)",
                        "para":  val_planilha,
                    })

        # ── Status ────────────────────────────────────────────────────────────
        status_planilha = _valor_str(row.get("status") or "").lower()
        status_atual    = _valor_str(vendedor.get("status") or "ativo").lower()
        if status_planilha and (status_planilha != status_atual):
            if status_planilha not in status_validos:
                msgs_aviso.append(f"Status '{status_planilha}' inválido. Use: ativo, inativo ou substituído.")
            else:
                dados["status"] = status_planilha
                alteracoes.append({
                    "campo": "Status",
                    "de":    status_atual,
                    "para":  status_planilha,
                })

        # ── Nome (se informado com ID e alterado) ─────────────────────────────
        nome_planilha = _valor_str(row.get("vendedor_nome") or row.get("nome") or "")
        nome_atual    = _valor_str(vendedor.get("nome") or "")
        if vid_raw.isdigit() and nome_planilha and (nome_planilha.lower() != nome_atual.lower()):
            dados["nome_novo"] = nome_planilha
            alteracoes.append({
                "campo": "Nome",
                "de":    nome_atual,
                "para":  nome_planilha,
            })

        dados["alteracoes"] = alteracoes

        # ── Determinar status final da linha ─────────────────────────────────
        if msgs_erro:
            status_linha = STATUS_ERRO
        elif len(alteracoes) == 0:
            status_linha = STATUS_SEM_ALTERACAO
        elif msgs_aviso:
            status_linha = STATUS_AVISO
        else:
            status_linha = STATUS_OK

        resultados.append({
            "linha":    linha_num,
            "status":   status_linha,
            "erros":    msgs_erro,
            "avisos":   msgs_aviso,
            "dados":    dados,
            "row_raw":  row.to_dict(),
        })

    return resultados


def executar_atualizacao(resultados: list[dict]) -> tuple[int, int, list[str]]:
    """
    Executa as atualizações validadas (apenas linhas com alterações).
    Linhas com status 'sem_alteracao' são puladas sem gerar erro nem tocar no banco.
    Retorna (sucesso, erros, mensagens_erro).
    """
    conn = get_connection()
    sucesso = 0
    erros   = 0
    msgs    = []
    itens_alterados = []

    for r in resultados:
        if r["status"] == STATUS_SEM_ALTERACAO:
            # Pula linhas sem alteração
            continue

        if r["status"] == STATUS_ERRO:
            erros += 1
            msgs.append(f"Linha {r['linha']}: pulada — {'; '.join(r['erros'])}")
            continue

        d = r["dados"]
        alteracoes = d.get("alteracoes", [])
        if not alteracoes or "id" not in d:
            continue

        try:
            sets   = []
            params = []
            if "gerente_id" in d:
                sets.append("gerente_id = ?")
                params.append(d["gerente_id"])
            if "coordenador_id" in d:
                sets.append("coordenador_id = ?")
                params.append(d["coordenador_id"])
            if "parceiro_id" in d:
                sets.append("parceiro_interno_id = ?")
                params.append(d["parceiro_id"])
            if "unidade_id" in d:
                sets.append("unidade_id = ?")
                params.append(d["unidade_id"])
            if "ramo_id" in d:
                sets.append("ramo_id = ?")
                params.append(d["ramo_id"])
            if "segmento_id" in d:
                sets.append("segmento_id = ?")
                params.append(d["segmento_id"])
            if "status" in d:
                sets.append("status = ?")
                params.append(d["status"])
            if "nome_novo" in d:
                sets.append("nome = ?")
                params.append(d["nome_novo"])

            if sets:
                params.append(d["id"])
                conn.execute(f"UPDATE vendedores SET {', '.join(sets)} WHERE id = ?", params)
                conn.commit()

            sucesso += 1
            itens_alterados.append({
                "nome": d.get("nome", f"ID {d['id']}"),
                "alteracoes": alteracoes,
            })

        except Exception as e:
            erros += 1
            msgs.append(f"Linha {r['linha']} ({d.get('nome', 'ID ' + str(d.get('id')))}): erro ao atualizar — {e}")

    conn.close()

    # Dispara e-mail de notificação (não-bloqueante)
    if itens_alterados:
        try:
            from services.email_service import notificar_alteracao_vendedor, notificar_atualizacao_massa
            if len(itens_alterados) == 1:
                notificar_alteracao_vendedor(itens_alterados[0]["nome"], itens_alterados[0]["alteracoes"])
            else:
                notificar_atualizacao_massa(itens_alterados, total_processados=len(resultados))
        except Exception:
            pass

    return sucesso, erros, msgs


# ══════════════════════════════════════════════════════════════════════════════
# MODO 2 — SUBSTITUIÇÃO EM MASSA
# ══════════════════════════════════════════════════════════════════════════════

def validar_substituicao(df: pd.DataFrame) -> list[dict]:
    """
    Valida cada linha do DataFrame de substituição.
    """
    mapas    = _mapas_referencia()
    por_nome, por_id = _vendedores_por_nome_e_id()
    # Apenas vendedores ativos podem ser substituídos
    ativos_por_nome = {v["nome"].strip().lower(): v for v in listar_vendedores(status="ativo")}
    ativos_por_id   = {v["id"]: v for v in listar_vendedores(status="ativo")}

    resultados = []

    for idx, row in df.iterrows():
        linha_num  = idx + 2
        msgs_erro  = []
        msgs_aviso = []
        dados      = {}

        # ── Vendedor saindo ──────────────────────────────────────────────────
        saindo_raw = _valor_str(row.get("vendedor_saindo") or "")
        if not saindo_raw:
            msgs_erro.append("Campo 'vendedor_saindo' está vazio.")
            v_saindo = None
        else:
            if saindo_raw.isdigit():
                v_saindo = ativos_por_id.get(int(saindo_raw))
            else:
                v_saindo = ativos_por_nome.get(saindo_raw.lower())
                if not v_saindo:
                    # fuzzy: qualquer ativo que contenha o nome
                    matches = [v for k, v in ativos_por_nome.items() if saindo_raw.lower() in k]
                    if len(matches) == 1:
                        v_saindo = matches[0]
                    elif len(matches) > 1:
                        msgs_aviso.append(f"'{saindo_raw}' corresponde a {len(matches)} ativos. Use o nome exato.")

            if not v_saindo:
                msgs_erro.append(f"Vendedor ativo '{saindo_raw}' não encontrado.")
            else:
                dados["vendedor_saindo_id"]   = v_saindo["id"]
                dados["vendedor_saindo_nome"] = v_saindo["nome"]

        # ── Novo vendedor ────────────────────────────────────────────────────
        novo_nome  = _valor_str(row.get("novo_nome") or "")
        novo_email = _valor_str(row.get("novo_email") or "")

        if not novo_nome:
            msgs_erro.append("Campo 'novo_nome' está vazio.")
        else:
            dados["novo_nome"] = novo_nome

        if not novo_email:
            msgs_erro.append("Campo 'novo_email' está vazio.")
        elif not _validar_email(novo_email):
            msgs_erro.append(f"E-mail '{novo_email}' com formato inválido.")
        else:
            dados["novo_email"] = novo_email

        # ── Vínculos opcionais (herdam do saindo se omitidos) ────────────────
        saindo_vd = buscar_vendedor(v_saindo["id"]) if v_saindo else {}

        campo_map = [
            ("gerente",          mapas["gerentes"],      "gerente_id",      saindo_vd.get("gerente_id")),
            ("coordenador",      mapas["coordenadores"], "coordenador_id",  saindo_vd.get("coordenador_id")),
            ("parceiro_interno", mapas["parceiros"],     "parceiro_id",     saindo_vd.get("parceiro_interno_id")),
            ("unidade",          mapas["unidades"],      "unidade_id",      saindo_vd.get("unidade_id")),
            ("ramo",             mapas["ramos"],         "ramo_id",         saindo_vd.get("ramo_id")),
            ("segmento",         mapas["segmentos"],     "segmento_id",     saindo_vd.get("segmento_id")),
        ]

        for col_planilha, mapa_lookup, chave_dados, fallback_id in campo_map:
            val = _valor_str(row.get(col_planilha) or "")
            if val:
                id_val = _buscar_id(mapa_lookup, val)
                if id_val is None:
                    msgs_aviso.append(f"'{val}' não encontrado para '{col_planilha}'. Será usado o vínculo do saindo.")
                    dados[chave_dados] = fallback_id
                else:
                    dados[chave_dados] = id_val
            else:
                dados[chave_dados] = fallback_id   # herda do saindo

        # ── Data e motivo ────────────────────────────────────────────────────
        data_raw  = _valor_str(row.get("data_substituicao") or "")
        motivo    = _valor_str(row.get("motivo") or "")

        if data_raw:
            # tenta converter formatos comuns
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    d_obj = datetime.strptime(data_raw, fmt)
                    dados["data_sub"] = d_obj.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue
            else:
                msgs_aviso.append(f"Data '{data_raw}' em formato não reconhecido. Será usada a data de hoje.")
                dados["data_sub"] = str(date.today())
        else:
            dados["data_sub"] = str(date.today())

        dados["motivo"] = motivo

        # ── Status final ─────────────────────────────────────────────────────
        if msgs_erro:
            status_linha = STATUS_ERRO
        elif msgs_aviso:
            status_linha = STATUS_AVISO
        else:
            status_linha = STATUS_OK

        resultados.append({
            "linha":   linha_num,
            "status":  status_linha,
            "erros":   msgs_erro,
            "avisos":  msgs_aviso,
            "dados":   dados,
            "row_raw": row.to_dict(),
        })

    return resultados


def executar_substituicao(resultados: list[dict]) -> tuple[int, int, list[str]]:
    """
    Executa as substituições validadas (apenas linhas ok ou aviso).
    """
    from services.vendedor_service import registrar_substituicao

    sucesso = 0
    erros   = 0
    msgs    = []

    for r in resultados:
        if r["status"] == STATUS_ERRO:
            erros += 1
            msgs.append(f"Linha {r['linha']}: pulada — {'; '.join(r['erros'])}")
            continue

        d = r["dados"]
        campos_req = ["vendedor_saindo_id", "novo_nome", "novo_email", "data_sub"]
        if any(k not in d for k in campos_req):
            erros += 1
            msgs.append(f"Linha {r['linha']}: dados incompletos.")
            continue

        try:
            registrar_substituicao(
                vendedor_saindo_id = d["vendedor_saindo_id"],
                novo_nome          = d["novo_nome"],
                novo_email         = d["novo_email"],
                gerente_id         = d.get("gerente_id"),
                coordenador_id     = d.get("coordenador_id"),
                parceiro_id        = d.get("parceiro_id"),
                unidade_id         = d.get("unidade_id"),
                ramo_id            = d.get("ramo_id"),
                segmento_id        = d.get("segmento_id"),
                motivo             = d.get("motivo", ""),
                data_sub           = d["data_sub"],
            )
            sucesso += 1

        except Exception as e:
            erros += 1
            msgs.append(f"Linha {r['linha']}: erro — {e}")

    return sucesso, erros, msgs


# ── Gerador de relatório de resultados ────────────────────────────────────────

def gerar_relatorio(resultados: list[dict], modo: str) -> bytes:
    """Gera Excel com os resultados do processamento."""
    import io
    from utils.export import df_para_excel

    linhas = []
    status_map = {
        STATUS_OK:            "✅ Alterado",
        STATUS_AVISO:         "⚠️ Alterado c/ Aviso",
        STATUS_SEM_ALTERACAO: "⚪ Sem Alteração",
        STATUS_ERRO:          "❌ Erro",
    }

    for r in resultados:
        alts = r["dados"].get("alteracoes", [])
        txt_alt = " | ".join([f"{a['campo']}: {a['de']} ➔ {a['para']}" for a in alts]) if alts else ""

        linha = {
            "Linha":                 r["linha"],
            "Status":                status_map.get(r["status"], r["status"]),
            "Alterações Detectadas": txt_alt,
            "Erros":                 " | ".join(r["erros"])  if r["erros"]  else "",
            "Avisos":                " | ".join(r["avisos"]) if r["avisos"] else "",
        }
        # Adiciona campos brutos para referência
        for k, v in r["row_raw"].items():
            linha[f"planilha_{k}"] = v
        linhas.append(linha)

    df = pd.DataFrame(linhas)
    return df_para_excel(df)

