#!/bin/bash

# File to be saved. Default: /etc/nginx/unipi-alias.conf
export NGINX_ALIAS_FILE="./unipi-alias.conf"

# Optional, if set it is checked in the Authorization: header
# export SECURITY_KEY=""

# URL for the API used to load the aliases
export ALIAS_URL=https://manage.dm.unipi.it/api/v0/url

# Secret token used in the HTTP header Authorization: Bearer ${TOKEN}
export TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Command to reload the nginx server. Default: systemctl reload nginx
export RELOAD_COMMAND="systemctl reload nginx"

if [ ! -x environment/bin/gunicorn ]; then
  python3 -mvenv environment
  environment/bin/pip3 install -r requirements.txt
fi

environment/bin/gunicorn -b '0.0.0.0:8000' -w 1 'web_alias:app'


