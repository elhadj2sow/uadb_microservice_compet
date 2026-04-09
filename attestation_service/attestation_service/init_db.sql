-- ============================================================
-- Script SQL d'initialisation — Microservice Attestation UADB
-- À exécuter une seule fois en tant que superutilisateur
-- psql -U postgres -f init_db.sql
-- ============================================================

-- 1. Créer l'utilisateur et la base si pas déjà fait
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_roles WHERE rolname = 'uadb4_user'
    ) THEN
        CREATE USER uadb4_user WITH PASSWORD 'uadb4_pass';
    END IF;
END $$;

SELECT 'CREATE DATABASE uadb4_db OWNER uadb4_user'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'uadb4_db'
)\gexec

-- 2. Se connecter à la base
\c uadb4_db

-- 3. Créer le schéma attestation
CREATE SCHEMA IF NOT EXISTS attestation
    AUTHORIZATION uadb4_user;

-- 4. Droits sur le schéma attestation
GRANT ALL PRIVILEGES ON SCHEMA attestation TO uadb4_user;
GRANT ALL PRIVILEGES ON ALL TABLES
    IN SCHEMA attestation TO uadb4_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES
    IN SCHEMA attestation TO uadb4_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA attestation
    GRANT ALL ON TABLES    TO uadb4_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA attestation
    GRANT ALL ON SEQUENCES TO uadb4_user;

-- 5. Schéma public (tables Django internes)
GRANT ALL PRIVILEGES ON SCHEMA public TO uadb4_user;
GRANT ALL PRIVILEGES ON ALL TABLES
    IN SCHEMA public TO uadb4_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES
    IN SCHEMA public TO uadb4_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES    TO uadb4_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON SEQUENCES TO uadb4_user;
