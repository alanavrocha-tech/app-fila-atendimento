from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "fila.db"


def conectar():
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_banco():
    conexao = conectar()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            prioridade TEXT NOT NULL DEFAULT 'Normal',
            status TEXT NOT NULL DEFAULT 'Aguardando',
            data_chegada TEXT NOT NULL,
            data_atendimento TEXT,
            data_conclusao TEXT
        )
    """)

    conexao.commit()
    conexao.close()


@app.route("/")
def index():
    conexao = conectar()

    aguardando = conexao.execute("""
        SELECT * FROM clientes
        WHERE status = 'Aguardando'
        ORDER BY
            CASE
                WHEN prioridade = 'Preferencial' THEN 0
                ELSE 1
            END,
            id ASC
    """).fetchall()

    em_atendimento = conexao.execute("""
        SELECT * FROM clientes
        WHERE status = 'Em Atendimento'
        ORDER BY id ASC
    """).fetchall()

    conexao.close()

    return render_template(
        "index.html",
        aguardando=aguardando,
        em_atendimento=em_atendimento
    )


@app.route("/adicionar", methods=["POST"])
def adicionar():
    nome = request.form["nome"]
    prioridade = request.form["prioridade"]

    conexao = conectar()

    conexao.execute("""
        INSERT INTO clientes
        (nome, prioridade, status, data_chegada)
        VALUES (?, ?, ?, ?)
    """, (
        nome,
        prioridade,
        "Aguardando",
        datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    ))

    conexao.commit()
    conexao.close()

    return redirect(url_for("index"))


@app.route("/chamar_proximo", methods=["POST"])
def chamar_proximo():
    conexao = conectar()

    cliente = conexao.execute("""
        SELECT * FROM clientes
        WHERE status = 'Aguardando'
        ORDER BY
            CASE
                WHEN prioridade = 'Preferencial' THEN 0
                ELSE 1
            END,
            id ASC
        LIMIT 1
    """).fetchone()

    if cliente:
        conexao.execute("""
            UPDATE clientes
            SET status = 'Em Atendimento',
                data_atendimento = ?
            WHERE id = ?
        """, (
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            cliente["id"]
        ))

        conexao.commit()

    conexao.close()

    return redirect(url_for("index"))


@app.route("/concluir/<int:id>", methods=["POST"])
def concluir(id):
    conexao = conectar()

    conexao.execute("""
        UPDATE clientes
        SET status = 'Concluído',
            data_conclusao = ?
        WHERE id = ?
    """, (
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        id
    ))

    conexao.commit()
    conexao.close()

    return redirect(url_for("index"))


@app.route("/cancelar/<int:id>", methods=["POST"])
def cancelar(id):
    conexao = conectar()

    conexao.execute("""
        UPDATE clientes
        SET status = 'Cancelado',
            data_conclusao = ?
        WHERE id = ?
    """, (
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        id
    ))

    conexao.commit()
    conexao.close()

    return redirect(url_for("index"))


@app.route("/historico")
def historico():
    conexao = conectar()

    clientes = conexao.execute("""
        SELECT * FROM clientes
        WHERE status IN ('Concluído', 'Cancelado')
        ORDER BY id DESC
    """).fetchall()

    conexao.close()

    return render_template(
        "historico.html",
        clientes=clientes
    )


if __name__ == "__main__":
    criar_banco()
    app.run(debug=True)