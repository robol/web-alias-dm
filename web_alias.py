from flask import Flask, jsonify, render_template
from datetime import datetime, timezone
import json, os, subprocess, requests, re

# Parse default options from the environment
conf_file = os.getenv('NGINX_ALIAS_FILE', '/etc/nginx/unipi-alias.conf')
userlist_file = os.getenv('LIST_FILE', '/var/www/html/index.html')
security_key = os.getenv('SECURITY_KEY', None)
alias_url = os.getenv('ALIAS_URL', 'https://manage.dm.unipi.it/api/v0/url')
list_url = os.getenv('LIST_URL', 'https://manage.dm.unipi.it/api/v0/public/urls')
reload_command = os.getenv('RELOAD_COMMAND', "systemctl reload nginx")
token = os.getenv('TOKEN', None)

app = Flask(__name__)

alias_template = """
location /{ALIASNAME} {
    alias /home/unipi/{OWNER}/{DESTINATION};
    try_files $uri $uri/ $uri.html =404;
    expires 300;

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_split_path_info ^/{ALIASNAME}(.+\.php)(.*);
        # This line is here to fix the path handling for the alias above
        fastcgi_param  SCRIPT_FILENAME    /home/unipi/{OWNER}/{DESTINATION}/$fastcgi_script_name;
        fastcgi_pass unix:/run/php/php8.1-fpm.sock;
    }
}
"""

@app.route("/")
def index():
    security_key_msg = "not set" if security_key is None else "set"

    return f"""<!DOCTYPE html>
    <html>
    <head><title>Nginx alias reload</title></head>
    <body>
    <h1>Nginx Alias Generator</h1>
    <p>Please perform a request to /alias/reload to actually reload the aliases on the web server.</p>
    <p>Current configuration:</p>
    <ul>
      <li><strong>Configuration file</strong>: {conf_file}</li>
      <li><strong>Security key</strong>: {security_key_msg}</li>
      <li><strong>Alias URL</strong>: {alias_url}</li>
      <li><strong>Reload command</strong>: {reload_command}</li>
    </ul>
    </body>
    </html>
    """

def format_alias(entry):
    if not validate_path(entry['alias']) or not validate_path(entry["destination"]):
        return ""

    return alias_template.replace(
        '{ALIASNAME}', entry["alias"]
    ).replace(
        '{OWNER}', entry["owner"]
    ).replace(
        '{DESTINATION}', entry["destination"]
    )

def validate_path(path):
    if '..' in path:
        return False

    return re.match('^[a-zA-Z_0-9/.-]*$', path)

def generate_user_list():
    template = userlist()
    with open(userlist_file, "w") as h:
        h.write(template)

@app.route('/list')
def userlist():
    r = requests.get(list_url).json()
    return render_template("userlist.html", alias = sorted(r['data'], key = lambda x : x['alias']))

@app.route("/alias/reload")
def reload_alias():
    try:
        headers = {}
        if token is not None:
            headers['Authorization'] = 'Bearer ' + token
        aliases = requests.get(alias_url, headers = headers).json()
        aliases = aliases['data']
    except:
        return jsonify({
            "error": f"Could not load new aliases from {alias_url}"
        }), 500
    
    try:
        alias_block = "\n".join(map(format_alias, aliases))
    except:
        return jsonify({
            "error": "An error occurred while formatting the alias file, aborting"
        }), 500
    
    try:
        with open(conf_file, "w") as h:
            generated_date = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            h.write(f"""
# This file has been automatically generated.
# 
# Script: {__file__}    
# Generated on: {generated_date} UTC
""")
            h.write(alias_block)
    except:
        return jsonify({
            "error": "An error occurred while writing the configuration file, aborting"
        }), 500
    
    # Try reloading the web server
    p = subprocess.Popen(reload_command, shell = True)
    if p.wait() != 0:
        return jsonify({
            "error": "An error occurred while reloading the webserver"
        }), 500
    
    # If everything was successful, we generate the list of users in the home-page.
    try:
        generate_user_list()
    except:
        return jsonify({
            "error": "An error occurred while generating the user list"
        }), 500

    return jsonify({
        "success": True
    })
