"""Infraestrutura e migrations do banco de dados."""

from app.persistencia.migrations.versao_1_aluno import MIGRATION


MIGRATIONS = (MIGRATION,)