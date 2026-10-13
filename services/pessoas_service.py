import sqlite3
from database.connection import get_connection

# ── Gerentes ───────────────────────────────────────────────────────────────────

def listar_gerentes():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM gerentes ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def adicionar_gerente(nome: str, email: str):
    conn = get_connection()
    conn.execute("INSERT INTO gerentes (nome, email) VALUES (?, ?)", (nome.strip(), email.strip()))
    conn.commit()
    conn.close()

    try:
        from services.email_service import notificar_cadastro_pessoa
        notificar_cadastro_pessoa("Gerente", nome.strip(), email.strip())
    except Exception as e:
        print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

def editar_gerente(id_: int, nome: str, email: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM gerentes WHERE id = ?", (id_,)).fetchone()
    if not row:
        conn.close()
        return

    nome_novo = nome.strip()
    email_novo = email.strip()

    alteracoes = []
    if row["nome"] != nome_novo:
        alteracoes.append({"campo": "Nome", "de": row["nome"], "para": nome_novo})
    if (row["email"] or "").strip() != email_novo:
        alteracoes.append({"campo": "E-mail", "de": row["email"], "para": email_novo})

    conn.execute("UPDATE gerentes SET nome=?, email=? WHERE id=?", (nome_novo, email_novo, id_))
    conn.commit()
    conn.close()

    if alteracoes:
        try:
            from services.email_service import notificar_alteracao_pessoa
            notificar_alteracao_pessoa("Gerente", nome_novo, alteracoes)
        except Exception as e:
            print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

def excluir_gerente(id_: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM gerentes WHERE id = ?", (id_,)).fetchone()
    if not row:
        conn.close()
        return

    nome = row["nome"]
    email = row["email"]

    try:
        conn.execute("DELETE FROM gerentes WHERE id=?", (id_,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Não é possível excluir o gerente '{nome}' pois existem vendedores vinculados a ele.")
    except Exception as e:
        conn.close()
        raise e
    finally:
        try:
            conn.close()
        except Exception:
            pass

    try:
        from services.email_service import notificar_exclusao_pessoa
        notificar_exclusao_pessoa("Gerente", nome, email)
    except Exception as e:
        print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

def opcoes_gerentes() -> dict:
    return {r["nome"]: r["id"] for r in listar_gerentes()}

# ── Coordenadores ──────────────────────────────────────────────────────────────

def listar_coordenadores():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM coordenadores ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def adicionar_coordenador(nome: str, email: str):
    conn = get_connection()
    conn.execute("INSERT INTO coordenadores (nome, email) VALUES (?, ?)", (nome.strip(), email.strip()))
    conn.commit()
    conn.close()

    try:
        from services.email_service import notificar_cadastro_pessoa
        notificar_cadastro_pessoa("Coordenador", nome.strip(), email.strip())
    except Exception as e:
        print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

def editar_coordenador(id_: int, nome: str, email: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM coordenadores WHERE id = ?", (id_,)).fetchone()
    if not row:
        conn.close()
        return

    nome_novo = nome.strip()
    email_novo = email.strip()

    alteracoes = []
    if row["nome"] != nome_novo:
        alteracoes.append({"campo": "Nome", "de": row["nome"], "para": nome_novo})
    if (row["email"] or "").strip() != email_novo:
        alteracoes.append({"campo": "E-mail", "de": row["email"], "para": email_novo})

    conn.execute("UPDATE coordenadores SET nome=?, email=? WHERE id=?", (nome_novo, email_novo, id_))
    conn.commit()
    conn.close()

    if alteracoes:
        try:
            from services.email_service import notificar_alteracao_pessoa
            notificar_alteracao_pessoa("Coordenador", nome_novo, alteracoes)
        except Exception as e:
            print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

def excluir_coordenador(id_: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM coordenadores WHERE id = ?", (id_,)).fetchone()
    if not row:
        conn.close()
        return

    nome = row["nome"]
    email = row["email"]

    try:
        conn.execute("DELETE FROM coordenadores WHERE id=?", (id_,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Não é possível excluir o coordenador '{nome}' pois existem vendedores vinculados a ele.")
    except Exception as e:
        conn.close()
        raise e
    finally:
        try:
            conn.close()
        except Exception:
            pass

    try:
        from services.email_service import notificar_exclusao_pessoa
        notificar_exclusao_pessoa("Coordenador", nome, email)
    except Exception as e:
        print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

def opcoes_coordenadores() -> dict:
    return {r["nome"]: r["id"] for r in listar_coordenadores()}

# ── Líderes de Parceiros ───────────────────────────────────────────────────────

def listar_lideres():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM lideres_parceiros ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def adicionar_lider(nome: str, email: str):
    conn = get_connection()
    conn.execute("INSERT INTO lideres_parceiros (nome, email) VALUES (?, ?)", (nome.strip(), email.strip()))
    conn.commit()
    conn.close()

    try:
        from services.email_service import notificar_cadastro_pessoa
        notificar_cadastro_pessoa("Líder de Parceiro", nome.strip(), email.strip())
    except Exception as e:
        print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

def editar_lider(id_: int, nome: str, email: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM lideres_parceiros WHERE id = ?", (id_,)).fetchone()
    if not row:
        conn.close()
        return

    nome_novo = nome.strip()
    email_novo = email.strip()

    alteracoes = []
    if row["nome"] != nome_novo:
        alteracoes.append({"campo": "Nome", "de": row["nome"], "para": nome_novo})
    if (row["email"] or "").strip() != email_novo:
        alteracoes.append({"campo": "E-mail", "de": row["email"], "para": email_novo})

    conn.execute("UPDATE lideres_parceiros SET nome=?, email=? WHERE id=?", (nome_novo, email_novo, id_))
    conn.commit()
    conn.close()

    if alteracoes:
        try:
            from services.email_service import notificar_alteracao_pessoa
            notificar_alteracao_pessoa("Líder de Parceiro", nome_novo, alteracoes)
        except Exception as e:
            print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

def excluir_lider(id_: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM lideres_parceiros WHERE id = ?", (id_,)).fetchone()
    if not row:
        conn.close()
        return

    nome = row["nome"]
    email = row["email"]

    try:
        conn.execute("DELETE FROM lideres_parceiros WHERE id=?", (id_,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Não é possível excluir o líder '{nome}' pois existem parceiros internos vinculados a ele.")
    except Exception as e:
        conn.close()
        raise e
    finally:
        try:
            conn.close()
        except Exception:
            pass

    try:
        from services.email_service import notificar_exclusao_pessoa
        notificar_exclusao_pessoa("Líder de Parceiro", nome, email)
    except Exception as e:
        print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

def opcoes_lideres() -> dict:
    return {r["nome"]: r["id"] for r in listar_lideres()}

# ── Parceiros Internos ─────────────────────────────────────────────────────────

def listar_parceiros():
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.*, l.nome AS lider_nome, l.email AS lider_email
        FROM parceiros_internos p
        LEFT JOIN lideres_parceiros l ON p.lider_id = l.id
        ORDER BY p.nome
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def adicionar_parceiro(nome: str, email: str, lider_id: int):
    conn = get_connection()
    conn.execute(
        "INSERT INTO parceiros_internos (nome, email, lider_id) VALUES (?, ?, ?)",
        (nome.strip(), email.strip(), lider_id)
    )
    conn.commit()
    conn.close()

    try:
        from services.email_service import notificar_cadastro_pessoa
        conn2 = get_connection()
        row_lider = conn2.execute("SELECT nome FROM lideres_parceiros WHERE id = ?", (lider_id,)).fetchone()
        conn2.close()
        lider_nome = row_lider["nome"] if row_lider else "Não informado"
        notificar_cadastro_pessoa("Parceiro Interno", nome.strip(), email.strip(), extra_info=f"Líder: {lider_nome}")
    except Exception as e:
        print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

def editar_parceiro(id_: int, nome: str, email: str, lider_id: int):
    conn = get_connection()
    row = conn.execute("""
        SELECT p.*, l.nome AS lider_nome
        FROM parceiros_internos p
        LEFT JOIN lideres_parceiros l ON p.lider_id = l.id
        WHERE p.id = ?
    """, (id_,)).fetchone()

    if not row:
        conn.close()
        return

    nome_novo = nome.strip()
    email_novo = email.strip()

    alteracoes = []
    if row["nome"] != nome_novo:
        alteracoes.append({"campo": "Nome", "de": row["nome"], "para": nome_novo})
    if (row["email"] or "").strip() != email_novo:
        alteracoes.append({"campo": "E-mail", "de": row["email"], "para": email_novo})
    if row["lider_id"] != lider_id:
        row_novo_lider = conn.execute("SELECT nome FROM lideres_parceiros WHERE id = ?", (lider_id,)).fetchone()
        novo_lider_nome = row_novo_lider["nome"] if row_novo_lider else "(Sem líder)"
        alteracoes.append({"campo": "Líder de Parceiro", "de": row["lider_nome"] or "(Sem líder)", "para": novo_lider_nome})

    conn.execute(
        "UPDATE parceiros_internos SET nome=?, email=?, lider_id=? WHERE id=?",
        (nome_novo, email_novo, lider_id, id_)
    )
    conn.commit()
    conn.close()

    if alteracoes:
        try:
            from services.email_service import notificar_alteracao_pessoa
            notificar_alteracao_pessoa("Parceiro Interno", nome_novo, alteracoes)
        except Exception as e:
            print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

def excluir_parceiro(id_: int):
    conn = get_connection()
    row = conn.execute("""
        SELECT p.*, l.nome AS lider_nome
        FROM parceiros_internos p
        LEFT JOIN lideres_parceiros l ON p.lider_id = l.id
        WHERE p.id = ?
    """, (id_,)).fetchone()

    if not row:
        conn.close()
        return

    nome = row["nome"]
    email = row["email"]
    lider_nome = row["lider_nome"]

    try:
        conn.execute("DELETE FROM parceiros_internos WHERE id=?", (id_,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Não é possível excluir o parceiro '{nome}' pois existem vendedores vinculados a ele.")
    except Exception as e:
        conn.close()
        raise e
    finally:
        try:
            conn.close()
        except Exception:
            pass

    try:
        from services.email_service import notificar_exclusao_pessoa
        extra = f"Líder: {lider_nome}" if lider_nome else None
        notificar_exclusao_pessoa("Parceiro Interno", nome, email, extra_info=extra)
    except Exception as e:
        print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

def opcoes_parceiros() -> dict:
    return {r["nome"]: r["id"] for r in listar_parceiros()}
