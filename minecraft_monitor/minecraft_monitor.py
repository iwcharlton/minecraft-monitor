#!/usr/bin/env python
from flask import Flask
from flask_appconfig import AppConfig
from flask_bootstrap import Bootstrap
from flask_login import ( LoginManager, login_manager, login_required, login_user, logout_user )
from flask_socketio import SocketIO
import argparse
import json
import os

# Local imports
from frontend import frontend
from nav import nav
from server import Server
from user import User
import third_party
import utils

def create_app(config, log_limit):
  # Build and configure the app
  app = Flask(__name__)
  AppConfig(app)
  Bootstrap(app)

  # Login management
  app.config['SECRET_KEY'] = config['secret-key']
  
  login_manager = LoginManager()
  login_manager.init_app(app)
  login_manager.login_view = 'frontend.login'

  # Create users from simple config
  if 'users' in  config:
    print('Loading users from simple config')
    for user_id in config['users']:
      user = config['users'][user_id]
      User.add(user_id, user['name'], user['email'], user['password'])

  # We may have more advance SQL user management as an alternative...

  @login_manager.user_loader
  def load_user(user_id):
    return User.get(user_id)

  # Socket.io initialisation
  socketio = SocketIO(app)

  # Create our server object and allow the app templates to access it
  server = Server(socketio, config['location'], config['jar'], config['java-args'], log_limit)

  # Register all of the server actions and properties with the app
  server.register_global_functions(app)
  third_party.register_global_functions(app)
  utils.register_global_functions(app)
  server.register_blueprint_routes(frontend)
  utils.register_blueprint_routes(frontend)
  
  # Our application uses blueprints as well; these go well with the
  # application factory. We already imported the blueprint, now we just need
  # to register it:
  app.register_blueprint(frontend)

  # Because we're security-conscious developers, we also hard-code disabling
  # the CDN support (this might become a default in later versions):
  app.config['BOOTSTRAP_SERVE_LOCAL'] = True

  # We initialize the navigation as well
  nav.init_app(app)

  socketio.run(app, host=config['host'], port=config['port'])

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Run the Minecraft Server Monitor')
  parser.add_argument('--config', action='store', required=True, help='Path to the config file')
  parser.add_argument('--log-limit', action='store', type=int, required=False, help='Maximum number of log files to parse')
  args = parser.parse_args()

  # Load config and start
  config = None
  config_path = args.config
  if os.path.exists(config_path):
    print('loading config...')
    with open(config_path) as f:
      config = json.load(f)

  if config is None:
    print('Could not load config - unable to start')
    exit(1)

  create_app(config, args.log_limit)
  
