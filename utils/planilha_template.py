"""
utils/planilha_template.py
Geração dos templates Excel para operações em massa.
"""

import io
import pandas as pd
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ── Paleta de cores ────────────────────────────────────────────────────────────
_AZUL_HEADER   = "0E5BB3"
_VERDE_HEADER  = "088012"
_AMARELO_OBRIG = "FFF3CD"
_CINZA_OPCL    = "F0F4F8"
_BRANCO        = "FFFFFF"


def _estilizar_aba(ws, colunas_obrigatorias: list[str]):
    """Aplica estilo às duas primeiras linhas (título e legenda) e ao cabeçalho."""
    header_row  = ws[1]   # cabeçalhos de coluna
    exemplo_row = ws[2]   # linha de exemplo (se existir)

    for cell in header_row:
        col_name = cell.value or ""
        obrigatorio = col_name in colunas_obrigatorias
        fill_color  = _AMARELO_OBRIG if obrigatorio else _CINZA_OPCL
        font_color  = "7B4F00" if obrigatorio else "1E3A5F"

        cell.fill      = PatternFill("solid", fgColor=fill_color)
        cell.font      = Font(bold=True, color=font_color, size=10)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border    = _borda()

    for cell in exemplo_row:
        cell.fill      = PatternFill("solid", fgColor="E8F5E9")
        cell.font      = Font(italic=True, color="2E7D32", size=9)
        cell.alignment = Alignment(horizontal="left", vertical="center")
        cell.border    = _borda()

    # Largura automática
    for i, col in enumerate(ws.columns, 1):
        max_len = max(len(str(c.value or "")) for c in col) + 4
        ws.column_dimensions[get_column_letter(i)].width = min(max_len, 35)

    ws.row_dimensions[1].height = 30
    if ws.max_row >= 2:
        ws.row_dimensions[2].height = 22


def _borda():
    thin = Side(style="thin", color="CCCCCC")
    return Border(left=thin, right=thin, top=thin, bottom=thin)


def _buf_para_bytes(wb) -> bytes:
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _estilizar_aba_dados(ws):
    """Estiliza a aba de dados reais: cabeçalho azul escuro e linhas de dados formatadas."""
    for cell in ws[1]:
        cell.fill      = PatternFill("solid", fgColor=_AZUL_HEADER)
        cell.font      = Font(bold=True, color=_BRANCO, size=10)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border    = _borda()

    ws.row_dimensions[1].height = 28

    # Linhas de dados
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        ws.row_dimensions[row[0].row].height = 20
        for cell in row:
            cell.border = _borda()
            cell.font   = Font(size=10, color="0F172A")
            # Coluna 1 (ID) e 9 (Status) centralizadas
            if cell.column in (1, 9):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # Largura automática
    for i, col in enumerate(ws.columns, 1):
        max_len = max(len(str(c.value or "")) for c in col) + 4
        ws.column_dimensions[get_column_letter(i)].width = max(min(max_len, 40), 15)


# ── Template de Atualização ────────────────────────────────────────────────────

def gerar_template_atualizacao(
    gerentes: list[str],
    coordenadores: list[str],
    parceiros: list[str],
    unidades: list[str],
    ramos: list[str],
    segmentos: list[str],
    vendedores: list[dict] | None = None,
) -> bytes:
    """
    Gera template Excel para atualização em massa de vendedores,
    preenchendo automaticamente com toda a base de vendedores cadastrada no sistema.
    """
    if vendedores is None:
        try:
            from services.vendedor_service import listar_vendedores
            vendedores = listar_vendedores()
        except Exception:
            vendedores = []

    colunas = [
        "vendedor_id", "vendedor_nome",
        "gerente", "coordenador", "parceiro_interno",
        "unidade", "ramo", "segmento", "status",
    ]

    linhas = []
    if vendedores:
        for v in vendedores:
            linhas.append({
                "vendedor_id":      v.get("id"),
                "vendedor_nome":    v.get("nome", ""),
                "gerente":          v.get("gerente") or "",
                "coordenador":      v.get("coordenador") or "",
                "parceiro_interno": v.get("parceiro") or "",
                "unidade":          v.get("unidade") or "",
                "ramo":             v.get("ramo") or "",
                "segmento":         v.get("segmento") or "",
                "status":           v.get("status") or "ativo",
            })
    else:
        # Exemplo caso não haja nenhum vendedor cadastrado
        linhas.append({
            "vendedor_id":      1,
            "vendedor_nome":    "Exemplo de Vendedor",
            "gerente":          gerentes[0]      if gerentes      else "",
            "coordenador":      coordenadores[0] if coordenadores else "",
            "parceiro_interno": parceiros[0]     if parceiros     else "",
            "unidade":          unidades[0]      if unidades      else "",
            "ramo":             ramos[0]         if ramos         else "",
            "segmento":         segmentos[0]     if segmentos     else "",
            "status":           "ativo",
        })

    df = pd.DataFrame(linhas, columns=colunas)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Atualização")

        ws = writer.sheets["Atualização"]
        _estilizar_aba_dados(ws)

        # Aba de referência com listas válidas
        _criar_aba_referencia(writer, gerentes, coordenadores, parceiros, unidades, ramos, segmentos)

    return buf.getvalue()


