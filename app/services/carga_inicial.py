"""Carga inicial do currículo (seed).

Serviço responsável por inserir, de forma controlada e idempotente, o
primeiro conteúdo pedagógico da plataforma: o módulo "Lógica de
Programação" e a habilidade "Sequência de instruções" com seus níveis e
exercícios iniciais.

Características importantes:

  * IDEMPOTÊNCIA: cada entidade só é criada se ainda não existir (a busca
    é feita por nome dentro do pai correspondente). Executar a carga várias
    vezes NÃO duplica conteúdo — executá-la novamente apenas confirma que
    tudo que falta foi criado.
  * PRESERVAÇÃO: a carga nunca altera nem apaga registros existentes;
    apenas acrescenta o que está faltando.
  * SEM REGRA PEDAGÓGICA: este serviço apenas materializa conteúdo no
    banco; decisões de progressão/domínio pertencem ao motor pedagógico,
    que será implementado em tarefa futura.

Execução controlada (fora do ``main.py``):

    python -m app.services.carga_inicial

Todo o conteúdo abaixo é ORIGINAL desta plataforma — não copia apostilas
nem materiais de terceiros.
"""

from __future__ import annotations

from app.models import (
    TIPO_COMPLETAR_CODIGO,
    Exercicio,
    Habilidade,
    Modulo,
    Nivel,
)

from app.repositories import (
    ExercicioRepository,
    HabilidadeRepository,
    ModuloRepository,
    NivelRepository,
)

# ---------------------------------------------------------------------------
# Definição do currículo inicial (estrutura declarativa simples).
#
# Dicionários aninhados Módulo -> Habilidades -> Níveis -> Exercícios.
# Mantido como dado declarativo (e não como código espalhado) para que a
# evolução do currículo seja trivial em tarefas futuras.
# ---------------------------------------------------------------------------

CURRICULO_INICIAL: dict = {
    "nome": "Lógica de Programação",
    "descricao": (
        "Módulo inicial da plataforma. Trabalha os fundamentos da lógica "
        "de programação com pequenos passos progressivos, começando pela "
        "noção de sequência de instruções."
    ),
    "ordem": 1,
    "habilidades": [
        {
            "nome": "Sequência de instruções",
            "descricao": (
                "Compreender que um programa é formado por instruções "
                "executadas em uma ordem definida, uma após a outra."
            ),
            "ordem": 1,
            "niveis": [],  # preenchido abaixo, em partes
        },
    ],
}

# Nível 1 — compreensão do conceito de sequência.
NIVEL_1: dict = {
    "nome": "Nível 1 — O computador segue a ordem",
    "descricao": (
        "Compreender que um programa executa instruções "
        "em determinada sequência."
    ),
    "ordem": 1,
    "conteudo_titulo": "Um programa é uma lista de instruções",
    "conteudo_explicacao": (
        "Um programa é como uma receita: uma lista de instruções que o "
        "computador executa uma por vez, na ordem em que aparecem, sempre "
        "de cima para baixo. O computador não adivinha a intenção — ele "
        "faz exatamente o que está escrito, na ordem em que está escrito. "
        "Por isso, a posição de cada instrução importa: mudar a ordem das "
        "linhas muda o resultado do programa."
    ),
    "conteudo_exemplos": (
        "Exemplo 1 — três instruções nesta ordem:\n"
        "    escreva(\"A\")\n"
        "    escreva(\"B\")\n"
        "    escreva(\"C\")\n"
        "Resultado exibido na tela:\n"
        "    A\n"
        "    B\n"
        "    C\n"
        "\n"
        "Exemplo 2 — as mesmas instruções em outra ordem:\n"
        "    escreva(\"C\")\n"
        "    escreva(\"A\")\n"
        "    escreva(\"B\")\n"
        "Resultado exibido na tela:\n"
        "    C\n"
        "    A\n"
        "    B"
    ),
    "conteudo_observacoes": (
        "Neste momento usamos a instrução fictícia escreva(...), que "
        "apenas mostra um texto na tela. Cada linha é executada "
        "completamente antes de a próxima começar."
    ),
    "exercicios": [
        {
            "enunciado": (
                "Complete a lacuna para que o programa mostre "
                "\"Bola\" na tela:\n\n"
                "    escreva(______)\n"
            ),
            "codigo": "    escreva(______)",
            "ordem": 1,
            "tipo": TIPO_COMPLETAR_CODIGO,
            "resposta_esperada": '"Bola"',
        },
        {
            "enunciado": (
                "Complete a lacuna para que o programa mostre "
                "\"Chuteira\" na tela:\n\n"
                "    escreva(______)\n"
            ),
            "codigo": "    escreva(______)",
            "ordem": 2,
            "tipo": TIPO_COMPLETAR_CODIGO,
            "resposta_esperada": '"Chuteira"',
        },
        {
            "enunciado": (
                "Complete a lacuna para que o programa mostre primeiro "
                "\"Inicio\" e depois \"Fim\":\n\n"
                "    escreva(\"Inicio\")\n"
                "    ______\n"
            ),
            "codigo": "    escreva(\"Inicio\")\n    ______",
            "ordem": 3,
            "tipo": TIPO_COMPLETAR_CODIGO,
            "resposta_esperada": 'escreva("Fim")',
        },
    ],
}

