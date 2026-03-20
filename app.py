# ============================================================
#  Lions Cred | Backend Flask (Postgres/Neon)
#  Requer variável de ambiente DATABASE_URL (postgres://user:pass@host:port/db)
# ============================================================

from flask import Flask, jsonify, request, render_template, send_from_directory, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os, re
from datetime import datetime, date
import psycopg2
import psycopg2.extras
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
CORS(app)

# -------------------------------------------------------
# Conexão Postgres
# -------------------------------------------------------

def get_connection():
    if not Config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL não configurado. Defina a variável de ambiente DATABASE_URL.")
    conn = psycopg2.connect(Config.DATABASE_URL, sslmode=os.getenv("PG_SSLMODE", "require"))
    return conn

def rows_to_json(rows):
    def serializar(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return obj
    return [{k: serializar(v) for k, v in r.items()} for r in rows]

# -------------------------------------------------------
# Validações
# -------------------------------------------------------

def validar_cpf(cpf: str) -> bool:
    nums = re.sub(r"\D", "", cpf)
    if len(nums) != 11 or len(set(nums)) == 1:
        return False
    for i in range(9, 11):
        soma = sum(int(nums[j]) * (i + 1 - j) for j in range(i))
        d = (soma * 10 % 11) % 10
        if d != int(nums[i]):
            return False
    return True

def formatar_cpf(cpf: str) -> str:
    nums = re.sub(r"\D", "", cpf)
    return f"{nums[:3]}.{nums[3:6]}.{nums[6:9]}-{nums[9:]}"

# -------------------------------------------------------
# Rotas básicas
# -------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/logo")
def serve_logo():
    static_dir = os.path.join(app.root_path, "static")
    for ext in ("png", "jpg", "jpeg", "ico", "webp", "svg"):
        fname = f"logo.{ext}"
        if os.path.isfile(os.path.join(static_dir, fname)):
            return send_from_directory(static_dir, fname)
    return "", 404

# -------------------------------------------------------
# API – Estatísticas
# -------------------------------------------------------

@app.route("/api/stats", methods=["GET"])
def get_stats():
    try:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT COUNT(*) AS total FROM clientes")
            total = cur.fetchone()["total"]
            cur.execute("SELECT COUNT(*) AS ativos FROM clientes WHERE status='ativo'")
            ativos = cur.fetchone()["ativos"]
            cur.execute("SELECT COUNT(*) AS hoje FROM clientes WHERE DATE(criado_em)=CURRENT_DATE")
            hoje = cur.fetchone()["hoje"]
            cur.execute("SELECT COUNT(*) AS semana FROM clientes WHERE criado_em >= CURRENT_DATE - INTERVAL '7 days'")
            semana = cur.fetchone()["semana"]
        return jsonify({"total": total, "ativos": ativos, "hoje": hoje, "semana": semana})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------
# API – Clientes
# -------------------------------------------------------

@app.route("/api/clientes", methods=["GET"])
def listar_clientes():
    try:
        pagina   = int(request.args.get("pagina", 1))
        por_pag  = int(request.args.get("por_pagina", 10))
        status   = request.args.get("status", "todos")
        offset   = (pagina - 1) * por_pag
        filtro   = "" if status == "todos" else "WHERE status=%s"
        params_total = () if status == "todos" else (status,)
        params_list  = params_total + (por_pag, offset)
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(f"SELECT COUNT(*) AS total FROM clientes {filtro}", params_total)
            total = cur.fetchone()["total"]
            cur.execute(
                f"SELECT * FROM clientes {filtro} ORDER BY criado_em DESC LIMIT %s OFFSET %s",
                params_list
            )
            rows = cur.fetchall()
        return jsonify({
            "clientes": rows_to_json(rows),
            "total": total,
            "pagina": pagina,
            "paginas": -(-total // por_pag)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/clientes", methods=["POST"])
def cadastrar_cliente():
    data = request.get_json(force=True) or {}
    nome = data.get("nome", "").strip()
    cpf  = data.get("cpf", "").strip()
    if not nome:
        return jsonify({"error": "O campo nome é obrigatório."}), 400
    if not cpf:
        return jsonify({"error": "O campo CPF é obrigatório."}), 400
    if not validar_cpf(cpf):
        return jsonify({"error": "CPF inválido."}), 400
    cpf_fmt = formatar_cpf(cpf)
    try:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT id FROM clientes WHERE cpf=%s", (cpf_fmt,))
            if cur.fetchone():
                return jsonify({"error": "CPF já cadastrado."}), 409
            cur.execute(
                """INSERT INTO clientes
                   (nome, cpf, telefone, email, endereco, cidade, uf, status, observacao)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING *""",
                (
                    nome,
                    cpf_fmt,
                    data.get("telefone", "").strip() or None,
                    data.get("email",    "").strip() or None,
                    data.get("endereco", "").strip() or None,
                    data.get("cidade",   "").strip() or None,
                    data.get("uf",       "").strip().upper() or None,
                    data.get("status",   "ativo"),
                    data.get("observacao", "").strip() or None,
                )
            )
            cliente = cur.fetchone()
            conn.commit()
        return jsonify({"message": "Cliente cadastrado com sucesso!", "cliente": rows_to_json([cliente])[0]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/clientes/buscar", methods=["GET"])
def buscar_clientes():
    termo = request.args.get("q", "").strip()
    if not termo:
        return jsonify({"clientes": [], "total": 0})

    cpf_digits = re.sub(r"\D", "", termo)
    cpf_fmt = f"{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:]}" if len(cpf_digits) == 11 else ""

    try:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            where_parts = ["nome ILIKE %s", "cpf ILIKE %s"]
            params = [f"%{termo}%", f"%{termo}%"]

            # Só adiciona busca por CPF em dígitos quando houver dígitos no termo;
            # evita '%'+''+'%' => '%%' que retornava praticamente tudo.
            if cpf_digits:
                where_parts.append("regexp_replace(cpf, '\\D', '', 'g') ILIKE %s")
                params.append(f"%{cpf_digits}%")

            if cpf_fmt:
                where_parts.append("cpf ILIKE %s")
                params.append(f"%{cpf_fmt}%")

            sql = f"""
                SELECT *
                FROM clientes
                WHERE {' OR '.join(where_parts)}
                ORDER BY nome
                LIMIT 50
            """

            cur.execute(sql, params)
            rows = cur.fetchall()

        return jsonify({"clientes": rows_to_json(rows), "total": len(rows)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/clientes/<int:cliente_id>", methods=["GET"])
def detalhe_cliente(cliente_id):
    try:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM clientes WHERE id=%s", (cliente_id,))
            row = cur.fetchone()
        if not row:
            return jsonify({"error": "Cliente não encontrado."}), 404
        return jsonify(rows_to_json([row])[0])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/clientes/<int:cliente_id>", methods=["PUT"])
def atualizar_cliente(cliente_id):
    data = request.get_json(force=True) or {}
    nome = data.get("nome", "").strip()
    cpf  = data.get("cpf",  "").strip()
    if cpf and not validar_cpf(cpf):
        return jsonify({"error": "CPF inválido."}), 400
    cpf_fmt = formatar_cpf(cpf) if cpf else None
    try:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT id FROM clientes WHERE id=%s", (cliente_id,))
            if not cur.fetchone():
                return jsonify({"error": "Cliente não encontrado."}), 404
            if cpf_fmt:
                cur.execute("SELECT id FROM clientes WHERE cpf=%s AND id!=%s", (cpf_fmt, cliente_id))
                if cur.fetchone():
                    return jsonify({"error": "CPF já cadastrado para outro cliente."}), 409
            campos = []
            valores = []
            mapeamento = {
                "nome": nome or None,
                "cpf": cpf_fmt,
                "telefone": data.get("telefone", "").strip() or None,
                "email":    data.get("email",    "").strip() or None,
                "endereco": data.get("endereco", "").strip() or None,
                "cidade":   data.get("cidade",   "").strip() or None,
                "uf":       data.get("uf",       "").strip().upper() or None,
                "status":   data.get("status")   or None,
                "observacao": data.get("observacao", "").strip() or None,
            }
            for campo, valor in mapeamento.items():
                if valor is not None:
                    campos.append(f"{campo}=%s")
                    valores.append(valor)
            if campos:
                valores.append(cliente_id)
                cur.execute(f"UPDATE clientes SET {', '.join(campos)}, atualizado_em=NOW() WHERE id=%s", valores)
                conn.commit()
            cur.execute("SELECT * FROM clientes WHERE id=%s", (cliente_id,))
            cliente = cur.fetchone()
        return jsonify({"message": "Cliente atualizado!", "cliente": rows_to_json([cliente])[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/clientes/<int:cliente_id>", methods=["DELETE"])
def excluir_cliente(cliente_id):
    try:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM clientes WHERE id=%s", (cliente_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "Cliente não encontrado."}), 404
            cur.execute(
                """INSERT INTO historico
                   (nome,cpf,telefone,email,endereco,cidade,uf,status,observacao,criado_em_original,excluido_por)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    row['nome'], row['cpf'], row['telefone'], row['email'],
                    row['endereco'], row['cidade'], row['uf'], row['status'],
                    row['observacao'], row['criado_em'], session.get('usuario_nome', 'Sistema')
                )
            )
            cur.execute("DELETE FROM clientes WHERE id=%s", (cliente_id,))
            conn.commit()
        return jsonify({"message": "Cliente excluído com sucesso."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------
# API – Histórico
# -------------------------------------------------------

@app.route("/api/historico", methods=["GET"])
def listar_historico():
    try:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM historico ORDER BY excluido_em DESC")
            rows = cur.fetchall()
        return jsonify({"historico": rows_to_json(rows), "total": len(rows)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/historico/<int:hid>/recuperar", methods=["POST"])
def recuperar_cliente(hid):
    try:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM historico WHERE id=%s", (hid,))
            h = cur.fetchone()
            if not h:
                return jsonify({"error": "Registro não encontrado."}), 404
            cur.execute(
                """INSERT INTO clientes (nome, cpf, telefone, email, endereco, cidade, uf, status, observacao, criado_em)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s, COALESCE(%s, NOW()))""",
                (
                    h['nome'], h['cpf'], h['telefone'], h['email'],
                    h['endereco'], h['cidade'], h['uf'], h['status'],
                    h['observacao'], h['criado_em_original']
                )
            )
            cur.execute("DELETE FROM historico WHERE id=%s", (hid,))
            conn.commit()
        return jsonify({"message": "Cliente recuperado com sucesso."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------
# API – Autenticação
# -------------------------------------------------------

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data  = request.get_json(force=True) or {}
    nome  = data.get("nome",  "").strip()
    senha = data.get("senha", "").strip()
    if not nome or not senha:
        return jsonify({"error": "Informe usuário e senha."}), 400
    try:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM usuarios WHERE nome=%s", (nome,))
            user = cur.fetchone()
        if not user or not check_password_hash(user["senha_hash"], senha):
            return jsonify({"error": "Usuário ou senha incorretos."}), 401
        session["usuario_id"]    = user["id"]
        session["usuario_nome"]  = user["nome"]
        session["usuario_perfil"] = user["perfil"]
        return jsonify({"message": "Login realizado!", "usuario": {
            "id": user["id"], "nome": user["nome"], "perfil": user["perfil"]
        }})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    session.clear()
    return jsonify({"message": "Logout realizado."})

@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    if "usuario_id" not in session:
        return jsonify({"logado": False, "usuario": None})
    return jsonify({"logado": True, "usuario": {
        "id": session["usuario_id"],
        "nome": session["usuario_nome"],
        "perfil": session["usuario_perfil"]
    }})

# -------------------------------------------------------
# API – Usuários
# -------------------------------------------------------

@app.route("/api/usuarios", methods=["GET"])
def listar_usuarios():
    q = request.args.get("q", "").strip()
    try:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            if q:
                cur.execute("SELECT id,nome,perfil,criado_em FROM usuarios WHERE nome ILIKE %s ORDER BY nome", (f"%{q}%",))
            else:
                cur.execute("SELECT id,nome,perfil,criado_em FROM usuarios ORDER BY nome")
            rows = cur.fetchall()
        return jsonify({"usuarios": rows_to_json(rows)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/usuarios", methods=["POST"])
def criar_usuario():
    data  = request.get_json(force=True) or {}
    nome  = data.get("nome",  "").strip()
    senha = data.get("senha", "").strip()
    perfil = data.get("perfil", "Visualização")
    if not nome or not senha:
        return jsonify({"error": "Nome e senha são obrigatórios."}), 400
    if perfil not in ('Desenvolvedor','Administração','Visualização'):
        return jsonify({"error": "Perfil inválido."}), 400
    # Administração não pode criar usuário Desenvolvedor
    caller_perfil = session.get('usuario_perfil')
    if caller_perfil == 'Administração' and perfil == 'Desenvolvedor':
        return jsonify({"error": "Sem permissão para criar usuário Desenvolvedor."}), 403
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM usuarios WHERE nome=%s", (nome,))
            if cur.fetchone():
                return jsonify({"error": "Já existe um usuário com este nome."}), 409
            cur.execute(
                "INSERT INTO usuarios (nome, perfil, senha_hash) VALUES (%s,%s,%s)",
                (nome, perfil, generate_password_hash(senha))
            )
            conn.commit()
        return jsonify({"message": "Usuário criado!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/usuarios/<int:uid>", methods=["PUT"])
def atualizar_usuario(uid):
    data   = request.get_json(force=True) or {}
    nome   = data.get("nome",  "").strip()
    senha  = data.get("senha", "").strip()
    perfil = data.get("perfil", "").strip()
    caller_perfil = session.get('usuario_perfil')
    try:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT id, perfil FROM usuarios WHERE id=%s", (uid,))
            target = cur.fetchone()
            if not target:
                return jsonify({"error": "Usuário não encontrado."}), 404
            # Administração não pode editar Desenvolvedor nem atribuir perfil Desenvolvedor
            if caller_perfil == 'Administração':
                if (target['perfil'] if isinstance(target, dict) else target[1]) == 'Desenvolvedor':
                    return jsonify({"error": "Sem permissão para editar usuário Desenvolvedor."}), 403
                if perfil == 'Desenvolvedor':
                    return jsonify({"error": "Sem permissão para atribuir perfil Desenvolvedor."}), 403
            if nome:
                cur.execute("SELECT id FROM usuarios WHERE nome=%s AND id!=%s", (nome, uid))
                if cur.fetchone():
                    return jsonify({"error": "Nome já em uso."}), 409
            sets = []
            vals = []
            if nome:   sets.append("nome=%s");        vals.append(nome)
            if perfil: sets.append("perfil=%s");      vals.append(perfil)
            if senha:  sets.append("senha_hash=%s");  vals.append(generate_password_hash(senha))
            if sets:
                vals.append(uid)
                cur.execute(f"UPDATE usuarios SET {', '.join(sets)} WHERE id=%s", vals)
                conn.commit()
                if session.get('usuario_id') == uid:
                    if nome:   session['usuario_nome']   = nome
                    if perfil: session['usuario_perfil'] = perfil
        return jsonify({"message": "Usuário atualizado!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/usuarios/<int:uid>", methods=["DELETE"])
def remover_usuario(uid):
    if uid == session.get('usuario_id'):
        return jsonify({"error": "Você não pode remover o próprio usuário."}), 400
    caller_perfil = session.get('usuario_perfil')
    try:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT id, perfil FROM usuarios WHERE id=%s", (uid,))
            target = cur.fetchone()
            if not target:
                return jsonify({"error": "Usuário não encontrado."}), 404
            # Administração não pode remover Desenvolvedor
            if caller_perfil == 'Administração':
                if (target['perfil'] if isinstance(target, dict) else target[1]) == 'Desenvolvedor':
                    return jsonify({"error": "Sem permissão para remover usuário Desenvolvedor."}), 403
            cur.execute("DELETE FROM usuarios WHERE id=%s", (uid,))
            conn.commit()
        return jsonify({"message": "Usuário removido."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------
# Inicialização local
# -------------------------------------------------------

def init_db():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                cpf  TEXT NOT NULL UNIQUE,
                telefone TEXT,
                email    TEXT,
                endereco TEXT,
                cidade   TEXT,
                uf       TEXT,
                status   TEXT NOT NULL DEFAULT 'ativo' CHECK (status IN ('ativo','inativo')),
                observacao TEXT,
                criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes(nome)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_clientes_cpf  ON clientes(cpf)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_clientes_status ON clientes(status)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS historico (
                id SERIAL PRIMARY KEY,
                nome TEXT,
                cpf  TEXT,
                telefone TEXT,
                email    TEXT,
                endereco TEXT,
                cidade   TEXT,
                uf       TEXT,
                status   TEXT,
                observacao TEXT,
                criado_em_original TIMESTAMPTZ,
                excluido_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                excluido_por TEXT DEFAULT 'Sistema'
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE,
                perfil TEXT NOT NULL DEFAULT 'Visualização' CHECK (perfil IN ('Desenvolvedor','Administração','Visualização')),
                senha_hash TEXT NOT NULL,
                criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        cur.execute("SELECT id FROM usuarios WHERE nome='Admin'")
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO usuarios (nome, perfil, senha_hash) VALUES (%s,%s,%s)",
                ('Admin', 'Desenvolvedor', generate_password_hash('Admin'))
            )
        conn.commit()

# Em ambiente serverless (Vercel), __main__ não é executado.
# Inicializa schema ao importar o app para garantir tabelas existentes.
try:
    init_db()
except Exception as e:
    # Mantém logs sem derrubar import; rotas retornarão erro detalhado se conexão falhar.
    print(f"[init_db] aviso: {e}")

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
