DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'user') THEN
    CREATE USER "user" WITH PASSWORD 'password';
  END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE hotel_db TO "user";
ALTER SCHEMA public OWNER TO "user";
