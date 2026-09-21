"""Sistema de eventos acadêmicos: Aluno, Evento, Inscrição e Pagamento em SQLite puro.

Este arquivo é igual nos quatro repositórios da série `protocolos-*`. O que muda entre eles
é só o `servidor.py`, que expõe estas mesmas operações num protocolo diferente.

Relacionamentos:
- Inscricao 1:1 Pagamento      (inscricao_id é UNIQUE em pagamentos)
- Evento    1:N Inscricao      (evento_id em inscricoes)
- Aluno     1:N Inscricao      (aluno_id em inscricoes)
- Aluno     N:M Evento         (através de Inscricao, junção das duas linhas acima)
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

CAMINHO_BANCO = Path(__file__).resolve().parent.parent / "dados.db"


def conectar() -> sqlite3.Connection:
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def inicializar() -> None:
    """Recria o banco do zero e semeia dados de exemplo. Chamado uma vez, ao subir o servidor."""
    if CAMINHO_BANCO.exists():
        os.remove(CAMINHO_BANCO)

    conexao = conectar()
    try:
        conexao.executescript(
            """
            CREATE TABLE aluno (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                nome   TEXT NOT NULL,
                email  TEXT NOT NULL
            );

            CREATE TABLE evento (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                data   TEXT NOT NULL
            );

            CREATE TABLE inscricao (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                aluno_id  INTEGER NOT NULL REFERENCES aluno(id),
                evento_id INTEGER NOT NULL REFERENCES evento(id),
                status    TEXT NOT NULL DEFAULT 'pendente',
                UNIQUE (aluno_id, evento_id)
            );

            CREATE TABLE pagamento (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                inscricao_id  INTEGER NOT NULL UNIQUE REFERENCES inscricao(id),
                valor         REAL NOT NULL,
                status        TEXT NOT NULL
            );
            """
        )

        aluno_maria = conexao.execute(
            "INSERT INTO aluno (nome, email) VALUES (?, ?)", ("Maria", "maria@escola.dev")
        ).lastrowid
        aluno_joao = conexao.execute(
            "INSERT INTO aluno (nome, email) VALUES (?, ?)", ("João", "joao@escola.dev")
        ).lastrowid

        evento_semana = conexao.execute(
            "INSERT INTO evento (titulo, data) VALUES (?, ?)", ("Semana Acadêmica", "2026-09-14")
        ).lastrowid
        evento_hack = conexao.execute(
            "INSERT INTO evento (titulo, data) VALUES (?, ?)", ("Hackathon", "2026-10-02")
        ).lastrowid

        inscricao_maria_semana = conexao.execute(
            "INSERT INTO inscricao (aluno_id, evento_id, status) VALUES (?, ?, 'confirmada')",
            (aluno_maria, evento_semana),
        ).lastrowid
        conexao.execute(
            "INSERT INTO inscricao (aluno_id, evento_id, status) VALUES (?, ?, 'pendente')",
            (aluno_maria, evento_hack),
        )
        conexao.execute(
            "INSERT INTO inscricao (aluno_id, evento_id, status) VALUES (?, ?, 'pendente')",
            (aluno_joao, evento_semana),
        )

        conexao.execute(
            "INSERT INTO pagamento (inscricao_id, valor, status) VALUES (?, ?, 'aprovado')",
            (inscricao_maria_semana, 50.0),
        )

        conexao.commit()
    finally:
        conexao.close()


def linha_para_dict(linha: sqlite3.Row) -> dict[str, Any]:
    return dict(linha)


def buscar_aluno(aluno_id: int) -> dict[str, Any] | None:
    conexao = conectar()
    try:
        linha = conexao.execute("SELECT * FROM aluno WHERE id = ?", (aluno_id,)).fetchone()
        return linha_para_dict(linha) if linha is not None else None
    finally:
        conexao.close()


def buscar_evento(evento_id: int) -> dict[str, Any] | None:
    conexao = conectar()
    try:
        linha = conexao.execute("SELECT * FROM evento WHERE id = ?", (evento_id,)).fetchone()
        return linha_para_dict(linha) if linha is not None else None
    finally:
        conexao.close()


def criar_aluno(nome: str, email: str) -> dict[str, Any]:
    conexao = conectar()
    try:
        id_novo = conexao.execute(
            "INSERT INTO aluno (nome, email) VALUES (?, ?)", (nome, email)
        ).lastrowid
        conexao.commit()
        return {"id": id_novo, "nome": nome, "email": email}
    finally:
        conexao.close()


def criar_evento(titulo: str, data: str) -> dict[str, Any]:
    conexao = conectar()
    try:
        id_novo = conexao.execute(
            "INSERT INTO evento (titulo, data) VALUES (?, ?)", (titulo, data)
        ).lastrowid
        conexao.commit()
        return {"id": id_novo, "titulo": titulo, "data": data}
    finally:
        conexao.close()


def inscrever(aluno_id: int, evento_id: int) -> dict[str, Any]:
    conexao = conectar()
    try:
        aluno = conexao.execute("SELECT id FROM aluno WHERE id = ?", (aluno_id,)).fetchone()
        if aluno is None:
            raise ValueError(f"aluno {aluno_id} não existe")
        evento = conexao.execute("SELECT id FROM evento WHERE id = ?", (evento_id,)).fetchone()
        if evento is None:
            raise ValueError(f"evento {evento_id} não existe")

        existente = conexao.execute(
            "SELECT id FROM inscricao WHERE aluno_id = ? AND evento_id = ?", (aluno_id, evento_id)
        ).fetchone()
        if existente is not None:
            raise ValueError("aluno já inscrito nesse evento")

        id_novo = conexao.execute(
            "INSERT INTO inscricao (aluno_id, evento_id, status) VALUES (?, ?, 'pendente')",
            (aluno_id, evento_id),
        ).lastrowid
        conexao.commit()
        return {"id": id_novo, "aluno_id": aluno_id, "evento_id": evento_id, "status": "pendente"}
    finally:
        conexao.close()


def registrar_pagamento(inscricao_id: int, valor: float) -> dict[str, Any]:
    conexao = conectar()
    try:
        inscricao = conexao.execute(
            "SELECT id FROM inscricao WHERE id = ?", (inscricao_id,)
        ).fetchone()
        if inscricao is None:
            raise ValueError(f"inscrição {inscricao_id} não existe")

        ja_pago = conexao.execute(
            "SELECT id FROM pagamento WHERE inscricao_id = ?", (inscricao_id,)
        ).fetchone()
        if ja_pago is not None:
            raise ValueError("inscrição já tem pagamento registrado")

        status = "aprovado" if valor > 0 else "recusado"
        id_novo = conexao.execute(
            "INSERT INTO pagamento (inscricao_id, valor, status) VALUES (?, ?, ?)",
            (inscricao_id, valor, status),
        ).lastrowid

        if status == "aprovado":
            conexao.execute(
                "UPDATE inscricao SET status = 'confirmada' WHERE id = ?", (inscricao_id,)
            )

        conexao.commit()
        return {"id": id_novo, "inscricao_id": inscricao_id, "valor": valor, "status": status}
    finally:
        conexao.close()


def buscar_inscricao(inscricao_id: int) -> dict[str, Any] | None:
    conexao = conectar()
    try:
        inscricao = conexao.execute(
            "SELECT * FROM inscricao WHERE id = ?", (inscricao_id,)
        ).fetchone()
        if inscricao is None:
            return None

        resultado = linha_para_dict(inscricao)
        pagamento = conexao.execute(
            "SELECT * FROM pagamento WHERE inscricao_id = ?", (inscricao_id,)
        ).fetchone()
        resultado["pagamento"] = linha_para_dict(pagamento) if pagamento is not None else None
        return resultado
    finally:
        conexao.close()


def eventos_do_aluno(aluno_id: int) -> list[dict[str, Any]]:
    conexao = conectar()
    try:
        linhas = conexao.execute(
            """
            SELECT evento.*, inscricao.status AS status_inscricao
            FROM evento
            JOIN inscricao ON inscricao.evento_id = evento.id
            WHERE inscricao.aluno_id = ?
            """,
            (aluno_id,),
        ).fetchall()
        return [linha_para_dict(linha) for linha in linhas]
    finally:
        conexao.close()


def alunos_do_evento(evento_id: int) -> list[dict[str, Any]]:
    conexao = conectar()
    try:
        linhas = conexao.execute(
            """
            SELECT aluno.*, inscricao.status AS status_inscricao
            FROM aluno
            JOIN inscricao ON inscricao.aluno_id = aluno.id
            WHERE inscricao.evento_id = ?
            """,
            (evento_id,),
        ).fetchall()
        return [linha_para_dict(linha) for linha in linhas]
    finally:
        conexao.close()
