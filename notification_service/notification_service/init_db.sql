-- ============================================================
-- Script SQL d'initialisation — Microservice Notification UADB
-- À exécuter une seule fois en tant que superutilisateur
-- psql -U postgres -f init_db.sql
-- ============================================================

-- 1. Créer l'utilisateur et la base si pas déjà fait
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_roles WHERE rolname = 'uadb5_user'
    ) THEN
        CREATE USER uadb5_user WITH PASSWORD 'uadb5_pass';
    END IF;
END $$;

SELECT 'CREATE DATABASE uadb5_db OWNER uadb5_user'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'uadb5_db'
)\gexec

-- 2. Se connecter à la base
\c uadb5_db

-- 3. Créer le schéma notification
CREATE SCHEMA IF NOT EXISTS notification
    AUTHORIZATION uadb5_user;

-- 4. Droits sur le schéma notification
GRANT ALL PRIVILEGES ON SCHEMA notification TO uadb5_user;
GRANT ALL PRIVILEGES ON ALL TABLES
    IN SCHEMA notification TO uadb5_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES
    IN SCHEMA notification TO uadb5_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA notification
    GRANT ALL ON TABLES    TO uadb5_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA notification
    GRANT ALL ON SEQUENCES TO uadb5_user;

-- 5. Schéma public (tables Django internes)
GRANT ALL PRIVILEGES ON SCHEMA public TO uadb5_user;
GRANT ALL PRIVILEGES ON ALL TABLES
    IN SCHEMA public TO uadb5_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES
    IN SCHEMA public TO uadb5_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES    TO uadb5_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON SEQUENCES TO uadb5_user;
