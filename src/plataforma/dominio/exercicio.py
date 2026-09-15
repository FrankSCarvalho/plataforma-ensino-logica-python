class Exercicio:
    def __init__(self, id, enunciado, nivel_id):
        if id is None:
            raise ValueError("O id do exercicio é obrigatório.")

        if not enunciado or not enunciado.strip():
            raise ValueError("O enunciado do exercicio é obrigatório.")

        if nivel_id is None:
            raise ValueError("O nível do exercicio é obrigatório.")

        self.id = id
        self.enunciado = enunciado
        self.nivel_id = nivel_id