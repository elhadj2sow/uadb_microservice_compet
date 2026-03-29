-- ============================================================
-- Script SQL d'initialisation — Microservice Inscription UADB
-- À exécuter une seule fois en tant que superutilisateur
-- ============================================================

-- 1. Créer l'utilisateur et la base de données
CREATE USER uadb1_user WITH PASSWORD 'uadb1_pass';
CREATE DATABASE uadb_db1 OWNER uadb1_user;

-- 2. Se connecter à la base uadb_db1 puis exécuter :
\c uadb_db1

-- 3. Créer le schéma inscription
CREATE SCHEMA IF NOT EXISTS inscription AUTHORIZATION uadb1_user;

-- 4. Donner les droits à l'utilisateur
GRANT ALL PRIVILEGES ON SCHEMA inscription TO uadb1_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA inscription TO uadb1_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA inscription TO uadb1_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA inscription
    GRANT ALL ON TABLES TO uadb1_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA inscription
    GRANT ALL ON SEQUENCES TO uadb1_user;

-- 5. Schéma public (pour les tables Django internes : auth, sessions...)
GRANT ALL PRIVILEGES ON SCHEMA public TO uadb1_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO uadb1_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO uadb1_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES TO uadb1_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON SEQUENCES TO uadb1_user;
