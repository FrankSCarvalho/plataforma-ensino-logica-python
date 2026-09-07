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

# ---------------------------------------------------------------------------
# Versão 4 — conteúdo pedagógico do currículo (Tarefa 05)
# ---------------------------------------------------------------------------
# Prepara o armazenamento do conteúdo inicial do currículo:
#
#   * niveis: recebe colunas de conteúdo conceitual exibido antes dos
#     exercícios (título, explicação, exemplos e observações). Optou-se por
#     colunas na própria tabela ``niveis`` por ser a solução mais simples
#     possível (sem estruturas de CMS): cada nível possui um único bloco de
#     conteúdo, gravado como texto simples.
#
#   * exercicios: recebe a coluna ``tipo``, que torna a entidade extensível
#     para os tipos de exercício que serão implementados futuramente
#     (múltipla escolha, completar código, prever resultado etc.). Nesta
#     etapa a coluna apenas armazena o rótulo do tipo — nenhuma lógica de
#     correção é implementada.
#
# ALTER TABLE ADD COLUMN preserva todos os dados existentes e não recria
# tabelas. O valor NOT NULL é permitido no SQLite porque cada coluna nova
# possui um DEFAULT preenchido também nos registros já gravados.
MIGRACAO_4 = [
    "ALTER TABLE niveis ADD COLUMN conteudo_titulo      TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE niveis ADD COLUMN conteudo_explicacao  TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE niveis ADD COLUMN conteudo_exemplos    TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE niveis ADD COLUMN conteudo_observacoes TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE exercicios ADD COLUMN tipo TEXT NOT NULL DEFAULT 'resposta_textual'",
]

# ---------------------------------------------------------------------------
# Versão 5 — resposta esperada para correção automática (Tarefa 06)
# ---------------------------------------------------------------------------
# A correção do tipo ``prever_resultado`` exige que o exercício tenha uma
# resposta esperada para comparação determinística (sem IA e sem bibliotecas
# externas). A coluna é TEXT para permitir respostas de múltiplas linhas
# (por exemplo, a saída completa de um programa).
#
# ALTER TABLE ADD COLUMN preserva todos os dados existentes e não recria
# tabelas. O DEFAULT '' mantém os exercícios já gravados válidos: exercício
# sem resposta esperada simplesmente não é corrigido automaticamente
# (resultado ``nao_avaliada``), comportamento coerente com os demais tipos.
MIGRACAO_5 = [
    "ALTER TABLE exercicios ADD COLUMN resposta_esperada TEXT NOT NULL DEFAULT ''",
]

# ---------------------------------------------------------------------------
# Versão 6 — código apresentado ao aluno (Tarefa 07)
# ---------------------------------------------------------------------------
# Adiciona a coluna ``codigo`` à tabela ``exercicios``: contém o código que
# se apresenta ao aluno para que ele complete a lacuna (``______``). Esta
# coluna passa a ser a fonte principal do código exibido pela UI; o campo
# ``enunciado`` continua existendo como texto descritivo (alteração não
# destrutiva, sem remoção de colunas).
#
# ALTER TABLE ADD COLUMN preserva todos os dados existentes. O DEFAULT ''
# mantém os registros já gravados válidos: exercícios de bancos antigos
# não exibem a nova coluna até que a carga inicial a preencha.
MIGRACAO_6 = [
    "ALTER TABLE exercicios ADD COLUMN codigo TEXT NOT NULL DEFAULT ''",
]

# Mapa de migrações na ordem de aplicação. A chave é o número da versão.
MIGRACOES = {
    1: MIGRACAO_1,
    2: MIGRACAO_2,
    3: MIGRACAO_3,
    4: MIGRACAO_4,
    5: MIGRACAO_5,
    6: MIGRACAO_6,
}