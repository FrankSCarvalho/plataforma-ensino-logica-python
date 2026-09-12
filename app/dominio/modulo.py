from dataclasses import dataclass  # Gera automaticamente __init__, __eq__, __repr__, etc.
from datetime import datetime  # Representação de datas no domínio (stdlib, sem dependências)


# 'frozen=True' torna a dataclass IMUTÁVEL: depois de criada, não pode ser
# modificada. Assim protegemos as invariantes do domínio (nome sempre válido).
@dataclass(frozen=True)
class Modulo:
    """Representa um módulo da plataforma (entidade do domínio)."""

    # O id é opcional (None) pois, antes de ser persistido no banco,
    # o módulo ainda não possui identificador atribuído pelo sistema.
    id: int | None
    # 'materia_id' é apenas o identificador inteiro da matéria dona.
    # Não criamos um objeto Materia aqui: o vínculo é por identidade.
    materia_id: int
    nome: str
    # A descrição é opcional: o módulo pode ser criado sem explicação.
    descricao: str | None
    # 'ativa' indica se o módulo está disponível para estudo (bool no domínio).
    ativa: bool
    # 'ordem' é a posição organizacional do módulo (independente do id).
    ordem: int
    # Datas técnicas do registro (criação e última atualização).
    # A conversão para o formato armazenado no SQLite fica na persistência.
    data_criacao: datetime
    data_atualizacao: datetime

    # __post_init__ é um "gancho" que a dataclass executa após o __init__
    # automático. Serve para VALIDAR os campos antes de o objeto ser usado.
    def __post_init__(self) -> None:
        # 'materia_id' é obrigatório: representa a matéria dona pelo seu id.
        # Rejeitamos bool explicitamente porque, em Python, bool é subclasse
        # de int (True == 1) e não representa um identificador válido.
        if isinstance(self.materia_id, bool) or not isinstance(self.materia_id, int):
            raise ValueError("O módulo deve estar vinculado a uma matéria (materia_id).")
        # Garantimos que o nome não seja nulo, vazio nem só espaços.
        if not isinstance(self.nome, str) or not self.nome.strip():
            raise ValueError("O nome do módulo é obrigatório e não pode ser vazio.")
        # Garantia mínima da decisão F2-001.1 (TEXT ISO 8601 UTC no SQLite):
        # o domínio trabalha com datetime ciente de fuso, para que um
        # datetime ingênuo (sem tzinfo) nunca seja gravado como se fosse UTC.
        for rotulo, valor in (
            ("criação", self.data_criacao),
            ("atualização", self.data_atualizacao),
        ):
            if not isinstance(valor, datetime) or valor.tzinfo is None:
                raise ValueError(
                    f"A data de {rotulo} do módulo deve possuir fuso horário (UTC)."
                )
