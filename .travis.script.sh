#!/bin/bash
set -eo pipefail

flake8
pytest
docker build -t rickster001/sqldd:latest .

docker run -d -p "3306:3306" -e "MYSQL_ROOT_PASSWORD=password" -e "MYSQL_DATABASE=sqldd_db" --name mysql mysql:5.7
DB_INITIALIZED=0
DOCKER_INITIALIZED=0
COUNT=0
while [ "$DB_INITIALIZED" -eq 0 ] && [ "$COUNT" -lt 30 ]; do
  sleep 1

  if [ "$DOCKER_INITIALIZED" -eq 0 ]; then
  	if docker logs mysql 2>&1 | grep -o "MySQL init process done" >/dev/null; then
  		DOCKER_INITIALIZED=1
  	fi
  fi

  if [ "$DOCKER_INITIALIZED" -eq 1 ]; then
  	if mysql -uroot -ppassword -h127.0.0.1 -P3306 -e 'show tables;' sqldd_db; then
  		DB_INITIALIZED=1
  	fi
  fi

  COUNT=$((COUNT + 1))
done

if [ "$DB_INITIALIZED" -eq 0 ]; then
	{ docker rm -f mysql || true; } && exit 1
fi
echo "Starting live tests"

if ! pytest --runlivedb; then
	docker rm -f mysql >/dev/null
	exit 1
fi

docker rm -f mysql >/dev/null
