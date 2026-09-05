"""Camada de repositórios (acesso a dados persistentes).

Cada repositório concentra as operações de persistência de uma entidade,
utilizando consultas parametrizadas e a conexão da camada de banco.
"""

from app.repositories.aluno_repository import AlunoRepository
from app.repositories.exercicio_repository import ExercicioRepository
from app.repositories.habilidade_repository import HabilidadeRepository
from app.repositories.modulo_repository import ModuloRepository
from app.repositories.nivel_repository import NivelRepository
from app.repositories.progresso_aluno_repository import ProgressoAlunoRepository
from app.repositories.sessao_estudo_repository import SessaoEstudoRepository
from app.repositories.tentativa_repository import TentativaRepository

__all__ = [
    "AlunoRepository",
    "ModuloRepository",
    "HabilidadeRepository",
    "NivelRepository",
    "ExercicioRepository",
    "ProgressoAlunoRepository",
    "SessaoEstudoRepository",
    "TentativaRepository",
]