"""Operações sobre livros (SQL direto) e validação dos dados do formulário."""

import sqlite3
from datetime import date

STATUS_LABELS = {"por-ler": "Por ler", "lido": "Lido"}


def list_books(conn: sqlite3.Connection, status: str | None = None) -> list[sqlite3.Row]:
    if status in STATUS_LABELS:
        return conn.execute(
            "SELECT * FROM books WHERE status = ? ORDER BY id", (status,)
        ).fetchall()
    return conn.execute("SELECT * FROM books ORDER BY id").fetchall()


def get_book(conn: sqlite3.Connection, book_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()


def create_book(conn: sqlite3.Connection, data: dict) -> int:
    cur = conn.execute(
        "INSERT INTO books (title, author, status, rating, read_on) VALUES (?, ?, ?, ?, ?)",
        (data["title"], data["author"], data["status"], data["rating"], data["read_on"]),
    )
    conn.commit()
    return cur.lastrowid


def update_book(conn: sqlite3.Connection, book_id: int, data: dict) -> None:
    conn.execute(
        "UPDATE books SET title = ?, author = ?, status = ?, rating = ?, read_on = ? WHERE id = ?",
        (data["title"], data["author"], data["status"], data["rating"], data["read_on"], book_id),
    )
    conn.commit()


def delete_book(conn: sqlite3.Connection, book_id: int) -> None:
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()


def validate(title: str, author: str, status: str, rating: str,
             read_on: str = "") -> tuple[dict, list[str]]:
    """Normaliza os campos do formulário. Devolve (dados, erros)."""
    errors: list[str] = []
    data = {
        "title": title.strip(),
        "author": author.strip(),
        "status": status,
        "rating": None,
        "read_on": None,
    }
    if not data["title"]:
        errors.append("O título é obrigatório.")
    if not data["author"]:
        errors.append("O autor é obrigatório.")
    if status not in STATUS_LABELS:
        errors.append("Estado inválido.")
    if rating:
        if rating.isdigit() and 1 <= int(rating) <= 5:
            data["rating"] = int(rating)
        else:
            errors.append("A nota tem de ser de 1 a 5.")
    if read_on:
        try:
            day = date.fromisoformat(read_on)
        except ValueError:
            errors.append("Data de leitura inválida.")
        else:
            if status != "lido":
                errors.append("Só um livro lido pode ter data de leitura.")
            elif day > date.today():
                errors.append("A data de leitura não pode ser no futuro.")
            else:
                data["read_on"] = day.isoformat()
    return data, errors


def format_date(value: str | None) -> str:
    """AAAA-MM-DD → DD/MM/AAAA (vazio → —)."""
    return date.fromisoformat(value).strftime("%d/%m/%Y") if value else "—"
