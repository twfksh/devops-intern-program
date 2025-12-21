FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

# install dependencies
RUN apt-get update && \
    apt-get install -y \
        postgresql-client \
        bash \
        gzip \
        findutils \
        cron && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/backups/postgres /var/lock /etc/cron.d

COPY pg-backup.sh /usr/local/bin/pg-backup.sh
RUN chmod +x /usr/local/bin/pg-backup.sh

COPY pg-backup.cron /etc/cron.d/pg-backup
RUN chmod 0644 /etc/cron.d/pg-backup && \
    crontab /etc/cron.d/pg-backup

CMD ["cron", "-f"]

