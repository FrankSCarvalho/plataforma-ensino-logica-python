"""Camada de interface gráfica (Flet).

Telas do fluxo de estudo (Tarefa 08), cada uma em um módulo com
responsabilidade clara — a navegação entre elas fica em ``main_view``:

    * ``aluno_view``      — seleção/cadastro simples do aluno;
    * ``habilidade_view`` — lista de habilidades + progresso;
    * ``nivel_view``      — conteúdo conceitual do nível atual;
    * ``exercicio_view``  — exercícios, resposta, resultado e resumo;
    * ``components``      — tema e componentes reutilizáveis (Tarefa 09).

Nenhuma regra de negócio aqui: as telas apenas chamam
``app.services.fluxo_estudo`` (que orquestra repositórios, avaliador e
motor pedagógico).
"""