from dataclasses import dataclass


@dataclass(frozen=True)
class Aluno:
    """Representa um aluno da plataforma."""

    id: int | None
    nome: str

    def __post_init__(self) -> None:
        if not isinstance(self.nome, str) or not self.nome.strip():
            raise ValueError("O nome do aluno é obrigatório e não pode ser vazio.")