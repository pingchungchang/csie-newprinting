#!/bin/bash
set -e
CONN="$1"
psql "$CONN" -c "CREATE DATABASE newprinting_db"
# Replace dbname in the connection string to target the new database
CONN_NEWDB=$(echo "$CONN" | sed 's/dbname=[^ ]*/dbname=newprinting_db/')
psql "$CONN_NEWDB" -f /docker-entrypoint-initdb.d/init.sql
