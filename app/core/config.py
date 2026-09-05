"""Configurações centrais do projeto.

Esta camada concentra as definições de caminhos e configurações
compartilhadas por toda a aplicação, evitando que valores como a
localização do banco de dados fiquem espalhados pelo código.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos do projeto
# ---------------------------------------------------------------------------

# Raiz do projeto: app/core/config.py -> sobe 3 níveis até a pasta raiz.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Diretório onde ficam os dados gerados pela aplicação (ex.: banco SQLite).
DATA_DIR = PROJECT_ROOT / "data"

# Caminho completo do arquivo do banco de dados SQLite.
DATABASE_PATH = DATA_DIR / "plataforma_ensino_logica.db"