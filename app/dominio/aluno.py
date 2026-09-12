from dataclasses import dataclass  # Gera automaticamente __init__, __eq__, __repr__, etc.


# 'frozen=True' torna a dataclass IMUTÁVEL: depois de criada, não pode ser
# modificada. Assim protegemos as invariantes do domínio (nome sempre válido).
@dataclass(frozen=True)
class Aluno:
    """Representa um aluno da plataforma (entidade do domínio)."""

    # O id é opcional (None) pois, antes de ser persistido no banco,
    # o aluno ainda não possui identificador atribuído pelo sistema.
    id: int | None
    nome: str

    # __post_init__ é um "gancho" que a dataclass executa após o __init__
    # automático. Serve para VALIDAR os campos antes de o objeto ser usado.
    def __post_init__(self) -> None:
        # Garantimos que o nome não seja vazio nem composto só por espaços.
        if not isinstance(self.nome, str) or not self.nome.strip():
            raise ValueError("O nome do aluno é obrigatório e não pode ser vazio.")