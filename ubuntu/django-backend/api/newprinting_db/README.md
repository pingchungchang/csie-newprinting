# newprinting_db
a docker-postgresql database for newprinting
To add new tables, add in init.sql, run `sudo docker compose down -v; sudo rm -rf ./pgdata; sudo docker compose up -d` to restart and empty the database
