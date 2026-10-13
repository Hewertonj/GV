from database.connection import get_connection

# ── Tabelas simples (unidades, ramos, segmentos) ───────────────────────────────

def listar(tabela: str):
    conn = get_connection()
    rows = conn.execute(f"SELECT * FROM {tabela} ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def adicionar(tabela: str, nome: str):
    conn = get_connection()
    conn.execute(f"INSERT INTO {tabela} (nome) VALUES (?)", (nome.strip(),))
    conn.commit()
    conn.close()

def editar(tabela: str, id_: int, novo_nome: str):
    conn = get_connection()
    conn.execute(f"UPDATE {tabela} SET nome=? WHERE id=?", (novo_nome.strip(), id_))
    conn.commit()
    conn.close()

def excluir(tabela: str, id_: int):
    conn = get_connection()
    conn.execute(f"DELETE FROM {tabela} WHERE id=?", (id_,))
    conn.commit()
    conn.close()

def opcoes(tabela: str) -> dict:
    """Retorna {nome: id} para usar em selectboxes."""
    rows = listar(tabela)
    return {r["nome"]: r["id"] for r in rows}

def opcoes_id_nome(tabela: str) -> dict:
    """Retorna {id: nome}."""
    rows = listar(tabela)
    return {r["id"]: r["nome"] for r in rows}
