-- Crear la base de datos de tests
CREATE DATABASE butler_test;

-- Conectar a la base recién creada
\connect butler_test;

-- Crear esquema público si no existe
CREATE SCHEMA IF NOT EXISTS public;

-- Asignar todos los permisos al usuario principal
GRANT ALL PRIVILEGES ON DATABASE butler_test TO "ai-butler";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "ai-butler";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "ai-butler";

-- Garantizar permisos para futuros objetos
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO "ai-butler";
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON SEQUENCES TO "ai-butler";

