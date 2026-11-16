"""App FastAPI: páginas HTML do catálogo e /health."""

from collections.abc import Iterator
from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import books, db
from app.config import Settings, load_settings

APP_DIR = Path(__file__).resolve().parent


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        db.init_db(settings.db_path, settings.app_env)
        yield

    app = FastAPI(title="git-class-render", version=settings.version, lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
    templates = Jinja2Templates(directory=APP_DIR / "templates")
    templates.env.globals.update(settings=settings, status_labels=books.STATUS_LABELS)
    templates.env.filters["pt_date"] = books.format_date

    def get_conn() -> Iterator[sqlite3.Connection]:
        conn = db.connect(settings.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def get_or_404(conn: sqlite3.Connection, book_id: int) -> sqlite3.Row:
        book = books.get_book(conn, book_id)
        if book is None:
            raise HTTPException(status_code=404, detail="Livro não encontrado")
        return book

    def redirect_home() -> RedirectResponse:
        # 303: depois de um POST, o browser segue com GET (padrão Post/Redirect/Get)
        return RedirectResponse("/", status_code=303)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "env": settings.app_env, "version": settings.version,
                "commit": settings.commit}

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, status: str | None = None, conn=Depends(get_conn)):
        return templates.TemplateResponse(request, "list.html", {
            "books": books.list_books(conn, status),
            "current_status": status if status in books.STATUS_LABELS else "todos",
        })

    @app.get("/books/new", response_class=HTMLResponse)
    def new_form(request: Request):
        return templates.TemplateResponse(request, "form.html", {"book": None, "errors": []})

    @app.post("/books")
    def create(request: Request, title: str = Form(""), author: str = Form(""),
               status: str = Form("por-ler"), rating: str = Form(""), read_on: str = Form(""),
               conn=Depends(get_conn)):
        data, errors = books.validate(title, author, status, rating, read_on)
        if errors:
            return templates.TemplateResponse(request, "form.html",
                                              {"book": data, "errors": errors}, status_code=422)
        books.create_book(conn, data)
        return redirect_home()

    @app.get("/books/{book_id}/edit", response_class=HTMLResponse)
    def edit_form(request: Request, book_id: int, conn=Depends(get_conn)):
        book = get_or_404(conn, book_id)
        return templates.TemplateResponse(request, "form.html", {"book": book, "errors": []})

    @app.post("/books/{book_id}")
    def update(request: Request, book_id: int, title: str = Form(""), author: str = Form(""),
               status: str = Form("por-ler"), rating: str = Form(""), read_on: str = Form(""),
               conn=Depends(get_conn)):
        get_or_404(conn, book_id)
        data, errors = books.validate(title, author, status, rating, read_on)
        if errors:
            return templates.TemplateResponse(request, "form.html",
                                              {"book": {**data, "id": book_id}, "errors": errors},
                                              status_code=422)
        books.update_book(conn, book_id, data)
        return redirect_home()

    @app.post("/books/{book_id}/delete")
    def delete(book_id: int, conn=Depends(get_conn)):
        get_or_404(conn, book_id)
        books.delete_book(conn, book_id)
        return redirect_home()

    return app


app = create_app()
