class Materia:
    def __init__(self, id, nome):
        if id is None:
            raise ValueError("O id da matéria é obrigatório.")

        if not nome or not nome.strip():
            raise ValueError("O nome da matéria é obrigatório.")

        self.id = id
        self.nome = nome