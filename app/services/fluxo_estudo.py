"""Serviço de fluxo de estudo (Tarefa 08).

Orquestra a primeira versão do fluxo real de estudo da plataforma,
ligando a interface (Flet) aos serviços existentes SEM conter SQL e SEM
conter regras pedagógicas próprias:

    carregar habilidades -> abrir habilidade (progresso inicial via motor
    pedagógico) -> iniciar sessão -> responder (avaliador + tentativa +
    motor pedagógico) -> avançar exercício/nível -> resumo -> encerrar.

Responsabilidades e limites:

    * toda persistência passa pelos repositories existentes;
    * a avaliação de respostas continua sendo responsabilidade exclusiva
      do serviço de avaliação/registro (Tarefa 06), via
      ``processar_resposta`` do motor pedagógico (Tarefa 07);
    * as contagens do resumo (corretas/incorretas/não avaliadas) são
      apenas INFORMATIVAS para a tela — nenhuma decisão pedagógica é
      tomada aqui;
    * a sessão de estudo é criada quando os exercícios começam e é
      encerrada pelo método ``encerrar_sessao`` (chamado pela UI em
      saídas normais do fluxo).
"""

from dataclasses import dataclass, field

from app.models import (
    RESULTADO_CORRETA,
    RESULTADO_INCORRETA,
    RESULTADO_NAO_AVALIADA,
    Aluno,
    Exercicio,
    Habilidade,
    Nivel,
    ProgressoAluno,
    SessaoEstudo,
)
from app.repositories import (
    AlunoRepository,
    ExercicioRepository,
    HabilidadeRepository,
    NivelRepository,
    ProgressoAlunoRepository,
    SessaoEstudoRepository,
)
from app.services.motor_pedagogico import (
    RegistroComProgressao,
    STATUS_CONCLUIDO,
    garantir_progresso_inicial,
    processar_resposta,
)


@dataclass
class EstadoEstudo:
    """Estado explícito da sessão de estudo de um aluno em uma habilidade.

    A UI mantém ESTA estrutura (evitando variáveis globais) e a atualiza
    por meio das funções deste módulo. Campos principais:

        * ``progresso``/``nivel``/``exercicios`` — estado atual do estudo;
        * ``sessao`` — sessão de estudo criada ao iniciar os exercícios
          (``None`` até que ``iniciar_sessao`` seja chamado);
        * ``indice_exercicio`` — exercício corrente na lista;
        * contadores do resumo (apenas informativos);
        * ``ultima_avaliacao``/``ultima_progressao`` — resultado da última
          resposta, para exibição do resultado e da progressão;
        * ``houve_progressao`` — reflete EXCLUSIVAMENTE a última resposta
          processada (True somente na resposta que causou progressão);
        * ``resumo_nivel_concluido`` — números do nível recém-concluído,
          preservados no momento da progressão para que a UI exiba o
          resumo ANTES de o aluno entrar no novo nível (``None`` quando
          não há progressão pendente).
    """

    aluno: Aluno
    habilidade: Habilidade
    progresso: ProgressoAluno
    nivel: Nivel
    exercicios: list[Exercicio]
    sessao: SessaoEstudo | None = None
    indice_exercicio: int = 0
    # Contadores informativos do resumo do nível.
    corretas: int = 0
    incorretas: int = 0
    nao_avaliadas: int = 0
    # Resultado da última resposta enviada.
    ultima_avaliacao: object | None = None
    ultima_progressao: RegistroComProgressao | None = None
    # Marca temporária usada pela UI para mostrar a mensagem de avanço.
    houve_progressao: bool = False
    resumo_nivel_concluido: dict | None = None
    historico: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Consultas simples usadas pelas telas (sem SQL: repositories fazem isso)
# ---------------------------------------------------------------------------

def listar_alunos() -> list[Aluno]:
    """Devolve todos os alunos cadastrados (tela de seleção)."""
    return AlunoRepository().listar()


def criar_aluno(nome: str) -> Aluno:
    """Cadastra um novo aluno (usado quando ainda não existe nenhum)."""
    return AlunoRepository().inserir(Aluno(nome=nome))


def listar_habilidades() -> list[Habilidade]:
    """Devolve as habilidades disponíveis no currículo (ordem pedagógica)."""
    return HabilidadeRepository().listar()


def nome_do_nivel(nivel_id: int) -> str:
    """Devolve o nome de um nível (para exibir o progresso na lista)."""
    nivel = NivelRepository().buscar_por_id(nivel_id)
    return nivel.nome if nivel is not None else "?"


