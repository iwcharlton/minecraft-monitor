from flask import Flask
from flask_appconfig import AppConfig
from flask_bootstrap import Bootstrap
from flask_login import ( LoginManager, login_manager, login_required, login_user, logout_user )
from flask_socketio import SocketIO
#from flask_sqlalchemy import SQLAlchemy
import json
import os

# Local imports
from frontend import frontend
from nav import nav
from server import Server
from third_party import third_party_list
from user import User
import utils

def create_app(config):
  # Build and configure the app
  app = Flask(__name__)
  AppConfig(app)
  Bootstrap(app)

  # Login management
  app.config['SECRET_KEY'] = config['secret-key']
  app.config['SQLALCHEMY_DATABASE_URI'] = config['db-uri']
  
  login_manager = LoginManager()
  login_manager.init_app(app)
  login_manager.login_view = 'frontend.login'

  # Socket.io initialisation
  socketio = SocketIO(app)

  # Create our server object and allow the app templates to access it
  server = Server(socketio, config['location'], config['jar'], config['java-args'])

  # Register all of the server actions and properties with the app
  server.register_global_functions(app)
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

  @app.template_global()
  def get_third_party_list():
    return third_party_list

  @app.template_global()
  def global_log(text):
    print(text)

  @login_manager.user_loader
  def load_user(user_id):
    return User.get(user_id)
  
  socketio.run(app, host=config['host'], port=config['port'])

if __name__ == '__main__':
  config = None
  # Local config
  dir_path = os.path.dirname(os.path.realpath(__file__))
  config_path = os.path.join(dir_path, 'default-config.json')
  if os.path.exists(config_path):
    print('loading config...')
    with open(config_path) as f:
      config = json.load(f)

  if config is None:
    print('Could not load config - unable to start')
    exit(1)

  create_app(config)
  
