# Production PostgreSQL 17 Image for Tech4Future-Global
FROM postgres:17-alpine

# Copy custom postgresql.conf and initialization scripts
COPY docker/postgres/postgresql.conf /etc/postgresql/postgresql.conf
COPY docker/postgres/init-db.sh /docker-entrypoint-initdb.d/01-init-db.sh

RUN chmod +x /docker-entrypoint-initdb.d/01-init-db.sh

# Use customized config file
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
