from flask import Flask, jsonify
from datetime import datetime, timezone
import json, os, subprocess, requests, re

# Parse default options from the environment
conf_file = os.getenv('NGINX_ALIAS_FILE', '/etc/nginx/unipi-alias.conf')
security_key = os.getenv('SECURITY_KEY', None)
alias_url = os.getenv('ALIAS_URL', 'https://manage.dm.unipi.it/api/v0/url')
reload_command = os.getenv('RELOAD_COMMAND', "systemctl reload nginx")
token = os.getenv('TOKEN', None)

app = Flask(__name__)

alias_template = """
location /{ALIASNAME} {
    alias /home/unipi/{OWNER}/{DESTINATION};
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

    return jsonify({
        "success": True
    })
