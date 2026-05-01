#!/usr/bin/env bash

set -e
cd "$(dirname "$0")"

set -a
source ../.env
set +a

docker run -d \
  --name web_app \
  --network host \
  --restart unless-stopped \
  -e APP_ENV=staging \
  -e FLASK_HOST=0.0.0.0 \
  -e SQLALCHEMY_DATABASE_URI="mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@localhost:${MYSQL_PORT}/${MYSQL_DATABASE}" \
  -e REDIS_HOST=localhost \
  "${IMAGE_NAME}:${IMAGE_TAG:-staging}" \
  sh -c "gunicorn --bind 0.0.0.0:5000 run:app"