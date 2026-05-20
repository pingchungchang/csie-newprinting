#!/bin/bash
set -e
CONN="$1"
psql "$CONN" -c "CREATE DATABASE newprinting_db"
psql "$CONN" -d newprinting_db -f /docker-entrypoint-initdb.d/init.sql
