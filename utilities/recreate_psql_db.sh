cd /var/lib/postgresql/

su postgres -c "psql ieddit -c \"DROP SCHEMA public CASCADE;\""
su postgres -c "psql ieddit -c \"CREATE SCHEMA public;\""
su postgres -c "psql ieddit -c \"GRANT ALL ON SCHEMA public TO postgres;\""
su postgres -c "psql ieddit -c \"GRANT ALL ON SCHEMA public TO public;\""
su postgres -c "psql ieddit -c \"COMMENT ON SCHEMA public IS 'standard public schema';\""
su postgres -c "psql ieddit -c \"CREATE USER test WITH PASSWORD 'test';\""
su postgres -c "psql ieddit -c \"ALTER SCHEMA public OWNER to postgres;\""

cd ~
