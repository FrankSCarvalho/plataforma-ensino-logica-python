from pathlib import Path

CAMINHO_SCHEMA =  Path(__file__).with_name("schema.sql")

def criar_tabelas(conexao):
    schema = CAMINHO_SCHEMA.read_text(encoding="utf-8")

    conexao.executescript(schema)
    conexao.commit()
    