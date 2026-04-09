-- ============================================================
-- Script SQL d'initialisation — Microservice IA UADB
-- À exécuter une seule fois en tant que superutilisateur
-- psql -U postgres -f init_db.sql
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'uadb6_user') THEN
        CREATE USER uadb6_user WITH PASSWORD 'uadb6_pass';
    END IF;
END $$;

SELECT 'CREATE DATABASE uadb6_db OWNER uadb6_user'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'uadb6_db'
)\gexec

\c uadb6_db

CREATE SCHEMA IF NOT EXISTS ia AUTHORIZATION uadb6_user;

GRANT ALL PRIVILEGES ON SCHEMA ia TO uadb6_user;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA ia TO uadb6_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ia TO uadb6_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA ia GRANT ALL ON TABLES    TO uadb6_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA ia GRANT ALL ON SEQUENCES TO uadb6_user;

GRANT ALL PRIVILEGES ON SCHEMA public TO uadb6_user;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA public TO uadb6_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO uadb6_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES    TO uadb6_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO uadb6_user;
