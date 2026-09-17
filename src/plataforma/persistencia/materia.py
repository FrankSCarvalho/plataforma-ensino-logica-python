from src.plataforma.dominio import materia

def salvar_materia(conexao, materia):
    conexao.execute("INSERT INTO materia (id, nome) VALUES (?, ?)", (materia.id, materia.nome))
    
    conexao.commit()