CURRICULO_INICIAL["habilidades"][0]["niveis"].append(NIVEL_1)

# Nível 2 — identificar a ordem de execução.
NIVEL_2: dict = {
    "nome": "Nível 2 — Identificando a ordem de execução",
    "descricao": (
        "Identificar a ordem de execução de instruções, prevendo a "
        "saída completa de pequenos programas."
    ),
    "ordem": 2,
    "conteudo_titulo": "Prevendo a saída de um programa",
    "conteudo_explicacao": (
        "Ler um programa como um leitor: acompanhe as linhas na ordem em "
        "que aparecem e anote o que cada uma produz. Ao terminar de "
        "percorrer todas as linhas, a lista anotada é a saída do programa, "
        "nessa mesma ordem. Treinar esse acompanhamento linha a linha é a "
        "base para entender programas maiores."
    ),
    "conteudo_exemplos": (
        "Exemplo — acompanhe linha a linha:\n"
        "    escreva(\"Ana\")\n"
        "    escreva(\"Bia\")\n"
        "    escreva(\"Caio\")\n"
        "Acompanhamento: a linha 1 mostra Ana; a linha 2 mostra Bia; "
        "a linha 3 mostra Caio.\n"
        "Saída completa, em ordem:\n"
        "    Ana\n"
        "    Bia\n"
        "    Caio"
    ),
    "conteudo_observacoes": (
        "Instruções repetidas executam de novo, cada vez que aparecem. "
        "Se a mesma linha escreva(\"Oi\") estiver em duas posições, o "
        "texto Oi aparece duas vezes — uma por linha executada."
    ),
    "exercicios": [
        {
            "enunciado": (
                "Complete a lacuna para que a saída seja:\n"
                "    cafe\n"
                "    pao\n"
                "    leite\n\n"
                "Código:\n"
                "    escreva(\"cafe\")\n"
                "    escreva(______)\n"
                "    escreva(\"leite\")\n"
            ),
            "codigo": (
                "    escreva(\"cafe\")\n"
                "    escreva(______)\n"
                "    escreva(\"leite\")"
            ),
            "ordem": 1,
            "tipo": TIPO_COMPLETAR_CODIGO,
            "resposta_esperada": '"pao"',
        },
        {
            "enunciado": (
                "Complete a lacuna para que a palavra \"Oi\" apareça "
                "duas vezes:\n\n"
                "    escreva(\"Oi\")\n"
                "    ______\n"
            ),
            "codigo": "    escreva(\"Oi\")\n    ______",
            "ordem": 2,
            "tipo": TIPO_COMPLETAR_CODIGO,
            "resposta_esperada": 'escreva("Oi")',
        },
        {
            "enunciado": (
                "Complete a lacuna para que a saída seja, nesta ordem:\n"
                "    um\n"
                "    dois\n"
                "    tres\n\n"
                "Código:\n"
                "    escreva(\"um\")\n"
                "    escreva(______)\n"
                "    escreva(\"tres\")\n"
            ),
            "codigo": (
                "    escreva(\"um\")\n"
                "    escreva(______)\n"
                "    escreva(\"tres\")"
            ),
            "ordem": 3,
            "tipo": TIPO_COMPLETAR_CODIGO,
            "resposta_esperada": '"dois"',
        },
    ],
}

CURRICULO_INICIAL["habilidades"][0]["niveis"].append(NIVEL_2)

