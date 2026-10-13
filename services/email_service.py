import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from database.connection import get_connection

# ── Configurações SMTP ─────────────────────────────────────────────────────────

def obter_config_smtp() -> dict:
    """
    Retorna as configurações de SMTP salvas no banco de dados.
    Se não existirem no banco, tenta carregar do st.secrets['email'].
    """
    conn = get_connection()
    row = conn.execute("SELECT * FROM email_config WHERE id = 1").fetchone()
    conn.close()

    if row and row["smtp_server"]:
        return {
            "smtp_server": row["smtp_server"] or "",
            "smtp_port": int(row["smtp_port"] or 587),
            "remetente": row["remetente"] or "",
            "senha": row["senha"] or "",
            "usar_tls": bool(row["usar_tls"] if row["usar_tls"] is not None else 1),
        }

    # Fallback para st.secrets caso configurado via secrets.toml
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "email" in st.secrets:
            sec = st.secrets["email"]
            return {
                "smtp_server": sec.get("smtp_server", ""),
                "smtp_port": int(sec.get("smtp_port", 587)),
                "remetente": sec.get("remetente", ""),
                "senha": sec.get("senha", ""),
                "usar_tls": bool(sec.get("usar_tls", True)),
            }
    except Exception:
        pass

    return {
        "smtp_server": "",
        "smtp_port": 587,
        "remetente": "",
        "senha": "",
        "usar_tls": True,
    }


def salvar_config_smtp(smtp_server: str, smtp_port: int, remetente: str, senha: str, usar_tls: bool = True) -> tuple[bool, str]:
    """Salva as configurações de SMTP no banco de dados (tabela email_config)."""
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO email_config (id, smtp_server, smtp_port, remetente, senha, usar_tls)
            VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                smtp_server = excluded.smtp_server,
                smtp_port   = excluded.smtp_port,
                remetente   = excluded.remetente,
                senha       = excluded.senha,
                usar_tls    = excluded.usar_tls
        """, (smtp_server.strip(), int(smtp_port), remetente.strip(), senha.strip(), 1 if usar_tls else 0))
        conn.commit()
        conn.close()
        return True, "Configurações de SMTP salvas com sucesso!"
    except Exception as e:
        return False, f"Erro ao salvar configurações: {e}"


# ── Destinatários de Notificação ──────────────────────────────────────────────

def listar_destinatarios(apenas_ativos: bool = False, tipo: str = None) -> list[dict]:
    """
    Lista destinatários cadastrados.
    tipo pode ser: 'vendedor', 'gerente', 'coordenador', 'parceiro'
    """
    conn = get_connection()
    query = "SELECT * FROM email_destinatarios WHERE 1=1"
    params = []

    if apenas_ativos:
        query += " AND ativo = 1"

    if tipo == "vendedor":
        query += " AND recebe_vendedor = 1"
    elif tipo == "gerente":
        query += " AND recebe_gerente = 1"
    elif tipo == "coordenador":
        query += " AND recebe_coordenador = 1"
    elif tipo == "parceiro":
        query += " AND recebe_parceiro = 1"

    query += " ORDER BY nome ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_destinatario(nome: str, email: str,
                           recebe_vendedor: bool = True,
                           recebe_gerente: bool = True,
                           recebe_coordenador: bool = True,
                           recebe_parceiro: bool = True) -> tuple[bool, str]:
    """Adiciona um novo destinatário de alertas."""
    nome = nome.strip()
    email = email.strip().lower()
    if not nome or not email:
        return False, "Nome e e-mail são obrigatórios."
    if "@" not in email or "." not in email:
        return False, "E-mail inválido."

    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO email_destinatarios
                (nome, email, ativo, recebe_vendedor, recebe_gerente, recebe_coordenador, recebe_parceiro)
            VALUES (?, ?, 1, ?, ?, ?, ?)
        """, (nome, email,
              1 if recebe_vendedor else 0,
              1 if recebe_gerente else 0,
              1 if recebe_coordenador else 0,
              1 if recebe_parceiro else 0))
        conn.commit()
        conn.close()
        return True, f"Destinatário {nome} cadastrado com sucesso!"
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return False, f"O e-mail '{email}' já está cadastrado."
        return False, f"Erro ao adicionar destinatário: {e}"


