from pathlib import Path
import sqlite3


CAMINHO_DADOS = Path(__file__).resolve().parents[2] / "data"
CAMINHO_BANCO = CAMINHO_DADOS / "plataforma.db"


def obter_conexao() -> sqlite3.Connection:
    CAMINHO_DADOS.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    return conexao