-- ============================================================
-- Script SQL d'initialisation — Microservice Audit UADB
-- psql -U postgres -f init_db.sql
-- ============================================================

-- CREATE DATABASE ne peut pas être exécuté dans un bloc DO.
-- On utilise donc des commandes psql conditionnelles via \gexec.

SELECT 'CREATE USER uadb7_user WITH PASSWORD ''uadb7_pass'''
WHERE NOT EXISTS (
    SELECT 1 FROM pg_roles WHERE rolname = 'uadb7_user'
)
\gexec

SELECT 'CREATE DATABASE uadb7_db OWNER uadb7_user'
WHERE NOT EXISTS (
    SELECT 1 FROM pg_database WHERE datname = 'uadb7_db'
)
\gexec

\connect uadb7_db

CREATE SCHEMA IF NOT EXISTS audit AUTHORIZATION uadb7_user;

GRANT ALL PRIVILEGES ON SCHEMA audit TO uadb7_user;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA audit TO uadb7_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA audit TO uadb7_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON TABLES    TO uadb7_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON SEQUENCES TO uadb7_user;

GRANT ALL PRIVILEGES ON SCHEMA public TO uadb7_user;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA public TO uadb7_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO uadb7_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES    TO uadb7_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO uadb7_user;
