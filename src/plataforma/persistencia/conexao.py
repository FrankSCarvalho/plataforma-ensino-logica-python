import sqlite3

def criar_conexao(caminho="plataforma.db"):
    conexao = sqlite3.connect(caminho)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao