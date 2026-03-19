import os
import sqlite3
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_values

SQLITE_PATH = os.getenv("SQLITE_PATH", os.path.join("database", "lions_cred.db"))
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise RuntimeError("Defina DATABASE_URL antes de rodar a migração.")

if not os.path.isfile(SQLITE_PATH):
    raise FileNotFoundError(f"SQLite não encontrado em: {SQLITE_PATH}")


def fetch_all_sqlite(conn, query):
    cur = conn.cursor()
    cur.execute(query)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    cur.close()
    return rows


def to_dt(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace(" ", "T")
    try:
        return datetime.fromisoformat(text)
    except Exception:
        return None


print("[1/5] Lendo SQLite...")
sconn = sqlite3.connect(SQLITE_PATH)

clientes = fetch_all_sqlite(
    sconn,
    """
    SELECT id, nome, cpf, telefone, email, endereco, cidade, uf, status, observacao, criado_em, atualizado_em
    FROM clientes
    ORDER BY id
    """,
)

historico = fetch_all_sqlite(
    sconn,
    """
    SELECT id, nome, cpf, telefone, email, endereco, cidade, uf, status, observacao, criado_em_original, excluido_em, excluido_por
    FROM historico
    ORDER BY id
    """,
)

usuarios = fetch_all_sqlite(
    sconn,
    """
    SELECT id, nome, perfil, senha_hash, criado_em
    FROM usuarios
    ORDER BY id
    """,
)

sconn.close()

print(f"    Clientes: {len(clientes)}")
print(f"    Histórico: {len(historico)}")
print(f"    Usuários: {len(usuarios)}")

print("[2/5] Conectando no Neon...")
pconn = psycopg2.connect(DATABASE_URL, sslmode=os.getenv("PG_SSLMODE", "require"))
pconn.autocommit = False
cur = pconn.cursor()

print("[3/5] Limpando dados atuais do Neon (mantendo estrutura)...")
cur.execute("TRUNCATE TABLE historico, clientes, usuarios RESTART IDENTITY CASCADE")

print("[4/5] Inserindo dados...")
if clientes:
    payload = [
        (
            c["id"], c.get("nome"), c.get("cpf"), c.get("telefone"), c.get("email"),
            c.get("endereco"), c.get("cidade"), c.get("uf"), c.get("status"), c.get("observacao"),
            to_dt(c.get("criado_em")), to_dt(c.get("atualizado_em"))
        )
        for c in clientes
    ]
    execute_values(
        cur,
        """
        INSERT INTO clientes (
            id, nome, cpf, telefone, email, endereco, cidade, uf, status, observacao, criado_em, atualizado_em
        ) VALUES %s
        """,
        payload,
    )

if historico:
    payload = [
        (
            h["id"], h.get("nome"), h.get("cpf"), h.get("telefone"), h.get("email"),
            h.get("endereco"), h.get("cidade"), h.get("uf"), h.get("status"), h.get("observacao"),
            to_dt(h.get("criado_em_original")), to_dt(h.get("excluido_em")), h.get("excluido_por")
        )
        for h in historico
    ]
    execute_values(
        cur,
        """
        INSERT INTO historico (
            id, nome, cpf, telefone, email, endereco, cidade, uf, status, observacao, criado_em_original, excluido_em, excluido_por
        ) VALUES %s
        """,
        payload,
    )

if usuarios:
    payload = [
        (
            u["id"], u.get("nome"), u.get("perfil"), u.get("senha_hash"), to_dt(u.get("criado_em"))
        )
        for u in usuarios
    ]
    execute_values(
        cur,
        """
        INSERT INTO usuarios (
            id, nome, perfil, senha_hash, criado_em
        ) VALUES %s
        """,
        payload,
    )

print("[5/5] Ajustando sequências e finalizando...")
cur.execute("SELECT setval('clientes_id_seq', COALESCE((SELECT MAX(id) FROM clientes), 1), true)")
cur.execute("SELECT setval('historico_id_seq', COALESCE((SELECT MAX(id) FROM historico), 1), true)")
cur.execute("SELECT setval('usuarios_id_seq', COALESCE((SELECT MAX(id) FROM usuarios), 1), true)")

pconn.commit()
cur.close()
pconn.close()

print("Migração concluída com sucesso.")