# Nível 3 — construir pequenas sequências.
NIVEL_3: dict = {
    "nome": "Nível 3 — Construindo sequências",
    "descricao": (
        "Construir pequenas sequências de instruções para produzir "
        "uma saída desejada."
    ),
    "ordem": 3,
    "conteudo_titulo": "Escrevendo sua própria sequência",
    "conteudo_explicacao": (
        "Agora o papel se inverte: em vez de prever a saída, você recebe "
        "a saída desejada e monta a lista de instruções que a produz. "
        "Escreva as linhas na ordem em que devem ser executadas, confira "
        "uma a uma e verifique se o resultado final é exatamente o "
        "pedido — nem a mais, nem a menos."
    ),
    "conteudo_exemplos": (
        "Objetivo: exibir na tela\n"
        "    bom\n"
        "    dia\n"
        "Solução (uma instrução por linha exibida):\n"
        "    escreva(\"bom\")\n"
        "    escreva(\"dia\")\n"
        "Repare: a primeira linha do programa produz a primeira linha "
        "da saída, e assim por diante."
    ),
    "conteudo_observacoes": (
        "Use a instrução escreva(\"...\") colocando o texto desejado "
        "entre aspas. Uma instrução por linha da saída desejada."
    ),
    "exercicios": [
        {
            "enunciado": (
                "Complete a lacuna para que o programa produza:\n"
                "    verde\n"
                "    amarelo\n"
                "    azul\n\n"
                "Código:\n"
                "    escreva(\"verde\")\n"
                "    ______\n"
                "    escreva(\"azul\")\n"
            ),
            "codigo": (
                "    escreva(\"verde\")\n"
                "    ______\n"
                "    escreva(\"azul\")"
            ),
            "ordem": 1,
            "tipo": TIPO_COMPLETAR_CODIGO,
            "resposta_esperada": 'escreva("amarelo")',
        },
        {
            "enunciado": (
                "Complete a lacuna para que a saída seja:\n"
                "    tres\n"
                "    dois\n"
                "    um\n\n"
                "Código:\n"
                "    escreva(\"tres\")\n"
                "    escreva(______)\n"
                "    escreva(\"um\")\n"
            ),
            "codigo": (
                "    escreva(\"tres\")\n"
                "    escreva(______)\n"
                "    escreva(\"um\")"
            ),
            "ordem": 2,
            "tipo": TIPO_COMPLETAR_CODIGO,
            "resposta_esperada": '"dois"',
        },
        {
            "enunciado": (
                "Complete a lacuna para que a saída seja:\n"
                "    Bom dia!\n"
                "    Boa noite!\n\n"
                "Código:\n"
                "    escreva(\"Bom dia!\")\n"
                "    ______\n"
            ),
            "codigo": "    escreva(\"Bom dia!\")\n    ______",
            "ordem": 3,
            "tipo": TIPO_COMPLETAR_CODIGO,
            "resposta_esperada": 'escreva("Boa noite!")',
        },
    ],
}

CURRICULO_INICIAL["habilidades"][0]["niveis"].append(NIVEL_3)


