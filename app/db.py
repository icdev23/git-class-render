"""SQLite sem ORM: ligação, esquema e dados de exemplo por ambiente."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    title   TEXT NOT NULL,
    author  TEXT NOT NULL,
    status  TEXT NOT NULL CHECK (status IN ('por-ler', 'lido')),
    rating  INTEGER CHECK (rating BETWEEN 1 AND 5),
    read_on TEXT  -- data de leitura (AAAA-MM-DD), só para livros lidos
)
"""

# (title, author, status, rating, read_on) — dados diferentes em cada ambiente
SEEDS: dict[str, list[tuple[str, str, str, int | None, str | None]]] = {
    "dev": [
        ("[DEV] Livro de teste 1", "Autor Fictício", "lido", 3, "2026-01-15"),
        ("[DEV] Livro de teste 2", "Autora Fictícia", "por-ler", None, None),
        ("[DEV] Livro de teste 3", "Outro Autor", "lido", 5, None),
    ],
    "qa": [
        ("Um título propositadamente muito longo para ver como a tabela se comporta quando o texto não cabe numa linha",
         "Autor com Acentuação Çãõ", "lido", 1, "2025-12-31"),
        ("Livro sem nota", "QA Tester", "por-ler", None, None),
        ("Livro com nota máxima", "QA Tester", "lido", 5, None),
    ],
    "prd": [
        ("The Pragmatic Programmer", "David Thomas, Andrew Hunt", "lido", 5, "2025-03-10"),
        ("Clean Code", "Robert C. Martin", "lido", 4, "2025-07-22"),
        ("Designing Data-Intensive Applications", "Martin Kleppmann", "por-ler", None, None),
    ],
}


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path, app_env: str) -> None:
    """Cria a tabela se não existir e, se estiver vazia, insere os dados do ambiente."""
    with connect(db_path) as conn:
        conn.execute(SCHEMA)
        empty = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0
        if empty:
            conn.executemany(
                "INSERT INTO books (title, author, status, rating, read_on) VALUES (?, ?, ?, ?, ?)",
                SEEDS[app_env],
            )
    conn.close()
