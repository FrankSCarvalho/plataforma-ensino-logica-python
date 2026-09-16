CREATE TABLE IF NOT EXISTS materia (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS modulo(
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    materia_id INTEGER NOT NULL,
    FOREIGN KEY (materia_id) REFERENCES materia(id)
);

CREATE TABLE IF NOT EXISTS habilidade(
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    modulo_id INTEGER NOT NULL,
    FOREIGN KEY (modulo_id) REFERENCES modulo(id)
);

CREATE TABLE IF NOT EXISTS nivel(
    id INTEGER PRIMARY KEY,
    numero INTEGER NOT NULL CHECK (numero > 0),
    habilidade_id INTEGER NOT NULL,
    FOREIGN KEY (habilidade_id) REFERENCES habilidade(id)
);

CREATE TABLE IF NOT EXISTS exercicio(
    id INTEGER PRIMARY KEY,
    enunciado TEXT NOT NULL,
    nivel_id INTEGER NOT NULL,
    FOREIGN KEY (nivel_id) REFERENCES nivel(id)
);
