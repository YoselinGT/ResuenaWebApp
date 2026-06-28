-- init.sql — Inicialización de la base de datos Resuena.
-- Se ejecuta una sola vez al crear el volumen de PostgreSQL.
-- La BD `resuena` ya la crea el contenedor vía POSTGRES_DB; aquí solo
-- habilitamos extensiones y configuración base.

-- Extensiones requeridas por el dominio.
--   pgcrypto  → gen_random_uuid() para PKs UUID (regla no negociable).
--   uuid-ossp → utilidades UUID adicionales.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Zona horaria por defecto en UTC (timestamps siempre con timezone).
ALTER DATABASE resuena SET timezone TO 'UTC';
