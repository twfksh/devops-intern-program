#!/bin/bash

LOCKFILE="/var/lock/lockfile"

(
  flock -xn 200 || { echo 'Lock is busy!'; exit 1; }
  # critical section start
  echo "sleeping"
  sleep 10
  # critical section end 
) 200>"$LOCKFILE"

