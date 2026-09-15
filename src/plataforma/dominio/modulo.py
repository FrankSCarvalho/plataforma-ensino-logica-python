class Modulo:
    def __init__(self, id, nome, materia_id):
        if id is None:
            raise ValueError("O id do módulo é obrigatório.")

        if not nome or not nome.strip():
            raise ValueError("O nome do módulo é obrigatório.")

        if materia_id is None:
            raise ValueError("A matéria do módulo é obrigatória.")

        self.id = id
        self.nome = nome
        self.materia_id = materia_id