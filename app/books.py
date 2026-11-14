"""Operações sobre livros (SQL direto) e validação dos dados do formulário."""

import sqlite3

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
        "INSERT INTO books (title, author, status, rating) VALUES (?, ?, ?, ?)",
        (data["title"], data["author"], data["status"], data["rating"]),
    )
    conn.commit()
    return cur.lastrowid


def update_book(conn: sqlite3.Connection, book_id: int, data: dict) -> None:
    conn.execute(
        "UPDATE books SET title = ?, author = ?, status = ?, rating = ? WHERE id = ?",
        (data["title"], data["author"], data["status"], data["rating"], book_id),
    )
    conn.commit()


def delete_book(conn: sqlite3.Connection, book_id: int) -> None:
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()


def validate(title: str, author: str, status: str, rating: str) -> tuple[dict, list[str]]:
    """Normaliza os campos do formulário. Devolve (dados, erros)."""
    errors: list[str] = []
    data = {
        "title": title.strip(),
        "author": author.strip(),
        "status": status,
        "rating": None,
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
    return data, errors
