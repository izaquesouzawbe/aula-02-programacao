# api.py
from flask import Flask, request, jsonify
from contextlib import closing
import sqlite3
import os

from flask_cors import CORS

# Use barra invertida (escape com \\)
DB_PATH = os.environ.get("DB_PATH", "C:\\Dev\\Izaque\\aulas\\aula-02-programacao\\teste.db")

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}},
     allow_headers=["Content-Type"],
     methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_db()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT
            )
            """
        )
        conn.commit()

# Flask 3.x: inicializa já na subida (não existe before_first_request)
init_db()

def row_to_dict(row: sqlite3.Row):
    return {k: row[k] for k in row.keys()}

def validate_payload(data, required=None):
    if data is None:
        return False, "JSON inválido ou ausente"
    required = required or []
    missing = [k for k in required if k not in data]
    if missing:
        return False, f"Campos obrigatórios ausentes: {', '.join(missing)}"
    return True, None

@app.get("/")
def root():
    return jsonify({"status": "ok", "message": "API de usuários rodando", "db": DB_PATH})

@app.get("/usuarios")
def listar_usuarios():
    q = request.args.get("q")
    with closing(get_db()) as conn:
        cur = conn.cursor()
        if q:
            cur.execute(
                "SELECT id, nome, telefone FROM usuario WHERE nome LIKE ? OR telefone LIKE ? ORDER BY id DESC",
                (f"%{q}%", f"%{q}%"),
            )
        else:
            cur.execute("SELECT id, nome, telefone FROM usuario ORDER BY id DESC")
        rows = cur.fetchall()
        return jsonify([row_to_dict(r) for r in rows])

@app.get("/usuarios/<int:usuario_id>")
def obter_usuario(usuario_id: int):
    with closing(get_db()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, nome, telefone FROM usuario WHERE id = ?", (usuario_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Usuário não encontrado"}), 404
        return jsonify(row_to_dict(row))

@app.post("/usuarios")
def criar_usuario():
    data = request.get_json(silent=True)
    ok, err = validate_payload(data, required=["nome"])
    if not ok:
        return jsonify({"error": err}), 400

    nome = str(data.get("nome", "")).strip()
    telefone = data.get("telefone")
    if not nome:
        return jsonify({"error": "'nome' não pode ser vazio"}), 400

    with closing(get_db()) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuario (nome, telefone) VALUES (?, ?)",
            (nome, telefone),
        )
        conn.commit()
        new_id = cur.lastrowid
    return jsonify({"id": new_id, "nome": nome, "telefone": telefone}), 201

@app.put("/usuarios/<int:usuario_id>")
@app.patch("/usuarios/<int:usuario_id>")
def atualizar_usuario(usuario_id: int):
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "JSON inválido ou ausente"}), 400

    campos = []
    valores = []
    if "nome" in data:
        nome = str(data.get("nome") or "").strip()
        if not nome:
            return jsonify({"error": "'nome' não pode ser vazio"}), 400
        campos.append("nome = ?")
        valores.append(nome)
    if "telefone" in data:
        campos.append("telefone = ?")
        valores.append(data.get("telefone"))

    if not campos:
        return jsonify({"error": "Nada para atualizar"}), 400

    with closing(get_db()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM usuario WHERE id = ?", (usuario_id,))
        if not cur.fetchone():
            return jsonify({"error": "Usuário não encontrado"}), 404

        sql = f"UPDATE usuario SET {', '.join(campos)} WHERE id = ?"
        valores.append(usuario_id)
        cur.execute(sql, tuple(valores))
        conn.commit()

        cur.execute("SELECT id, nome, telefone FROM usuario WHERE id = ?", (usuario_id,))
        row = cur.fetchone()
        return jsonify(row_to_dict(row))

@app.delete("/usuarios/<int:usuario_id>")
def deletar_usuario(usuario_id: int):
    with closing(get_db()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM usuario WHERE id = ?", (usuario_id,))
        if not cur.fetchone():
            return jsonify({"error": "Usuário não encontrado"}), 404
        cur.execute("DELETE FROM usuario WHERE id = ?", (usuario_id,))
        conn.commit()
    return ("", 204)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