def editar_destinatario(id_: int, nome: str, email: str, ativo: bool,
                        recebe_vendedor: bool, recebe_gerente: bool,
                        recebe_coordenador: bool, recebe_parceiro: bool) -> tuple[bool, str]:
    """Edita um destinatário existente."""
    nome = nome.strip()
    email = email.strip().lower()
    if not nome or not email:
        return False, "Nome e e-mail são obrigatórios."

    try:
        conn = get_connection()
        conn.execute("""
            UPDATE email_destinatarios
            SET nome = ?, email = ?, ativo = ?,
                recebe_vendedor = ?, recebe_gerente = ?,
                recebe_coordenador = ?, recebe_parceiro = ?
            WHERE id = ?
        """, (nome, email,
              1 if ativo else 0,
              1 if recebe_vendedor else 0,
              1 if recebe_gerente else 0,
              1 if recebe_coordenador else 0,
              1 if recebe_parceiro else 0,
              id_))
        conn.commit()
        conn.close()
        return True, f"Destinatário atualizado com sucesso!"
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return False, f"O e-mail '{email}' já está em uso por outro cadastro."
        return False, f"Erro ao atualizar: {e}"


def alternar_status_destinatario(id_: int, novo_status: bool) -> tuple[bool, str]:
    """Ativa ou desativa um destinatário."""
    try:
        conn = get_connection()
        conn.execute("UPDATE email_destinatarios SET ativo = ? WHERE id = ?", (1 if novo_status else 0, id_))
        conn.commit()
        conn.close()
        return True, "Status alterado com sucesso!"
    except Exception as e:
        return False, f"Erro ao alterar status: {e}"


def excluir_destinatario(id_: int) -> tuple[bool, str]:
    """Remove um destinatário."""
    try:
        conn = get_connection()
        conn.execute("DELETE FROM email_destinatarios WHERE id = ?", (id_,))
        conn.commit()
        conn.close()
        return True, "Destinatário removido com sucesso!"
    except Exception as e:
        return False, f"Erro ao excluir: {e}"


# ── Motor de Envio de E-mails ──────────────────────────────────────────────────

def _gerar_html(titulo: str, subtitulo: str, detalhes: list[tuple[str, str]], tag_cor: str = "#0E5BB3", tag_texto: str = "Movimentação") -> str:
    """Gera um template HTML responsivo, moderno e padronizado nas cores do sistema."""
    linhas_tabela = ""
    for label, valor in detalhes:
        linhas_tabela += f"""
        <tr>
            <td style="padding: 10px 14px; font-weight: 600; color: #475569; width: 35%; border-bottom: 1px solid #f1f5f9;">{label}</td>
            <td style="padding: 10px 14px; color: #0f172a; font-weight: 500; border-bottom: 1px solid #f1f5f9;">{valor}</td>
        </tr>
        """

    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{titulo}</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #EDF7F6; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; color: #1e293b;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #EDF7F6; padding: 30px 15px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 14px; overflow: hidden; border: 1px solid #e2e8f0;">
                        <!-- Header -->
                        <tr>
                            <td bgcolor="{tag_cor}" style="background-color: {tag_cor}; padding: 26px 30px; text-align: left;">
                                <div style="display: inline-block; background-color: transparent; border: 1px solid #ffffff; color: #ffffff; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px;">
                                    {tag_texto}
                                </div>
                                <h1 style="color: #ffffff; font-size: 20px; font-weight: 700; margin: 0 0 6px 0; line-height: 1.3; font-family: 'Segoe UI', Arial, sans-serif;">
                                    {titulo}
                                </h1>
                                <p style="color: #ffffff; font-size: 13px; margin: 0; line-height: 1.4; opacity: 0.9; font-family: 'Segoe UI', Arial, sans-serif;">
                                    {subtitulo}
                                </p>
                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td style="padding: 28px 30px;">
                                <p style="margin: 0 0 16px 0; font-size: 14px; color: #334155; line-height: 1.5;">
                                    Uma nova movimentação foi registrada no <strong>Sistema de Gestão de Vendedores</strong>. Confira os detalhes abaixo:
                                </p>

                                <table width="100%" cellspacing="0" cellpadding="0" style="border-collapse: collapse; background-color: #f8fafc; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; font-size: 13px; margin-bottom: 22px;">
                                    {linhas_tabela}
                                </table>

                                <div style="background-color: #f0fdf4; border-left: 4px solid #088012; padding: 12px 16px; border-radius: 6px; font-size: 12px; color: #166534; line-height: 1.5;">
                                    ℹ️ <em>Registro automático gerado pelo sistema em <strong>{agora}</strong>.</em>
                                </div>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8fafc; padding: 18px 30px; text-align: center; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b;">
                                <p style="margin: 0 0 4px 0; font-weight: 600; color: #0E5BB3;">
                                    Atenciosamente, Equipe de Business Intelligence
                                </p>
                                <p style="margin: 0; font-size: 11px; color: #94a3b8;">
                                    Email enviado automaticamente.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html


