#!/bin/bash

LOCKFILE="/var/lock/lockfile"

(
  flock -sn 200 || { echo "Another process holds exclusive lock. Exiting."; exit 1; }
  # critical section start
  echo "sleeping"
  sleep 10
  # critical section end
) 200>"$LOCKFILE"
