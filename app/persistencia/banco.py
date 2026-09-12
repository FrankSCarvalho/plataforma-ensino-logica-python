from pathlib import Path  # Manipulação de caminhos multiplataforma (Windows/Linux/macOS)
import sqlite3  # Driver integrado do Python para SQLite (sem dependências externas)


# Path(__file__).resolve().parents[2] sobe 2 níveis desde este arquivo:
#   app/persistencia/banco.py -> parents[0]=persistencia, parents[1]=app, parents[2]=raiz
# Assim o caminho independe do diretório de onde o processo é iniciado.
CAMINHO_DADOS = Path(__file__).resolve().parents[2] / "data"
CAMINHO_BANCO = CAMINHO_DADOS / "plataforma.db"  # Arquivo físico do banco


def obter_conexao() -> sqlite3.Connection:
    """Cria (se não existir) e devolve uma conexão ao banco SQLite."""
    # Cria a pasta 'data' se ainda não existir, para não falhar na primeira execução.
    CAMINHO_DADOS.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(CAMINHO_BANCO)

    # row_factory = sqlite3.Row permite acessar as colunas POR NOME
    # (ex.: linha["nome"]), em vez de apenas por índice numérico (ex.: linha[1]).
    conexao.row_factory = sqlite3.Row
    return conexao