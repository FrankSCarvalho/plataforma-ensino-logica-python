"""Camada de modelos de domínio (representação dos dados).

Os modelos são classes simples e independentes da interface Flet e do
banco de dados: não contêm SQL nem regras de negócio complexas.
"""

from app.models.aluno import Aluno
from app.models.exercicio import Exercicio
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
]