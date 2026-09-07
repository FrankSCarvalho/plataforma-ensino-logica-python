"""Camada de modelos de domínio (representação dos dados).

Os modelos são classes simples e independentes da interface Flet e do
banco de dados: não contêm SQL nem regras de negócio complexas.
"""

from app.models.aluno import Aluno
from app.models.avaliacao import (
    RESULTADO_CORRETA,
    RESULTADO_INCORRETA,
    RESULTADO_NAO_AVALIADA,
    RESULTADO_PARCIALMENTE_CORRETA,
    RESULTADOS_AVALIACAO,
    Avaliacao,
)
from app.models.exercicio import (
    TIPO_COMPLETAR_CODIGO,
    TIPO_ESCREVER_CODIGO,
    TIPO_PADRAO,
    TIPO_PREVER_RESULTADO,
    TIPO_RESPOSTA_TEXTUAL,
    TIPOS_DE_EXERCICIO,
    Exercicio,
)
from app.models.habilidade import Habilidade
from app.models.modulo import Modulo
from app.models.nivel import Nivel
from app.models.progresso_aluno import ProgressoAluno
from app.models.sessao_estudo import SessaoEstudo
from app.models.tentativa import Tentativa

__all__ = [
    "Aluno",
    "Modulo",
    "Habilidade",
    "Nivel",
    "Exercicio",
    "ProgressoAluno",
    "SessaoEstudo",
    "Tentativa",
    # Constantes de tipos de exercício (Tarefa 05).
    "TIPO_RESPOSTA_TEXTUAL",
    "TIPO_ESCREVER_CODIGO",
    "TIPO_PREVER_RESULTADO",
    "TIPO_COMPLETAR_CODIGO",
    "TIPOS_DE_EXERCICIO",
    "TIPO_PADRAO",
    # Avaliação de respostas (Tarefa 06) — valores centralizados.
    "Avaliacao",
    "RESULTADO_CORRETA",
    "RESULTADO_INCORRETA",
    "RESULTADO_PARCIALMENTE_CORRETA",
    "RESULTADO_NAO_AVALIADA",
    "RESULTADOS_AVALIACAO",
]