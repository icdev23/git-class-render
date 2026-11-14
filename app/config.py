"""Configuração lida do ambiente ao arrancar (nunca entra no código nem no build)."""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VALID_ENVS = ("dev", "qa", "prd")


def read_version() -> str:
    """Versão da app: fonte única no pyproject.toml."""
    with open(PROJECT_ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)["project"]["version"]


@dataclass(frozen=True)
class Settings:
    app_env: str
    db_path: Path
    version: str
    commit: str | None  # commit do deploy, se a plataforma o fornecer

    @property
    def is_prd(self) -> bool:
        return self.app_env == "prd"


def load_settings() -> Settings:
    app_env = os.environ.get("APP_ENV", "dev").strip().lower()
    if app_env not in VALID_ENVS:
        # Falhar logo no arranque é melhor do que correr com a config errada.
        raise ValueError(f"APP_ENV inválido: {app_env!r} (esperado: {', '.join(VALID_ENVS)})")

    db_path = Path(os.environ.get("DB_PATH", PROJECT_ROOT / "data" / "books.db"))
    commit = os.environ.get("RENDER_GIT_COMMIT")  # a confirmar nos docs do Render
    return Settings(
        app_env=app_env,
        db_path=db_path,
        version=read_version(),
        commit=commit[:7] if commit else None,
    )