def progresso_do_aluno(
    aluno_id: int, habilidade_id: int
) -> ProgressoAluno | None:
    """Devolve o progresso atual do aluno na habilidade (ou ``None``).

    Usado pela tela de habilidades para exibir a situação de cada item.
    A criação do progresso NÃO acontece aqui — apenas na abertura da
    habilidade, pelo motor pedagógico.
    """
    return ProgressoAlunoRepository().buscar_por_aluno_e_habilidade(
        aluno_id, habilidade_id
    )


def resumo_do_progresso(aluno_id: int, habilidade_id: int) -> str:
    """Texto informativo da situação do aluno em uma habilidade (lista).

    Centraliza aqui a frase exibida pela tela de habilidades, evitando
    regras de formatação dentro da view (que consulta o banco apenas
    através deste serviço):

        * sem progresso   -> "Estudo será iniciado no primeiro nível";
        * em andamento    -> "Em andamento — nível atual: <nome>";
        * concluída       -> "Concluída — nível atual: <nome>".
    """
    progresso = progresso_do_aluno(aluno_id, habilidade_id)
    if progresso is None:
        return "Estudo será iniciado no primeiro nível"
    situacao = (
        "Concluída" if progresso.status == STATUS_CONCLUIDO else "Em andamento"
    )
    return f"{situacao} — nível atual: {nome_do_nivel(progresso.nivel_id)}"


def posicao_do_nivel(estado: EstadoEstudo) -> tuple[int, int]:
    """Devolve ``(posicao, total)`` do nível atual dentro da habilidade.

    Usado pelas telas para exibir textos como "Nível 1 de 3" e para o
    resumo saber quando o aluno concluiu o último nível. Total zero indica
    habilidade sem níveis (caso de banco vazio).
    """
    niveis = NivelRepository().listar_por_habilidade(estado.habilidade.id)
    total = len(niveis)
    for posicao, nivel in enumerate(niveis, start=1):
        if nivel.id == estado.nivel.id:
            return posicao, total
    return 0, total


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------

def abrir_habilidade(aluno_id: int, habilidade_id: int) -> EstadoEstudo:
    """Abre uma habilidade para o aluno, SEM iniciar sessão de estudo.

    Passos:

        1. Garante a existência do progresso inicial (motor pedagógico):
           se o aluno nunca estudou a habilidade, o progresso é criado no
           primeiro nível com status ``em_andamento``; se já existe, o
           registro atual é reutilizado (nunca duplicado).
        2. Carrega o nível atual apontado pelo progresso e seus
           exercícios (na ordem pedagógica armazenada no banco).

    Levanta ``ValueError`` quando a habilidade não existe ou não possui
    níveis cadastrados.
    """
    habilidade = HabilidadeRepository().buscar_por_id(habilidade_id)
    if habilidade is None:
        raise ValueError(f"Habilidade {habilidade_id} não existe.")

    aluno = AlunoRepository().buscar_por_id(aluno_id)
    if aluno is None:
        raise ValueError(f"Aluno {aluno_id} não existe.")

    # Regra de criação do progresso pertence ao motor pedagógico (T.07).
    progresso = garantir_progresso_inicial(aluno_id, habilidade_id)

    nivel = NivelRepository().buscar_por_id(progresso.nivel_id)
    if nivel is None:
        raise ValueError(
            f"O progresso aponta para o nível {progresso.nivel_id}, "
            "que não existe."
        )

    exercicios = ExercicioRepository().listar_por_nivel(nivel.id)
    return EstadoEstudo(
        aluno=aluno,
        habilidade=habilidade,
        progresso=progresso,
        nivel=nivel,
        exercicios=exercicios,
    )


def iniciar_sessao(estado: EstadoEstudo) -> EstadoEstudo:
    """Cria a sessão de estudo para o aluno atual.

    Chamada pela UI quando o aluno inicia a sequência de exercícios. Se
    já existe uma sessão ativa neste estado, ela é encerrada antes de
    criar a nova (evita sessões abandonadas ao reentrar no fluxo).
    """
    if estado.sessao is not None:
        encerrar_sessao(estado)

    estado.sessao = SessaoEstudoRepository().inserir(
        SessaoEstudo(aluno_id=estado.aluno.id)
    )
    return estado


def exercicio_atual(estado: EstadoEstudo) -> Exercicio | None:
    """Devolve o exercício corrente (``None`` quando a lista terminou)."""
    if 0 <= estado.indice_exercicio < len(estado.exercicios):
        return estado.exercicios[estado.indice_exercicio]
    return None


