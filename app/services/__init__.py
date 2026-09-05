"""Camada de serviços (regras de negócio e orquestração).

Módulos disponíveis (importar diretamente do respectivo submódulo, o que
evita dependências circulares entre a inicialização do pacote e a
execução via ``python -m``):

    * ``app.services.carga_inicial``      — carga idempotente do currículo
      inicial (executável via ``python -m app.services.carga_inicial``).
    * ``app.services.avaliador``          — avaliação de respostas de
      exercícios (Tarefa 06); apenas responde se a resposta está correta,
      incorreta, parcialmente correta ou não avaliada.
    * ``app.services.registro_tentativas`` — orquestra o fluxo
      "resposta -> avaliação -> nova tentativa registrada" (Tarefa 06).
    * ``app.services.motor_pedagogico`` — interpreta o histórico de
      tentativas e decide a progressão entre níveis da mesma habilidade
      (Tarefa 07).

Nenhum destes serviços implementa o motor pedagógico (domínio,
progressão, repetição etc.) — decisão reservada para tarefa futura.
"""