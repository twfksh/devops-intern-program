#!/bin/bash
case "$1" in
  api)
    docker compose --profile api up -d
    ;;
  es)
    docker compose --profile es up -d
    ;;
  pgbackup)
    docker compose up --profile pgbackup up -d
    ;;
  misc)
    docker compose up --profile misc up -d
    ;;
  *)
    echo "Usage: $0 {api|worker|pgbackup}"
    ;;
esac

