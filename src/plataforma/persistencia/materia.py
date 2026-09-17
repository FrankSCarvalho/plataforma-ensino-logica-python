from src.plataforma.dominio.materia import Materia

def salvar_materia(conexao, materia):
    conexao.execute("INSERT INTO materia (id, nome) VALUES (?, ?)", (materia.id, materia.nome))

    conexao.commit()

def buscar_materia_por_id(conexao, id):
    resultado = conexao.execute("SELECT id, nome FROM materia WHERE id = ?", (id,),).fetchone()

    if resultado is None:
        return None

    return Materia(resultado[0], resultado[1])