# ── Template de Substituição ───────────────────────────────────────────────────

def gerar_template_substituicao(
    gerentes: list[str],
    coordenadores: list[str],
    parceiros: list[str],
    unidades: list[str],
    ramos: list[str],
    segmentos: list[str],
) -> bytes:
    """Gera template Excel para substituição em massa de vendedores."""

    colunas = [
        "vendedor_saindo",
        "novo_nome", "novo_email",
        "gerente", "coordenador", "parceiro_interno",
        "unidade", "ramo", "segmento",
        "motivo", "data_substituicao",
    ]
    obrigatorias = ["vendedor_saindo", "novo_nome", "novo_email"]

    exemplo = {
        "vendedor_saindo":   "João Silva",
        "novo_nome":         "Pedro Costa",
        "novo_email":        "pedro.costa@empresa.com",
        "gerente":           gerentes[0]      if gerentes      else "(herda do saindo)",
        "coordenador":       coordenadores[0] if coordenadores else "(herda do saindo)",
        "parceiro_interno":  parceiros[0]     if parceiros     else "(herda do saindo)",
        "unidade":           unidades[0]      if unidades      else "(herda do saindo)",
        "ramo":              ramos[0]         if ramos         else "(herda do saindo)",
        "segmento":          segmentos[0]     if segmentos     else "(herda do saindo)",
        "motivo":            "Pedido de demissão",
        "data_substituicao": pd.Timestamp.today().strftime("%Y-%m-%d"),
    }

    df = pd.DataFrame([exemplo], columns=colunas)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Substituição")

        ws = writer.sheets["Substituição"]

        cabecalho_amigavel = {
            "vendedor_saindo":   "vendedor_saindo *",
            "novo_nome":         "novo_nome *",
            "novo_email":        "novo_email *",
            "gerente":           "gerente (opcional)",
            "coordenador":       "coordenador (opcional)",
            "parceiro_interno":  "parceiro_interno (opcional)",
            "unidade":           "unidade (opcional)",
            "ramo":              "ramo (opcional)",
            "segmento":          "segmento (opcional)",
            "motivo":            "motivo (opcional)",
            "data_substituicao": "data_substituicao (AAAA-MM-DD)",
        }
        for i, col in enumerate(colunas, 1):
            ws.cell(1, i).value = cabecalho_amigavel[col]

        _estilizar_aba(ws, [cabecalho_amigavel[c] for c in obrigatorias])
        _criar_aba_referencia(writer, gerentes, coordenadores, parceiros, unidades, ramos, segmentos)

    return buf.getvalue()


# ── Aba de Referência ──────────────────────────────────────────────────────────

def _criar_aba_referencia(writer, gerentes, coordenadores, parceiros, unidades, ramos, segmentos):
    """Cria aba 'Referência' com os valores válidos para cada campo."""
    status_lista = ["ativo", "inativo", "substituído"]
    max_len = max(len(gerentes), len(coordenadores), len(parceiros),
                  len(unidades), len(ramos), len(segmentos), len(status_lista), 1)

    def pad(lst):
        lst = list(lst)
        return lst + [""] * max(0, max_len - len(lst))

    df_ref = pd.DataFrame({
        "Gerentes":           pad(gerentes),
        "Coordenadores":      pad(coordenadores),
        "Parceiros Internos": pad(parceiros),
        "Unidades":           pad(unidades),
        "Ramos":              pad(ramos),
        "Segmentos":          pad(segmentos),
        "Status válidos":     pad(status_lista),
    })

    df_ref.to_excel(writer, index=False, sheet_name="Referência")
    ws_ref = writer.sheets["Referência"]

    for cell in ws_ref[1]:
        cell.fill = PatternFill("solid", fgColor="0E5BB3")
        cell.font = Font(bold=True, color="FFFFFF", size=10)
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for col in ws_ref.columns:
        max_w = max(len(str(c.value or "")) for c in col) + 4
        ws_ref.column_dimensions[get_column_letter(col[0].column)].width = min(max_w, 30)

    ws_ref.row_dimensions[1].height = 25
