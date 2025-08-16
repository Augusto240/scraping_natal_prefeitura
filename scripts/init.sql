CREATE DATABASE natal_prefeitura WITH ENCODING 'UTF8';

\c natal_prefeitura;

CREATE TABLE IF NOT EXISTS publications (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    publication_date TIMESTAMP NOT NULL,
    competence VARCHAR(7) NOT NULL,
    original_link TEXT,
    file_path TEXT,
    file_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_publications_competence ON publications(competence);