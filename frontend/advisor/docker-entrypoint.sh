#!/bin/sh
set -e

# Explicitly replace ONLY ${BACKEND_URL} and keep other variables (like $host, $uri) intact
envsubst '${BACKEND_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

exec "$@"
