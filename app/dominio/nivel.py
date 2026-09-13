from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Nivel:
    """Representa um nível curricular vinculado a uma habilidade."""

    id: int | None
    habilidade_id: int
    nome: str
    descricao: str
    ativa: bool
    ordem: int
    data_criacao: datetime
    data_atualizacao: datetime

    def __post_init__(self) -> None:
        if isinstance(self.habilidade_id, bool) or not isinstance(self.habilidade_id, int):
            raise ValueError("O nível deve estar vinculado a uma habilidade (habilidade_id).")
        if not isinstance(self.nome, str) or not self.nome.strip():
            raise ValueError("O nome do nível é obrigatório e não pode ser vazio.")
        if not isinstance(self.descricao, str) or not self.descricao.strip():
            raise ValueError("A descrição do nível é obrigatória e não pode ser vazia.")
        for rotulo, valor in (
            ("criação", self.data_criacao),
            ("atualização", self.data_atualizacao),
        ):
            if not isinstance(valor, datetime) or valor.tzinfo is None:
                raise ValueError(
                    f"A data de {rotulo} do nível deve possuir fuso horário (UTC)."
                )
