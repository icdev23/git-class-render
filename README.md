# git-class-render

Catálogo de livros (CRUD) para praticar **branches de ambiente** com deploy no Render: `develop` → DEV, `qa` → QA, `main` → PRD. Faz parte da aula prática de Git do Path26 (ciclo 2 da etapa 6).

**Stack:** Python 3.13 · `uv` · FastAPI · Jinja2 · `sqlite3` (sem ORM, sem migrações).

## Correr em local (PowerShell)

```powershell
uv sync                                        # cria a .venv e instala as dependências do uv.lock
uv run uvicorn app.main:app --reload           # http://127.0.0.1:8000
uv run pytest                                  # testes
```

Para ver outro ambiente em local:

```powershell
$env:APP_ENV = "qa"; uv run uvicorn app.main:app --reload
Remove-Item Env:APP_ENV                        # volta a dev
```

## Configuração (variáveis de ambiente)

| Variável | Valores | Padrão | Efeito |
| --- | --- | --- | --- |
| `APP_ENV` | `dev`, `qa`, `prd` | `dev` | Faixa do ambiente (DEV verde, QA laranja, nenhuma em PRD) e dados de exemplo. Um valor inválido impede o arranque. |
| `DB_PATH` | caminho de ficheiro | `data/books.db` | Onde fica a base de dados SQLite. |

A configuração é lida ao arrancar e nunca entra no código: o mesmo código corre nos três ambientes.

## Rotas

| Rota | Faz |
| --- | --- |
| `GET /` (`?status=por-ler` ou `lido`) | Lista, com filtro |
| `GET /books/new` · `POST /books` | Criar |
| `GET /books/{id}/edit` · `POST /books/{id}` | Editar |
| `POST /books/{id}/delete` | Apagar |
| `GET /health` | Estado, ambiente, versão e commit em JSON |

## Deploy no Render

| | |
| --- | --- |
| Build Command | `uv sync --frozen --no-dev` |
| Start Command | `uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Variável | `APP_ENV` = `dev` / `qa` / `prd` conforme o serviço |

Um serviço por ambiente, cada um ligado à sua branch, com auto-deploy a cada push.

## O que observar

- **Base de dados por ambiente:** cada serviço tem a sua `books.db`, com dados de exemplo diferentes.
- **Disco efémero:** no plano gratuito do Render, a BD volta aos dados de exemplo a cada deploy, reinício ou adormecimento.
- **Versão:** a fonte única é o `version` do `pyproject.toml`; aparece no rodapé e em `/health`. Ao mudar a versão, o `uv` atualiza também o `uv.lock` (commitar os dois).
- **Esquema sem migrações:** se o esquema da tabela mudar, a BD local tem de ser apagada (`data/books.db`) para ser recriada.