def responder(estado: EstadoEstudo, resposta: str) -> EstadoEstudo:
    """Registra a resposta do aluno e atualiza o estado do estudo.

    Todo o fluxo pedagógico é delegado ao motor (Tarefa 07):
    ``processar_resposta`` = avaliador -> tentativa registrada ->
    consulta do histórico -> atualização do progresso. Aqui apenas:

        * atualiza os contadores INFORMATIVOS do resumo;
        * quando o motor determina domínio com próximo nível, recarrega
          o novo nível e seus exercícios (a MESMA sessão continua
          ativa — o aluno continua estudando);
        * caso contrário, avança o índice para o próximo exercício da
          lista (a tentativa já registrada nunca é apagada nem alterada).

    Levanta ``ValueError`` se não houver sessão ativa ou se a lista de
    exercícios já tiver terminado (a UI não deve permitir isso).
    """
    if estado.sessao is None:
        raise ValueError("Não há sessão de estudo ativa.")
    exercicio = exercicio_atual(estado)
    if exercicio is None:
        raise ValueError("Todos os exercícios deste ciclo já foram vistos.")

    resultado = processar_resposta(
        sessao_id=estado.sessao.id,
        aluno_id=estado.aluno.id,
        exercicio_id=exercicio.id,
        resposta=resposta,
    )

    # ---- Contadores informativos (nenhuma decisão pedagógica aqui) ----
    resultado_tentativa = resultado.registro.tentativa.resultado
    if resultado_tentativa == RESULTADO_CORRETA:
        estado.corretas += 1
    elif resultado_tentativa == RESULTADO_INCORRETA:
        estado.incorretas += 1
    elif resultado_tentativa == RESULTADO_NAO_AVALIADA:
        estado.nao_avaliadas += 1

    estado.ultima_avaliacao = resultado.registro.avaliacao
    estado.ultima_progressao = resultado
    estado.historico.append(resultado)

    if (
        resultado.progressao.dominio_atingido
        and resultado.progressao.proximo_nivel_id is not None
    ):
        # ---- Progressão: recarrega o novo nível da MESMA habilidade ----
        estado.houve_progressao = True
        estado.progresso = resultado.progressao.progresso
        novo_nivel = NivelRepository().buscar_por_id(
            resultado.progressao.proximo_nivel_id
        )
        if novo_nivel is None:  # defesa: nunca deveria ocorrer (FK)
            raise ValueError(
                "O próximo nível não foi encontrado no banco de dados."
            )
        # Preserva o resumo do nível ANTERIOR antes de zerar os contadores:
        # a UI exibe este resumo antes de entrar no novo nível.
        estado.resumo_nivel_concluido = {
            "nivel_id": estado.nivel.id,
            "nivel_nome": estado.nivel.nome,
            "corretas": estado.corretas,
            "incorretas": estado.incorretas,
            "nao_avaliadas": estado.nao_avaliadas,
            "total_respondidos": (
                estado.corretas
                + estado.incorretas
                + estado.nao_avaliadas
            ),
            "situacao": "Nível concluído",
            "proximo_passo": (
                f"Você avançou para o nível {novo_nivel.nome}. "
                "Clique em continuar para começar."
            ),
        }
        estado.nivel = novo_nivel
        estado.exercicios = ExercicioRepository().listar_por_nivel(
            novo_nivel.id
        )
        # Reinicia o índice e os contadores: o resumo é por nível.
        estado.indice_exercicio = 0
        estado.corretas = 0
        estado.incorretas = 0
        estado.nao_avaliadas = 0
    else:
        # Continua no nível: apenas avança para o próximo exercício.
        # Quando a lista termina, ``exercicio_atual`` passa a devolver
        # ``None`` e a UI apresenta o resumo.
        #
        # NOTA: Resetamos ``houve_progressao`` aqui para que a flag
        # represente APENAS o resultado da última resposta processada.
        # Ela será True apenas na resposta que causou progressão.
        estado.houve_progressao = False
        estado.indice_exercicio += 1

    return estado


def reiniciar_lista_de_exercicios(estado: EstadoEstudo) -> EstadoEstudo:
    """Recomeça a lista de exercícios do nível atual (mais prática).

    O aluno continua no mesmo nível; as tentativas anteriores permanecem
    no histórico (o critério de domínio considera a janela de tentativas
    avaliadas, independentemente dos ciclos pela lista).
    """
    estado.indice_exercicio = 0
    estado.corretas = 0
    estado.incorretas = 0
    estado.nao_avaliadas = 0
    estado.ultima_avaliacao = None
    return estado


def encerrar_sessao(estado: EstadoEstudo) -> EstadoEstudo:
    """Encerra a sessão de estudo (preenche ``termino`` e o status)."""
    if estado.sessao is not None:
        SessaoEstudoRepository().encerrar(estado.sessao)
        estado.sessao = None
    return estado