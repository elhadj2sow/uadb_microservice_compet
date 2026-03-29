-- ============================================================
-- Script SQL d'initialisation — Microservice Auth UADB
-- À exécuter une seule fois en tant que superutilisateur
-- psql -U postgres -f init_db.sql
-- ============================================================

-- 1. Créer l'utilisateur PostgreSQL
CREATE USER uadb_user WITH PASSWORD 'uadb_pass';

-- 2. Créer la base de données
CREATE DATABASE uadb_db OWNER uadb_user;

-- 3. Se connecter à la base
\c uadb_db

-- 4. Créer le schéma auth_uadb
CREATE SCHEMA IF NOT EXISTS auth_uadb AUTHORIZATION uadb_user;

-- 5. Droits complets sur le schéma auth_uadb
GRANT ALL PRIVILEGES ON SCHEMA auth_uadb TO uadb_user;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA auth_uadb TO uadb_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth_uadb TO uadb_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth_uadb
    GRANT ALL ON TABLES    TO uadb_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth_uadb
    GRANT ALL ON SEQUENCES TO uadb_user;

-- 6. Schéma public (tables Django internes : sessions, permissions…)
GRANT ALL PRIVILEGES ON SCHEMA public TO uadb_user;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA public TO uadb_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO uadb_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES    TO uadb_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON SEQUENCES TO uadb_user;
