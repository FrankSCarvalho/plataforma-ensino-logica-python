"""Camada de banco de dados (infraestrutura SQLite).

Expõe a API pública desta camada para as demais camadas da aplicação.
"""

from app.database.connection import get_connection
from app.database.initialize import SCHEMA_VERSION, initialize_database

__all__ = ["get_connection", "SCHEMA_VERSION", "initialize_database"]