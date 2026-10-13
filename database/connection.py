import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vendedores.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS gerentes (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            nome  TEXT NOT NULL,
            email TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS coordenadores (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            nome  TEXT NOT NULL,
            email TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS lideres_parceiros (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            nome  TEXT NOT NULL,
            email TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS parceiros_internos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nome      TEXT NOT NULL,
            email     TEXT NOT NULL,
            lider_id  INTEGER REFERENCES lideres_parceiros(id)
        );

        CREATE TABLE IF NOT EXISTS unidades (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS ramos (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS segmentos (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS vendedores (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            nome                TEXT NOT NULL,
            email               TEXT NOT NULL,
            gerente_id          INTEGER REFERENCES gerentes(id),
            coordenador_id      INTEGER REFERENCES coordenadores(id),
            parceiro_interno_id INTEGER REFERENCES parceiros_internos(id),
            unidade_id          INTEGER REFERENCES unidades(id),
            ramo_id             INTEGER REFERENCES ramos(id),
            segmento_id         INTEGER REFERENCES segmentos(id),
            status              TEXT NOT NULL DEFAULT 'ativo',
            data_entrada        TEXT NOT NULL,
            data_saida          TEXT,
            substituto_id       INTEGER REFERENCES vendedores(id)
        );

        CREATE TABLE IF NOT EXISTS historico_substituicoes (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            vendedor_saindo_id   INTEGER REFERENCES vendedores(id),
            vendedor_entrando_id INTEGER REFERENCES vendedores(id),
            data_substituicao    TEXT NOT NULL,
            motivo               TEXT
        );

        CREATE TABLE IF NOT EXISTS email_destinatarios (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome                 TEXT NOT NULL,
            email                TEXT NOT NULL UNIQUE,
            ativo                INTEGER DEFAULT 1,
            recebe_vendedor      INTEGER DEFAULT 1,
            recebe_gerente       INTEGER DEFAULT 1,
            recebe_coordenador   INTEGER DEFAULT 1,
            recebe_parceiro      INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS email_config (
            id                   INTEGER PRIMARY KEY CHECK (id = 1),
            smtp_server          TEXT,
            smtp_port            INTEGER DEFAULT 587,
            remetente            TEXT,
            senha                TEXT,
            usar_tls             INTEGER DEFAULT 1
        );
    """)

    conn.commit()
    conn.close()
