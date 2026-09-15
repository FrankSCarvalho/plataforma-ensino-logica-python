class Nivel:
    def __init__(self, id, numero, habilidade_id):
        if id is None:
            raise ValueError("O id do nível é obrigatório.")

        if numero is None:
            raise ValueError("O número do nível é obrigatório.")

        if numero <= 0:
            raise ValueError("O número do nível deve ser maior que zero.")

        if habilidade_id is None:
            raise ValueError("A habilidade do nível é obrigatória.")

        self.id = id
        self.numero = numero
        self.habilidade_id = habilidade_id