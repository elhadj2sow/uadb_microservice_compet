-- ============================================================
-- Script SQL d'initialisation — Microservice Délibération UADB
-- À exécuter une seule fois en tant que superutilisateur
-- psql -U postgres -f init_db.sql
-- ============================================================

-- 1. Créer l'utilisateur et la base si pas déjà fait
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_roles WHERE rolname = 'uadb3_user'
    ) THEN
        CREATE USER uadb3_user WITH PASSWORD 'uadb3_pass';
    END IF;
END $$;

SELECT 'CREATE DATABASE uadb3_db OWNER uadb3_user'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'uadb3_db'
) \gexec

-- 2. Se connecter à la base
\c uadb3_db

-- 3. Créer le schéma deliberation
CREATE SCHEMA IF NOT EXISTS deliberation
    AUTHORIZATION uadb3_user;

-- 4. Droits sur le schéma deliberation
GRANT ALL PRIVILEGES ON SCHEMA deliberation TO uadb3_user;
GRANT ALL PRIVILEGES ON ALL TABLES
    IN SCHEMA deliberation TO uadb3_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES
    IN SCHEMA deliberation TO uadb3_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA deliberation
    GRANT ALL ON TABLES    TO uadb3_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA deliberation
    GRANT ALL ON SEQUENCES TO uadb3_user;

-- 5. Schéma public (tables Django internes)
GRANT ALL PRIVILEGES ON SCHEMA public TO uadb3_user;
GRANT ALL PRIVILEGES ON ALL TABLES
    IN SCHEMA public TO uadb3_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES
    IN SCHEMA public TO uadb3_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES    TO uadb3_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON SEQUENCES TO uadb3_user;
