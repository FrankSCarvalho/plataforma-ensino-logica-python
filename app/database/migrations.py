"""Migrações de schema do banco de dados.

Cada versão do banco é representada por uma lista de comandos SQL que
levam o esquema da versão ``n-1`` para a versão ``n``. A versão ativa
fica registrada no próprio banco através de ``PRAGMA user_version``.

Regra importante: uma migração JÁ APLICADA nunca deve ser editada.
Qualquer alteração futura no schema deve ser criada como uma nova
migração (versão seguinte), para que bancos existentes evoluam de forma
segura e incremental.
"""

# ---------------------------------------------------------------------------
# Versão 1 — banco base vazio (Tarefa 01)
# ---------------------------------------------------------------------------
# A Tarefa 01 apenas registrava ``user_version = 1`` sem criar tabelas.
# Não há comandos a executar nesta migração.
MIGRACAO_1 = []

# ---------------------------------------------------------------------------
# Versão 2 — entidades fundamentais do domínio (Tarefa 02)
# ---------------------------------------------------------------------------
# Cria as tabelas que representam o currículo (Módulo -> Habilidade ->
# Nível -> Exercício) e o Aluno (entidade independente).
#
# As chaves estrangeiras são declaradas sem ON DELETE CASCADE: o padrão
# do SQLite (NO ACTION/RESTRICT) impede a exclusão de um registro que
# possui filhos, protegendo a integridade do currículo. A exclusão de
# pais com filhos é tratada no nível dos repositórios, que recusam a
# operação com uma mensagem clara.
MIGRACAO_2 = [
    """
    CREATE TABLE IF NOT EXISTS modulos (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        nome       TEXT    NOT NULL,
        descricao  TEXT    NOT NULL DEFAULT '',
        ordem      INTEGER NOT NULL DEFAULT 0,
        ativo      INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS habilidades (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        modulo_id   INTEGER NOT NULL,
        nome        TEXT    NOT NULL,
        descricao   TEXT    NOT NULL DEFAULT '',
        ordem       INTEGER NOT NULL DEFAULT 0,
        ativo       INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (modulo_id) REFERENCES modulos (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS niveis (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        habilidade_id  INTEGER NOT NULL,
        nome           TEXT    NOT NULL,
        descricao      TEXT    NOT NULL DEFAULT '',
        ordem          INTEGER NOT NULL DEFAULT 0,
        ativo          INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (habilidade_id) REFERENCES habilidades (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS exercicios (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        nivel_id    INTEGER NOT NULL,
        enunciado   TEXT    NOT NULL,
        ordem       INTEGER NOT NULL DEFAULT 0,
        ativo       INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (nivel_id) REFERENCES niveis (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS alunos (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        nome           TEXT    NOT NULL,
        criado_em      TEXT    NOT NULL DEFAULT (datetime('now')),
        atualizado_em  TEXT    NOT NULL DEFAULT (datetime('now')),
        status         TEXT    NOT NULL DEFAULT 'ativo'
    )
    """,
]

# ---------------------------------------------------------------------------
# Versão 3 — infraestrutura de acompanhamento da aprendizagem (Tarefa 04)
# ---------------------------------------------------------------------------
# Cria as tabelas que registram o estado atual da trajetória do aluno
# (progresso_aluno), as sessões de estudo (sessoes_estudo) e as tentativas
# realizadas em exercícios (tentativas).
#
# IMPORTANTE sobre o histórico:
#   * Nenhuma dessas tabelas usa ON DELETE CASCADE. As tentativas antigas
#     precisam ser preservadas mesmo quando o progresso atual é atualizado;
#     estado atual (progresso_aluno) e histórico (sessões/tentativas) são
#     responsabilidades distintas.
#   * A exclusão desses registros será tratada em decisão futura; a camada
#     de repositórios bloqueia exclusões.
#
# A resposta da tentativa é TEXT, que no SQLite não possui limite prático
# de tamanho — adequado para respostas de programação (códigos longos).
# O tempo de resolução é armazenado em segundos (inteiro), uma unidade
# simples e consistente para cálculos futuros.
MIGRACAO_3 = [
    """
    CREATE TABLE IF NOT EXISTS sessoes_estudo (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id   INTEGER NOT NULL,
        inicio     TEXT    NOT NULL DEFAULT (datetime('now')),
        termino    TEXT    NULL,
        status     TEXT    NOT NULL DEFAULT 'ativa',
        FOREIGN KEY (aluno_id) REFERENCES alunos (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tentativas (
        id                       INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id                INTEGER NOT NULL,
        aluno_id                 INTEGER NOT NULL,
        exercicio_id             INTEGER NOT NULL,
        resposta                 TEXT    NOT NULL,
        resultado                TEXT    NOT NULL DEFAULT 'nao_avaliada',
        tempo_resolucao_segundos INTEGER NOT NULL DEFAULT 0,
        realizada_em             TEXT    NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (sessao_id)    REFERENCES sessoes_estudo (id),
        FOREIGN KEY (aluno_id)     REFERENCES alunos (id),
        FOREIGN KEY (exercicio_id) REFERENCES exercicios (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS progresso_aluno (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id       INTEGER NOT NULL,
        habilidade_id  INTEGER NOT NULL,
        nivel_id       INTEGER NOT NULL,
        status         TEXT    NOT NULL DEFAULT 'em_andamento',
        criado_em      TEXT    NOT NULL DEFAULT (datetime('now')),
        atualizado_em  TEXT    NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (aluno_id)      REFERENCES alunos (id),
        FOREIGN KEY (habilidade_id) REFERENCES habilidades (id),
        FOREIGN KEY (nivel_id)      REFERENCES niveis (id),
        UNIQUE (aluno_id, habilidade_id)
    )
    """,
]

# Mapa de migrações na ordem de aplicação. A chave é o número da versão.
MIGRACOES = {
    1: MIGRACAO_1,
    2: MIGRACAO_2,
    3: MIGRACAO_3,
}