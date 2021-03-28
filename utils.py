#!/usr/bin/env python
import requests
from flask import request

def register_global_functions(app):
  app.add_template_global(sanitise_string, 'sanitise_string')

def register_blueprint_routes(bp):
  bp.add_url_rule('/get_user_uuid', view_func=get_user_uuid)

def sanitise_string(text):
  return text.replace(' ', '').replace('.','-')

def get_user_uuid():
  username = request.args.get("username")
  if username is not None:
    response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
    if response.status_code == 200 and 'id' in response.json():
      uuid = response.json()['id']
      print(f"{username} current UUID is {uuid}")
      long_uuid = '{}-{}-{}-{}-{}'.format(uuid[0:8], uuid[8:12], uuid[12:16], uuid[16:20], uuid[20:32])
      return { 'uuid': long_uuid }, 200
    else:
      return { "ERROR": "bad username" }, 500
  else:
    return { "ERROR": "called with no username" }, 500
