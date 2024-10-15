#!/bin/bash

# File to be saved. Default: /etc/nginx/unipi-alias.conf
export NGINX_ALIAS_FILE="/etc/nginx/unipi-alias.conf"

# Optional, if set it is checked in the Authorization: header
# export SECURITY_KEY=""

# URL to use to load the data; if not specified, some testing example data is used.
# export ALIAS_URL=

# Command to reload the nginx server. Default: systemctl reload nginx
export RELOAD_COMMAND="systemctl reload nginx"

if [ ! -x environment/bin/gunicorn ]; then
  python3 -mvenv environment
  environment/bin/pip3 install -r requirements.txt
fi

environment/bin/gunicorn -w 1 'web_alias:app'


