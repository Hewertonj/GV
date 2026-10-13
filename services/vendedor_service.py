from database.connection import get_connection
from datetime import date

# ── Listagem ───────────────────────────────────────────────────────────────────

def listar_vendedores(status=None, unidade_id=None, gerente_id=None,
                      ramo_id=None, segmento_id=None):
    conn = get_connection()
    query = """
        SELECT
            v.id, v.nome, v.email, v.status, v.data_entrada, v.data_saida,
            g.nome  AS gerente,       g.email  AS gerente_email,
            c.nome  AS coordenador,   c.email  AS coordenador_email,
            p.nome  AS parceiro,      p.email  AS parceiro_email,
            l.nome  AS lider_parceiro, l.email AS lider_parceiro_email,
            u.nome  AS unidade,
            r.nome  AS ramo,
            s.nome  AS segmento,
            v.substituto_id
        FROM vendedores v
        LEFT JOIN gerentes          g ON v.gerente_id          = g.id
        LEFT JOIN coordenadores     c ON v.coordenador_id      = c.id
        LEFT JOIN parceiros_internos p ON v.parceiro_interno_id = p.id
        LEFT JOIN lideres_parceiros  l ON p.lider_id            = l.id
        LEFT JOIN unidades           u ON v.unidade_id          = u.id
        LEFT JOIN ramos              r ON v.ramo_id             = r.id
        LEFT JOIN segmentos          s ON v.segmento_id         = s.id
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND v.status = ?"
        params.append(status)
    if unidade_id:
        query += " AND v.unidade_id = ?"
        params.append(unidade_id)
    if gerente_id:
        query += " AND v.gerente_id = ?"
        params.append(gerente_id)
    if ramo_id:
        query += " AND v.ramo_id = ?"
        params.append(ramo_id)
    if segmento_id:
        query += " AND v.segmento_id = ?"
        params.append(segmento_id)

    query += " ORDER BY v.nome"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_vendedor(id_: int):
    conn = get_connection()
    row = conn.execute("""
        SELECT
            v.*,
            g.nome  AS gerente_nome,       g.email  AS gerente_email,
            c.nome  AS coordenador_nome,   c.email  AS coordenador_email,
            p.nome  AS parceiro_nome,      p.email  AS parceiro_email,
            l.nome  AS lider_nome,         l.email  AS lider_email,
            u.nome  AS unidade_nome,
            r.nome  AS ramo_nome,
            s.nome  AS segmento_nome
        FROM vendedores v
        LEFT JOIN gerentes           g ON v.gerente_id          = g.id
        LEFT JOIN coordenadores      c ON v.coordenador_id      = c.id
        LEFT JOIN parceiros_internos p ON v.parceiro_interno_id = p.id
        LEFT JOIN lideres_parceiros  l ON p.lider_id            = l.id
        LEFT JOIN unidades           u ON v.unidade_id          = u.id
        LEFT JOIN ramos              r ON v.ramo_id             = r.id
        LEFT JOIN segmentos          s ON v.segmento_id         = s.id
        WHERE v.id = ?
    """, (id_,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── CRUD ───────────────────────────────────────────────────────────────────────

def adicionar_vendedor(nome, email, gerente_id, coordenador_id,
                       parceiro_id, unidade_id, ramo_id, segmento_id,
                       data_entrada=None):
    if data_entrada is None:
        data_entrada = str(date.today())
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO vendedores
            (nome, email, gerente_id, coordenador_id, parceiro_interno_id,
             unidade_id, ramo_id, segmento_id, status, data_entrada)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ativo', ?)
    """, (nome.strip(), email.strip(), gerente_id, coordenador_id,
          parceiro_id, unidade_id, ramo_id, segmento_id, data_entrada))
    novo_id = cur.lastrowid
    conn.commit()
    conn.close()

    try:
        from services.email_service import notificar_cadastro_vendedor
        v_detalhes = buscar_vendedor(novo_id)
        if v_detalhes:
            notificar_cadastro_vendedor(v_detalhes)
    except Exception as e:
        print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

    return novo_id