def carregar_curriculo_inicial() -> dict:
    """Insere o currículo inicial no banco, sem duplicar conteúdo.

    Estratégia de idempotência: antes de inserir cada entidade, verifica
    se ela já existe (busca por nome dentro do pai correspondente, usando
    as consultas dos repositórios). Entidades existentes são
    reaproveitadas — nada é atualizado ou removido.

    Retorna um resumo com o que foi criado nesta execução:

        {
            "modulo": Modulo,
            "modulo_criado": bool,
            "habilidade": Habilidade,
            "habilidade_criada": bool,
            "niveis_criados": int,
            "exercicios_criados": int,
            "respostas_esperadas_preenchidas": int,
            "codigos_preenchidos": int,
        }
    """
    repositorio_modulos = ModuloRepository()
    repositorio_habilidades = HabilidadeRepository()
    repositorio_niveis = NivelRepository()
    repositorio_exercicios = ExercicioRepository()

    resumo: dict = {
        "modulo_criado": False,
        "habilidade_criada": False,
        "niveis_criados": 0,
        "exercicios_criados": 0,
        # Quantidade de exercícios já gravados que receberam a resposta
        # esperada nesta execução (retrocompatibilidade com a migração v5).
        "respostas_esperadas_preenchidas": 0,
        # Quantidade de exercícios já gravados que receberam o código
        # nesta execução (retrocompatibilidade com a migração v6).
        "codigos_preenchidos": 0,
    }

    # ---- Módulo ------------------------------------------------------
    # Busca o módulo pelo nome entre os existentes (o volume é pequeno,
    # e a listagem do repositório já devolve modelos prontos).
    definicao_modulo = CURRICULO_INICIAL
    modulo = next(
        (
            m
            for m in repositorio_modulos.listar()
            if m.nome == definicao_modulo["nome"]
        ),
        None,
    )
    if modulo is None:
        modulo = repositorio_modulos.inserir(
            Modulo(
                nome=definicao_modulo["nome"],
                descricao=definicao_modulo["descricao"],
                ordem=definicao_modulo["ordem"],
            )
        )
        resumo["modulo_criado"] = True
    resumo["modulo"] = modulo

    # ---- Habilidade (somente a primeira: "Sequência de instruções") ---
    # Nesta tarefa apenas a primeira habilidade do módulo é carregada; as
    # demais serão acrescentadas em tarefas futuras seguindo a mesma
    # estratégia idempotente.
    definicao_habilidade = definicao_modulo["habilidades"][0]
    habilidade = next(
        (
            h
            for h in repositorio_habilidades.listar_por_modulo(modulo.id)
            if h.nome == definicao_habilidade["nome"]
        ),
        None,
    )
    if habilidade is None:
        habilidade = repositorio_habilidades.inserir(
            Habilidade(
                modulo_id=modulo.id,
                nome=definicao_habilidade["nome"],
                descricao=definicao_habilidade["descricao"],
                ordem=definicao_habilidade["ordem"],
            )
        )
        resumo["habilidade_criada"] = True
    resumo["habilidade"] = habilidade

    # ---- Níveis da habilidade ----------------------------------------
    for definicao_nivel in definicao_habilidade["niveis"]:
        nivel = next(
            (
                n
                for n in repositorio_niveis.listar_por_habilidade(habilidade.id)
                if n.nome == definicao_nivel["nome"]
            ),
            None,
        )
        if nivel is None:
            nivel = repositorio_niveis.inserir(
                Nivel(
                    habilidade_id=habilidade.id,
                    nome=definicao_nivel["nome"],
                    descricao=definicao_nivel["descricao"],
                    ordem=definicao_nivel["ordem"],
                    conteudo_titulo=definicao_nivel["conteudo_titulo"],
                    conteudo_explicacao=definicao_nivel["conteudo_explicacao"],
                    conteudo_exemplos=definicao_nivel["conteudo_exemplos"],
                    conteudo_observacoes=definicao_nivel["conteudo_observacoes"],
                )
            )
            resumo["niveis_criados"] += 1

        # ---- Exercícios do nível -------------------------------------
        # A duplicidade é evitada comparando a combinação
        # (ordem, enunciado), que identifica um exercício dentro do nível.
        for definicao_exercicio in definicao_nivel["exercicios"]:
            # Resposta esperada definida no currículo (Tarefa 06); vazia
            # quando o exercício não possui correção automática.
            resposta_esperada_definida = definicao_exercicio.get(
                "resposta_esperada", ""
            )
            # Código apresentado ao aluno (migração v6); vazio quando a
            # definição ainda não o possui (exercícios de bancos antigos).
            codigo_definido = definicao_exercicio.get("codigo", "")
            exercicio_existente = next(
                (
                    e
                    for e in repositorio_exercicios.listar_por_nivel(nivel.id)
                    if e.ordem == definicao_exercicio["ordem"]
                    and e.enunciado == definicao_exercicio["enunciado"]
                ),
                None,
            )
            if exercicio_existente is None:
                repositorio_exercicios.inserir(
                    Exercicio(
                        nivel_id=nivel.id,
                        enunciado=definicao_exercicio["enunciado"],
                        ordem=definicao_exercicio["ordem"],
                        tipo=definicao_exercicio["tipo"],
                        resposta_esperada=resposta_esperada_definida,
                        codigo=codigo_definido,
                    )
                )
                resumo["exercicios_criados"] += 1
            elif exercicio_existente.tipo == TIPO_COMPLETAR_CODIGO and (
                (
                    not exercicio_existente.resposta_esperada
                    and resposta_esperada_definida
                )
                or (not exercicio_existente.codigo and codigo_definido)
            ):
                # Retrocompatibilidade (Tarefas 06 e 07): exercícios
                # gravados antes das migrações v5/v6 não têm resposta
                # esperada nem código próprio. Preenche os campos UMA
                # única vez — nas execuções seguintes já estão preenchidos
                # e nada é alterado (idempotência). O enunciado, a ordem e
                # o conteúdo pedagógico já gravados NÃO são modificados.
                if (
                    not exercicio_existente.resposta_esperada
                    and resposta_esperada_definida
                ):
                    exercicio_existente.resposta_esperada = (
                        resposta_esperada_definida
                    )
                    resumo["respostas_esperadas_preenchidas"] += 1
                if not exercicio_existente.codigo and codigo_definido:
                    exercicio_existente.codigo = codigo_definido
                    resumo["codigos_preenchidos"] += 1
                repositorio_exercicios.atualizar(exercicio_existente)

    return resumo


if __name__ == "__main__":
    # Execução controlada da carga inicial: prepara o banco (aplicando as
    # migrações pendentes, se houver) e carrega o currículo.
    from app.database import initialize_database

    initialize_database()
    resultado = carregar_curriculo_inicial()

    print("Carga inicial concluída.")
    print(f"  Módulo: {resultado['modulo'].nome} "
          f"(criado agora: {resultado['modulo_criado']})")
    print(f"  Habilidade: {resultado['habilidade'].nome} "
          f"(criada agora: {resultado['habilidade_criada']})")
    print(f"  Níveis criados nesta execução: {resultado['niveis_criados']}")
    print("  Exercícios criados nesta execução: "
          f"{resultado['exercicios_criados']}")
    print("  Respostas esperadas preenchidas (retrocompatibilidade): "
          f"{resultado['respostas_esperadas_preenchidas']}")
    print("  Códigos preenchidos (retrocompatibilidade): "
          f"{resultado['codigos_preenchidos']}")