def _enviar_email_sync(destinatarios: list[str], assunto: str, corpo_html: str) -> tuple[bool, str]:
    """Executa o envio síncrono via SMTP."""
    destinatarios_validos = [d.strip() for d in destinatarios if d and "@" in d]
    if not destinatarios_validos:
        return False, "Nenhum destinatário válido informado."

    config = obter_config_smtp()
    smtp_server = config.get("smtp_server", "").strip()
    smtp_port = config.get("smtp_port", 587)
    remetente = config.get("remetente", "").strip()
    senha = config.get("senha", "").strip()
    usar_tls = config.get("usar_tls", True)

    if not smtp_server or not remetente or not senha:
        msg_erro = "Configuração SMTP incompleta. Configure servidor, remetente e senha na aba Configurações > Notificações."
        print(f"[EmailService Aviso] {msg_erro}")
        return False, msg_erro

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = f"Gestão de Vendedores <{remetente}>"
        msg["To"] = ", ".join(destinatarios_validos)

        # Anexa parte HTML
        msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        porta = int(smtp_port)
        senha_limpa = senha.replace(" ", "") if (len(senha.replace(" ", "")) == 16 or "gmail" in smtp_server.lower()) else senha

        if porta == 465:
            server = smtplib.SMTP_SSL(smtp_server, porta, timeout=15)
            server.ehlo()
        else:
            server = smtplib.SMTP(smtp_server, porta, timeout=15)
            server.ehlo()
            # Garante STARTTLS para porta 587 ou quando o servidor anunciar suporte
            if usar_tls or porta == 587 or server.has_extn("starttls"):
                server.starttls()
                server.ehlo()

        # Autenticação
        try:
            server.login(remetente, senha_limpa)
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPServerDisconnected):
            if senha_limpa != senha:
                server.login(remetente, senha)
            else:
                raise

        server.sendmail(remetente, destinatarios_validos, msg.as_string())
        server.quit()
        assunto_limpo = assunto.encode('ascii', 'ignore').decode()
        print(f"[EmailService Sucesso] E-mail '{assunto_limpo}' enviado para {len(destinatarios_validos)} destinatario(s).")
        return True, f"E-mail enviado com sucesso para {len(destinatarios_validos)} destinatário(s)!"

    except smtplib.SMTPAuthenticationError as e:
        err = f"Falha de autenticação ({e.smtp_code}): Verifique se o e-mail remetente '{remetente}' e a Senha de Aplicativo estão corretos. (No Gmail, não use a senha pessoal da conta, use uma Senha de App de 16 caracteres gerada na Conta Google)."
        print(f"[EmailService Erro] {err}")
        return False, err
    except smtplib.SMTPServerDisconnected as e:
        err = f"O servidor encerrou a conexão durante o login. Isso quase sempre indica que a Senha de Aplicativo do Google está incorreta ou foi revogada (código 535 BadCredentials), ou que a conta bloqueou o acesso."
        print(f"[EmailService Erro] {err}")
        return False, err
    except smtplib.SMTPNotSupportedError as e:
        err = f"Extensão não suportada ({str(e)}). Verifique a porta do servidor (587 para STARTTLS ou 465 para SSL)."
        print(f"[EmailService Erro] {err}")
        return False, err
    except smtplib.SMTPConnectError as e:
        err = f"Não foi possível conectar ao servidor SMTP {smtp_server}:{smtp_port}. Verifique o endereço e a porta."
        print(f"[EmailService Erro] {err}")
        return False, err
    except Exception as e:
        err = f"Erro ao enviar e-mail: {str(e)}"
        print(f"[EmailService Erro] {err}")
        return False, err


