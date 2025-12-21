#!/bin/bash

BACKUP_DIR=${BACKUP_DIR:-/var/backups/postgres}
RETENTION_DAYS=${RETENTION_DAYS:-7}

POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}

POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=${POSTGRES_DB}

DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/${POSTGRES_DB}_backup_$DATE.sql.gz"

mkdir -p "$BACKUP_DIR"

command -v pg_dump >/dev/null 2>&1 || { echo "pg_dump not found, exiting."; exit 1; }

LOCKFILE="/var/lock/pgbackup-lock"

(
    flock -xn 200 || { echo "Another backup in progress, exiting."; exit 1; }

    export PGPASSWORD="$POSTGRES_PASSWORD"

    [ -z "$POSTGRES_USER" ] && echo "POSTGRES_USER is not set" && exit 1
    [ -z "$POSTGRES_PASSWORD" ] && echo "POSTGRES_PASSWORD is not set" && exit 1
    [ -z "$POSTGRES_DB" ] && echo "POSTGRES_DB is not set" && exit 1

    echo "Backing up database $POSTGRES_DB..."
    pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_FILE"

    if [ $? -eq 0 ]; then
        echo "Backup successful: $BACKUP_FILE"
    else
        echo "Backup failed!"
        exit 1
    fi

    # Remove backups older than 7 days
    echo "Removing backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -type f -name "${POSTGRES_DB}_backup_*.sql.gz" -mtime +$RETENTION_DAYS -exec rm {} \;

    echo "Backup completed."
) 200>"$LOCKFILE"