def editar_vendedor(id_, nome, email, gerente_id, coordenador_id,
                    parceiro_id, unidade_id, ramo_id, segmento_id):
    v_antigo = buscar_vendedor(id_)
    conn = get_connection()
    conn.execute("""
        UPDATE vendedores
        SET nome=?, email=?, gerente_id=?, coordenador_id=?,
            parceiro_interno_id=?, unidade_id=?, ramo_id=?, segmento_id=?
        WHERE id=?
    """, (nome.strip(), email.strip(), gerente_id, coordenador_id,
          parceiro_id, unidade_id, ramo_id, segmento_id, id_))
    conn.commit()
    conn.close()

    v_novo = buscar_vendedor(id_)
    if v_antigo and v_novo:
        alteracoes = []
        campos = [
            ("Nome", "nome"),
            ("E-mail", "email"),
            ("Gerente", "gerente_nome"),
            ("Coordenador", "coordenador_nome"),
            ("Parceiro Interno", "parceiro_nome"),
            ("Unidade", "unidade_nome"),
            ("Ramo", "ramo_nome"),
            ("Segmento", "segmento_nome"),
        ]
        for label, chave in campos:
            val_antigo = v_antigo.get(chave)
            val_novo = v_novo.get(chave)
            if val_antigo != val_novo:
                alteracoes.append({"campo": label, "de": val_antigo, "para": val_novo})

        if alteracoes:
            try:
                from services.email_service import notificar_alteracao_vendedor
                notificar_alteracao_vendedor(v_novo["nome"], alteracoes)
            except Exception as e:
                print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")


def desativar_vendedor(id_: int):
    v = buscar_vendedor(id_)
    data_saida = str(date.today())
    conn = get_connection()
    conn.execute(
        "UPDATE vendedores SET status='inativo', data_saida=? WHERE id=?",
        (data_saida, id_)
    )
    conn.commit()
    conn.close()

    if v:
        try:
            from services.email_service import notificar_inativacao_vendedor
            notificar_inativacao_vendedor(v["nome"], v.get("email"), data_saida=data_saida)
        except Exception as e:
            print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")


def excluir_vendedor(id_: int):
    conn = get_connection()
    conn.execute("DELETE FROM vendedores WHERE id=?", (id_,))
    conn.commit()
    conn.close()


def _update_status_datas(id_: int, status: str, data_entrada: str, data_saida=None):
    """Atualiza status e datas de um vendedor. Usado pela tela de edição."""
    v_antigo = buscar_vendedor(id_)
    conn = get_connection()
    conn.execute(
        "UPDATE vendedores SET status=?, data_entrada=?, data_saida=? WHERE id=?",
        (status, data_entrada, data_saida, id_)
    )
    conn.commit()
    conn.close()

    if v_antigo and v_antigo.get("status") != status and status == "inativo":
        try:
            from services.email_service import notificar_inativacao_vendedor
            notificar_inativacao_vendedor(v_antigo["nome"], v_antigo.get("email"), data_saida=data_saida)
        except Exception as e:
            print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")


# ── Substituição ───────────────────────────────────────────────────────────────

def registrar_substituicao(vendedor_saindo_id: int, novo_nome: str,
                            novo_email: str, gerente_id, coordenador_id,
                            parceiro_id, unidade_id, ramo_id, segmento_id,
                            motivo: str, data_sub: str):
    v_saindo = buscar_vendedor(vendedor_saindo_id)
    conn = get_connection()
    cur = conn.cursor()

    # 1. Marca vendedor saindo como substituído
    cur.execute("""
        UPDATE vendedores
        SET status='substituído', data_saida=?
        WHERE id=?
    """, (data_sub, vendedor_saindo_id))

    # 2. Insere novo vendedor
    cur.execute("""
        INSERT INTO vendedores
            (nome, email, gerente_id, coordenador_id, parceiro_interno_id,
             unidade_id, ramo_id, segmento_id, status, data_entrada)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ativo', ?)
    """, (novo_nome.strip(), novo_email.strip(), gerente_id, coordenador_id,
          parceiro_id, unidade_id, ramo_id, segmento_id, data_sub))
    novo_id = cur.lastrowid

    # 3. Vincula substituto
    cur.execute(
        "UPDATE vendedores SET substituto_id=? WHERE id=?",
        (novo_id, vendedor_saindo_id)
    )

    # 4. Registra histórico
    cur.execute("""
        INSERT INTO historico_substituicoes
            (vendedor_saindo_id, vendedor_entrando_id, data_substituicao, motivo)
        VALUES (?, ?, ?, ?)
    """, (vendedor_saindo_id, novo_id, data_sub, motivo))

    conn.commit()
    conn.close()

    try:
        from services.email_service import notificar_substituicao_vendedor
        v_entrando = buscar_vendedor(novo_id)
        saindo_nome = v_saindo["nome"] if v_saindo else f"Vendedor #{vendedor_saindo_id}"
        unidade = v_entrando.get("unidade_nome") if v_entrando else None
        gerente = v_entrando.get("gerente_nome") if v_entrando else None
        notificar_substituicao_vendedor(
            saindo_nome=saindo_nome,
            entrando_nome=novo_nome.strip(),
            data_sub=data_sub,
            motivo=motivo,
            unidade=unidade,
            gerente=gerente
        )
    except Exception as e:
        print(f"[EmailService Aviso] Falha ao disparar notificação: {e}")

    return novo_id
