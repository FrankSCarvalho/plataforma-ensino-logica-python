"""Fixtures compartilhadas pelos testes."""

import pytest

from app.core import config
from app.database.initialize import initialize_database


@pytest.fixture()
def banco_de_teste(tmp_path, monkeypatch):
    """Redireciona o banco para um diretório temporário e o inicializa.

    Cada teste recebe um banco limpo e isolado, sem tocar no banco de
    desenvolvimento localizado em ``data/``.
    """
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "data" / "testes.db")
    initialize_database()
    return config.DATABASE_PATH