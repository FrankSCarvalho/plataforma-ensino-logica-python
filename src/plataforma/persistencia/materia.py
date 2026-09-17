from src.plataforma.dominio.materia import Materia

def salvar_materia(conexao, materia):
    conexao.execute("INSERT INTO materia (id, nome) VALUES (?, ?)", (materia.id, materia.nome))

    conexao.commit()