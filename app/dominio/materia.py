from dataclasses import dataclass  # Gera automaticamente __init__, __eq__, __repr__, etc.
from datetime import datetime  # Representação de datas no domínio (stdlib, sem dependências)


# 'frozen=True' torna a dataclass IMUTÁVEL: depois de criada, não pode ser
# modificada. Assim protegemos as invariantes do domínio (nome sempre válido).
@dataclass(frozen=True)
class Materia:
    """Representa uma matéria da plataforma (entidade do domínio)."""

    # O id é opcional (None) pois, antes de ser persistido no banco,
    # a matéria ainda não possui identificador atribuído pelo sistema.
    id: int | None
    nome: str
    # A descrição é opcional: a matéria pode ser criada sem explicação.
    descricao: str | None
    # 'ativa' indica se a matéria está disponível para estudo.
    ativa: bool
    # 'ordem' é a posição organizacional da matéria (independente do id).
    ordem: int
    # Datas técnicas do registro (criação e última atualização).
    # A conversão para o formato armazenado no SQLite fica na persistência.
    data_criacao: datetime
    data_atualizacao: datetime

    # __post_init__ é um "gancho" que a dataclass executa após o __init__
    # automático. Serve para VALIDAR os campos antes de o objeto ser usado.
    def __post_init__(self) -> None:
        # Garantimos que o nome não seja vazio nem composto só por espaços.
        if not isinstance(self.nome, str) or not self.nome.strip():
            raise ValueError("O nome da matéria é obrigatório e não pode ser vazio.")
        # Garantia mínima da decisão F2-001.1 (TEXT ISO 8601 UTC no SQLite):
        # o domínio trabalha com datetime ciente de fuso, para que um
        # datetime ingênuo (sem tzinfo) nunca seja gravado como se fosse UTC.
        for rotulo, valor in (
            ("criação", self.data_criacao),
            ("atualização", self.data_atualizacao),
        ):
            if not isinstance(valor, datetime) or valor.tzinfo is None:
                raise ValueError(
                    f"A data de {rotulo} da matéria deve possuir fuso horário (UTC)."
                )