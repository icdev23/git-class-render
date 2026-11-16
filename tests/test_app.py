"""Testes do CRUD e da configuração. Cada teste usa uma BD temporária."""

import pytest
from fastapi.testclient import TestClient

from app.config import load_settings
from app.db import SEEDS
from app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    with TestClient(create_app(load_settings())) as c:  # "with" corre o arranque (seed)
        yield c


def test_invalid_app_env_fails_at_startup(monkeypatch):
    monkeypatch.setenv("APP_ENV", "producao")
    with pytest.raises(ValueError):
        load_settings()


def test_app_env_defaults_to_dev(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    assert load_settings().app_env == "dev"


@pytest.mark.parametrize("env", ["dev", "qa", "prd"])
def test_seed_and_banner_per_env(tmp_path, monkeypatch, env):
    monkeypatch.setenv("APP_ENV", env)
    monkeypatch.setenv("DB_PATH", str(tmp_path / f"{env}.db"))
    with TestClient(create_app(load_settings())) as c:
        html = c.get("/").text
        assert SEEDS[env][0][0] in html
        assert ("não é produção" in html) == (env != "prd")
        assert c.get("/health").json()["env"] == env


def test_create_book(client):
    r = client.post("/books", data={"title": "Novo", "author": "Alguém",
                                    "status": "lido", "rating": "4"})
    assert r.status_code == 200  # o TestClient segue o redirect 303
    assert "Novo" in r.text and "★★★★" in r.text


def test_create_requires_title(client):
    r = client.post("/books", data={"title": " ", "author": "Alguém", "status": "lido"})
    assert r.status_code == 422
    assert "O título é obrigatório." in r.text


def test_rating_out_of_range_is_rejected(client):
    r = client.post("/books", data={"title": "X", "author": "Y", "status": "lido", "rating": "9"})
    assert r.status_code == 422


def test_update_book(client):
    r = client.post("/books/1", data={"title": "Título editado", "author": "Autor",
                                      "status": "por-ler", "rating": ""})
    assert "Título editado" in r.text


def test_delete_book(client):
    title = SEEDS["dev"][0][0]
    r = client.post("/books/1/delete")
    assert title not in r.text


def test_filter_by_status(client):
    html = client.get("/?status=por-ler").text
    assert "[DEV] Livro de teste 2" in html
    assert "[DEV] Livro de teste 1" not in html


def test_missing_book_returns_404(client):
    assert client.get("/books/999/edit").status_code == 404


def test_create_with_read_date(client):
    r = client.post("/books", data={"title": "Com data", "author": "A", "status": "lido",
                                    "rating": "", "read_on": "2026-02-03"})
    assert r.status_code == 200
    assert "03/02/2026" in r.text


def test_read_date_requires_status_read(client):
    r = client.post("/books", data={"title": "X", "author": "Y", "status": "por-ler",
                                    "read_on": "2026-02-03"})
    assert r.status_code == 422
    assert "Só um livro lido pode ter data de leitura." in r.text


def test_read_date_cannot_be_in_future(client):
    r = client.post("/books", data={"title": "X", "author": "Y", "status": "lido",
                                    "read_on": "2999-01-01"})
    assert r.status_code == 422


def test_edit_form_keeps_read_date(client):
    assert 'value="2026-01-15"' in client.get("/books/1/edit").text
