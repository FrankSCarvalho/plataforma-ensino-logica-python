class Habilidade:
    def __init__(self, id, nome, modulo_id):
        if id is None:
            raise ValueError("O id da habilidade é obrigatório.")

        if not nome or not nome.strip():
            raise ValueError("O nome da habilidade é obrigatório.")

        if modulo_id is None:
            raise ValueError("O módulo da habilidade é obrigatório.")

        self.id = id
        self.nome = nome
        self.modulo_id = modulo_id