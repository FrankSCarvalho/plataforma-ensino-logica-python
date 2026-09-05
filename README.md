# Plataforma de Ensino de Lógica

Aplicativo desktop educacional para Windows com o objetivo de ensinar lógica de programação por meio de exercícios interativos e progressão guiada.

## Tecnologias

- **Python 3.11+**
- **Flet** (interface gráfica nativa do desktop)
- **SQLite** (persistência local)

## Pré-requisitos

- Python 3.11 ou superior instalado no computador (`python --version`)
- Windows como plataforma inicial

## Criação do ambiente virtual

```bash
python -m venv .venv
```

## Ativação do ambiente virtual (Windows)

No *Prompt de Comando*:

```bash
.venv\Scripts\activate
```

O prefixo `(.venv)` deve aparecer no início do prompt, indicando que o ambiente está ativo.

## Instalação das dependências

Com o ambiente virtual ativo, instale o projeto em modo editável junto com as dependências de desenvolvimento:

```bash
pip install -e ".[dev]"
```

## Execução do aplicativo

Com o ambiente virtual ativo, a partir da raiz do projeto:

```bash
python main.py
```

Deve abrir uma janela com "Plataforma de Ensino de Lógica".

## Execução dos testes

Com o ambiente virtual ativo, a partir da raiz do projeto:

```bash
python -m pytest
```

- verifica a inicialização da infraestrutura do banco SQLite;
- verifica que os módulos principais da aplicação importam sem erro.