-- ============================================================
-- Script SQL d'initialisation — Microservice Dossier UADB
-- À exécuter une seule fois en tant que superutilisateur
-- psql -U postgres -f init_db.sql
-- ============================================================

-- 1. Créer l'utilisateur et la base (si pas déjà fait par auth_service)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'uadb2_user') THEN
        CREATE USER uadb2_user WITH PASSWORD 'uadb2_pass';
    END IF;
END
$$;

SELECT 'CREATE DATABASE uadb2_db OWNER uadb2_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'uadb2_db') \gexec

-- 2. Se connecter à la base
\c uadb2_db

-- 3. Créer le schéma dossier
CREATE SCHEMA IF NOT EXISTS dossier AUTHORIZATION uadb2_user;

-- 4. Droits complets sur le schéma dossier
GRANT ALL PRIVILEGES ON SCHEMA dossier TO uadb2_user;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA dossier TO uadb2_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA dossier TO uadb2_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA dossier
    GRANT ALL ON TABLES    TO uadb2_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA dossier
    GRANT ALL ON SEQUENCES TO uadb2_user;

-- 5. Schéma public (tables Django internes)
GRANT ALL PRIVILEGES ON SCHEMA public TO uadb2_user;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA public TO uadb2_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO uadb2_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES    TO uadb2_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON SEQUENCES TO uadb2_user;
