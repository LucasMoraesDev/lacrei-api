-- Configurações iniciais do PostgreSQL para Lacrei Saúde
-- Executado automaticamente na primeira inicialização do container

-- Extensões úteis
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- para buscas full-text futuras

-- Configuração de timezone
SET timezone = 'America/Sao_Paulo';
