"""Testes da infraestrutura do banco de dados SQLite."""

from app.core import config
from app.database.connection import get_connection
from app.database.initialize import SCHEMA_VERSION, initialize_database


def _usar_banco_temporario(tmp_path, monkeypatch):
    """Redireciona o banco para um diretório temporário do teste.

    Evita criar ou alterar arquivos dentro de ``data/`` durante os testes.
    """
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "data" / "testes.db")


def test_inicializacao_cria_diretorio_de_dados(tmp_path, monkeypatch):
    _usar_banco_temporario(tmp_path, monkeypatch)

    initialize_database()

    assert config.DATA_DIR.is_dir()


def test_inicializacao_cria_arquivo_do_banco(tmp_path, monkeypatch):
    _usar_banco_temporario(tmp_path, monkeypatch)

    initialize_database()

    assert config.DATABASE_PATH.is_file()


def test_conexao_executa_consulta_simples(tmp_path, monkeypatch):
    _usar_banco_temporario(tmp_path, monkeypatch)
    initialize_database()

    with get_connection() as connection:
        resultado = connection.execute("SELECT 1").fetchone()

    assert resultado[0] == 1


def test_versao_do_esquema_registrada(tmp_path, monkeypatch):
    _usar_banco_temporario(tmp_path, monkeypatch)
    initialize_database()

    with get_connection() as connection:
        versao = connection.execute("PRAGMA user_version").fetchone()[0]

    assert versao == SCHEMA_VERSION


def test_caminho_padrao_do_banco_aponta_para_data():
    assert config.DATABASE_PATH.parent == config.DATA_DIR
    assert config.DATABASE_PATH.name.endswith(".db")