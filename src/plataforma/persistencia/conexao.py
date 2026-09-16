import sqlite3

def criar_conexao():
    return sqlite3.connect("plataforma.db")