#!/bin/bash
set -eo pipefail

flake8
pytest
docker build -t rickster001/sqldd:latest .

docker run --rm -d -p "3306:3306" -e "MYSQL_ROOT_PASSWORD=password" -e "MYSQL_DATABASE=sqldd_db" --name mysql mysql:5.7
RC=1
COUNT=30
while [ "$RC" -eq 1 ] && [ "$COUNT" -gt 0 ]; do
  sleep 1
  if docker logs mysql 2>&1 | grep -o "MySQL init process done" >/dev/null; then
	RC=0
  else
	COUNT=$((COUNT + 1))
  fi
done

pytest --runlivedb

docker stop mysql
