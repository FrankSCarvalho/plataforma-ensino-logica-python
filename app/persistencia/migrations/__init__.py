"""
Infraestrutura e migrations do banco de dados.

Este pacote reúne TODAS as migrations do schema. Cada arquivo
'versao_N_*.py' define uma migração concreta; aqui elas são registradas
para que o executor as aplique em ordem de versão.
"""

from app.persistencia.migrations.versao_1_aluno import MIGRATION as MIGRATION_ALUNO
from app.persistencia.migrations.versao_2_materia import MIGRATION as MIGRATION_MATERIA
from app.persistencia.migrations.versao_3_modulo import MIGRATION as MIGRATION_MODULO


# Tupla ordenada das migrations disponíveis.
# Quando for adicionada uma nova migração, basta incluí-la nesta lista.
MIGRATIONS = (MIGRATION_ALUNO, MIGRATION_MATERIA, MIGRATION_MODULO)