def enviar_email_async(destinatarios: list[str], assunto: str, corpo_html: str):
    """Dispara o envio de e-mail em segundo plano para não travar a interface Streamlit."""
    if not destinatarios:
        return
    t = threading.Thread(
        target=_enviar_email_sync,
        args=(destinatarios, assunto, corpo_html),
        daemon=True
    )
    t.start()


def enviar_email_teste(destinatario_teste: str) -> tuple[bool, str]:
    """Envia um e-mail de teste de forma síncrona para validar as configurações SMTP."""
    destinatario_teste = destinatario_teste.strip()
    if not destinatario_teste or "@" not in destinatario_teste:
        return False, "Informe um e-mail de teste válido."

    assunto = "✅ [Teste] Notificação de Gestão de Vendedores"
    detalhes = [
        ("Status da Conexão", "Conexão SMTP estabelecida com sucesso!"),
        ("E-mail de Destino", destinatario_teste),
        ("Data do Teste", datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        ("Canal de Envio", "Serviço de Alertas Automáticos"),
    ]
    html = _gerar_html(
        titulo="Teste de Notificação do Sistema",
        subtitulo="Seu sistema de gestão está configurado e pronto para disparar alertas.",
        detalhes=detalhes,
        tag_cor="#088012",
        tag_texto="Configuração Validada"
    )
    return _enviar_email_sync([destinatario_teste], assunto, html)


# ── Gatilhos de Notificação (Eventos de Movimentação) ──────────────────────────

def notificar_cadastro_vendedor(vendedor: dict):
    """Disparado quando um novo vendedor é cadastrado."""
    destinatarios = [d["email"] for d in listar_destinatarios(apenas_ativos=True, tipo="vendedor")]
    if not destinatarios:
        return

    nome = vendedor.get("nome", "Novo Vendedor")
    assunto = f"📢 [Gestão de Vendedores] Novo Vendedor Cadastrado: {nome}"
    detalhes = [
        ("Vendedor", nome),
        ("E-mail", vendedor.get("email") or "—"),
        ("Data de Entrada", vendedor.get("data_entrada") or "—"),
        ("Unidade", vendedor.get("unidade_nome") or vendedor.get("unidade") or "—"),
        ("Ramo", vendedor.get("ramo_nome") or vendedor.get("ramo") or "—"),
        ("Segmento", vendedor.get("segmento_nome") or vendedor.get("segmento") or "—"),
        ("Gerente", vendedor.get("gerente_nome") or vendedor.get("gerente") or "—"),
        ("Coordenador", vendedor.get("coordenador_nome") or vendedor.get("coordenador") or "—"),
        ("Parceiro Interno", vendedor.get("parceiro_nome") or vendedor.get("parceiro") or "—"),
    ]
    html = _gerar_html(
        titulo="Novo Vendedor Cadastrado",
        subtitulo=f"O vendedor <strong>{nome}</strong> foi integrado à equipe.",
        detalhes=detalhes,
        tag_cor="#088012",
        tag_texto="Novo Cadastro"
    )
    enviar_email_async(destinatarios, assunto, html)


def notificar_inativacao_vendedor(nome: str, email: str = None, data_saida: str = None, motivo: str = None):
    """Disparado quando um vendedor tem seu status alterado para inativo."""
    destinatarios = [d["email"] for d in listar_destinatarios(apenas_ativos=True, tipo="vendedor")]
    if not destinatarios:
        return

    assunto = f"⚠️ [Gestão de Vendedores] Vendedor Desativado: {nome}"
    detalhes = [
        ("Vendedor", nome),
        ("E-mail", email or "—"),
        ("Status Atual", "<span style='color:#dc2626;font-weight:700;'>Inativo</span>"),
        ("Data de Desativação", data_saida or datetime.now().strftime("%d/%m/%Y")),
    ]
    if motivo:
        detalhes.append(("Motivo", motivo))

    html = _gerar_html(
        titulo="Inativação de Vendedor",
        subtitulo=f"O vendedor <strong>{nome}</strong> foi marcado como inativo no sistema.",
        detalhes=detalhes,
        tag_cor="#dc2626",
        tag_texto="Inativação"
    )
    enviar_email_async(destinatarios, assunto, html)


def notificar_substituicao_vendedor(saindo_nome: str, entrando_nome: str, data_sub: str, motivo: str, unidade: str = None, gerente: str = None):
    """Disparado quando ocorre uma substituição de vendedor."""
    destinatarios = [d["email"] for d in listar_destinatarios(apenas_ativos=True, tipo="vendedor")]
    if not destinatarios:
        return

    assunto = f"🔄 [Gestão de Vendedores] Substituição: {saindo_nome} ➔ {entrando_nome}"
    detalhes = [
        ("Vendedor que Saiu", f"<span style='color:#dc2626;font-weight:600;'>{saindo_nome}</span>"),
        ("Novo Vendedor", f"<span style='color:#088012;font-weight:600;'>{entrando_nome}</span>"),
        ("Data da Substituição", data_sub or datetime.now().strftime("%d/%m/%Y")),
        ("Motivo", motivo or "Não informado"),
    ]
    if unidade:
        detalhes.append(("Unidade", unidade))
    if gerente:
        detalhes.append(("Gerente", gerente))

    html = _gerar_html(
        titulo="Substituição de Vendedor Realizada",
        subtitulo=f"Transição registrada: <strong>{saindo_nome}</strong> foi substituído por <strong>{entrando_nome}</strong>.",
        detalhes=detalhes,
        tag_cor="#0E5BB3",
        tag_texto="Substituição"
    )
    enviar_email_async(destinatarios, assunto, html)


def notificar_alteracao_vendedor(nome: str, alteracoes: list[dict]):
    """
    Disparado quando vínculos ou dados principais de um vendedor são alterados.
    alteracoes é uma lista de dicts: [{'campo': 'Gerente', 'de': 'Carlos', 'para': 'Marcos'}]
    """
    destinatarios = [d["email"] for d in listar_destinatarios(apenas_ativos=True, tipo="vendedor")]
    if not destinatarios or not alteracoes:
        return

    assunto = f"✏️ [Gestão de Vendedores] Alteração Cadastral: {nome}"
    detalhes = [("Vendedor", f"<strong>{nome}</strong>")]
    for alt in alteracoes:
        campo = alt.get("campo", "Campo")
        de = alt.get("de") or "(não definido)"
        para = alt.get("para") or "(não definido)"
        detalhes.append((campo, f"<del style='color:#94a3b8;'>{de}</del> ➔ <strong style='color:#0E5BB3;'>{para}</strong>"))

    html = _gerar_html(
        titulo="Alteração de Vínculos / Dados Cadastrais",
        subtitulo=f"Os dados do vendedor <strong>{nome}</strong> foram atualizados no sistema.",
        detalhes=detalhes,
        tag_cor="#0E5BB3",
        tag_texto="Atualização"
    )
    enviar_email_async(destinatarios, assunto, html)


def notificar_cadastro_pessoa(tipo_pessoa: str, nome: str, email: str, extra_info: str = None):
    """
    Disparado quando um novo Gerente, Coordenador ou Parceiro é cadastrado.
    tipo_pessoa: 'Gerente', 'Coordenador', 'Líder de Parceiro', 'Parceiro Interno'
    """
    filtro_tipo = "gerente"
    if tipo_pessoa == "Coordenador":
        filtro_tipo = "coordenador"
    elif "Parceiro" in tipo_pessoa or "Líder" in tipo_pessoa:
        filtro_tipo = "parceiro"

    destinatarios = [d["email"] for d in listar_destinatarios(apenas_ativos=True, tipo=filtro_tipo)]
    if not destinatarios:
        return

    assunto = f"👤 [Gestão de Vendedores] Novo(a) {tipo_pessoa} Cadastrado(a): {nome}"
    detalhes = [
        ("Função", tipo_pessoa),
        ("Nome", nome),
        ("E-mail", email or "—"),
    ]
    if extra_info:
        detalhes.append(("Informações Adicionais", extra_info))

    html = _gerar_html(
        titulo=f"Novo(a) {tipo_pessoa} Cadastrado(a)",
        subtitulo=f"O perfil de <strong>{nome}</strong> foi adicionado ao sistema.",
        detalhes=detalhes,
        tag_cor="#088012",
        tag_texto="Novo Membro"
    )
    enviar_email_async(destinatarios, assunto, html)


def notificar_alteracao_pessoa(tipo_pessoa: str, nome: str, alteracoes: list[dict], extra_info: str = None):
    """
    Disparado quando ocorrem alterações cadastrais em Gerentes, Coordenadores, Líderes ou Parceiros.
    alteracoes é uma lista de dicts: [{'campo': 'Nome', 'de': 'Antigo', 'para': 'Novo'}]
    """
    filtro_tipo = "gerente"
    if tipo_pessoa == "Coordenador":
        filtro_tipo = "coordenador"
    elif "Parceiro" in tipo_pessoa or "Líder" in tipo_pessoa:
        filtro_tipo = "parceiro"

    destinatarios = [d["email"] for d in listar_destinatarios(apenas_ativos=True, tipo=filtro_tipo)]
    if not destinatarios or not alteracoes:
        return

    assunto = f"✏️ [Gestão de Vendedores] Alteração Cadastral ({tipo_pessoa}): {nome}"
    detalhes = [
        ("Função / Cargo", tipo_pessoa),
        ("Membro", f"<strong>{nome}</strong>"),
    ]
    for alt in alteracoes:
        campo = alt.get("campo", "Campo")
        de = alt.get("de") or "(não informado)"
        para = alt.get("para") or "(não informado)"
        detalhes.append((campo, f"<del style='color:#94a3b8;'>{de}</del> ➔ <strong style='color:#0E5BB3;'>{para}</strong>"))

    if extra_info:
        detalhes.append(("Informações Adicionais", extra_info))

    html = _gerar_html(
        titulo=f"Alteração Cadastral — {tipo_pessoa}",
        subtitulo=f"Os dados de <strong>{nome}</strong> foram atualizados na base de internos.",
        detalhes=detalhes,
        tag_cor="#0E5BB3",
        tag_texto="Edição de Interno"
    )
    enviar_email_async(destinatarios, assunto, html)


def notificar_exclusao_pessoa(tipo_pessoa: str, nome: str, email: str = None, extra_info: str = None):
    """
    Disparado quando um Gerente, Coordenador, Líder ou Parceiro Interno é excluído do sistema.
    """
    filtro_tipo = "gerente"
    if tipo_pessoa == "Coordenador":
        filtro_tipo = "coordenador"
    elif "Parceiro" in tipo_pessoa or "Líder" in tipo_pessoa:
        filtro_tipo = "parceiro"

    destinatarios = [d["email"] for d in listar_destinatarios(apenas_ativos=True, tipo=filtro_tipo)]
    if not destinatarios:
        return

    assunto = f"🗑️ [Gestão de Vendedores] {tipo_pessoa} Excluído(a): {nome}"
    detalhes = [
        ("Função / Cargo", tipo_pessoa),
        ("Nome", nome),
        ("E-mail", email or "—"),
        ("Status", "<span style='color:#dc2626;font-weight:700;'>Removido(a) da Base de Internos</span>"),
    ]
    if extra_info:
        detalhes.append(("Informações Adicionais", extra_info))

    html = _gerar_html(
        titulo=f"{tipo_pessoa} Excluído(a) do Sistema",
        subtitulo=f"O registro de <strong>{nome}</strong> foi removido da base de internos.",
        detalhes=detalhes,
        tag_cor="#dc2626",
        tag_texto="Exclusão de Interno"
    )
    enviar_email_async(destinatarios, assunto, html)


def notificar_atualizacao_massa(itens_alterados: list[dict], total_processados: int = None):
    """
    Disparado após uma operação de atualização em massa via planilha.
    itens_alterados: lista de dicts [{'nome': '...', 'alteracoes': [{'campo': '...', 'de': '...', 'para': '...'}]}]
    """
    destinatarios = [d["email"] for d in listar_destinatarios(apenas_ativos=True, tipo="vendedor")]
    if not destinatarios or not itens_alterados:
        return

    qtd_alterados = len(itens_alterados)
    assunto = f"📦 [Gestão de Vendedores] Atualização em Massa: {qtd_alterados} vendedor(es) alterado(s)"

    # Monta linhas da tabela consolidada
    linhas_tabela = ""
    for item in itens_alterados:
        nome_vendedor = item.get("nome", "Vendedor")
        detalhes_alt = []
        for alt in item.get("alteracoes", []):
            campo = alt.get("campo", "Campo")
            de = alt.get("de") or "(não definido)"
            para = alt.get("para") or "(não definido)"
            detalhes_alt.append(
                f"<strong>{campo}:</strong> <del style='color:#94a3b8;'>{de}</del> ➔ <span style='color:#0E5BB3;font-weight:600;'>{para}</span>"
            )

        texto_mudancas = "<br>".join(detalhes_alt) if detalhes_alt else "Atualizado"

        linhas_tabela += f"""
        <tr>
            <td style="padding: 10px 14px; font-weight: 600; color: #0f172a; border-bottom: 1px solid #f1f5f9; vertical-align: top; width: 35%;">{nome_vendedor}</td>
            <td style="padding: 10px 14px; color: #334155; font-size: 13px; border-bottom: 1px solid #f1f5f9; vertical-align: top;">{texto_mudancas}</td>
        </tr>
        """

    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
    subtitulo_info = f"Foram atualizados <strong>{qtd_alterados}</strong> vendedor(es) via planilha."
    if total_processados:
        subtitulo_info += f" (Total de linhas analisadas na planilha: {total_processados})"

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Atualização em Massa</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #EDF7F6; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; color: #1e293b;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #EDF7F6; padding: 30px 15px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="100%" style="max-width: 650px; background-color: #ffffff; border-radius: 14px; overflow: hidden; border: 1px solid #e2e8f0;">
                        <!-- Header -->
                        <tr>
                            <td bgcolor="#0E5BB3" style="background-color: #0E5BB3; padding: 26px 30px; text-align: left;">
                                <div style="display: inline-block; background-color: transparent; border: 1px solid #ffffff; color: #ffffff; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px;">
                                    Operação em Massa
                                </div>
                                <h1 style="color: #ffffff; font-size: 20px; font-weight: 700; margin: 0 0 6px 0; line-height: 1.3;">
                                    Atualização Cadastral em Massa Concluída
                                </h1>
                                <p style="color: #ffffff; font-size: 13px; margin: 0; line-height: 1.4; opacity: 0.9;">
                                    {subtitulo_info}
                                </p>
                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td style="padding: 28px 30px;">
                                <p style="margin: 0 0 16px 0; font-size: 14px; color: #334155; line-height: 1.5;">
                                    As seguintes alterações foram detectadas e aplicadas na base de dados:
                                </p>

                                <table width="100%" cellspacing="0" cellpadding="0" style="border-collapse: collapse; background-color: #f8fafc; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; font-size: 13px; margin-bottom: 22px;">
                                    <thead>
                                        <tr style="background-color: #e2e8f0;">
                                            <th style="padding: 10px 14px; text-align: left; font-size: 12px; font-weight: 700; color: #475569;">Vendedor</th>
                                            <th style="padding: 10px 14px; text-align: left; font-size: 12px; font-weight: 700; color: #475569;">Alterações Realizadas (De ➔ Para)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {linhas_tabela}
                                    </tbody>
                                </table>

                                <div style="background-color: #f0fdf4; border-left: 4px solid #088012; padding: 12px 16px; border-radius: 6px; font-size: 12px; color: #166534; line-height: 1.5;">
                                    ℹ️ <em>Registro automático gerado pelo sistema em <strong>{agora}</strong>.</em>
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    enviar_email_async(destinatarios, assunto, html)


