#!/usr/bin/env python
from flask import Blueprint, render_template, flash, redirect, url_for, request, abort
from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from urllib.parse import urlparse, urljoin
from werkzeug.security import generate_password_hash, check_password_hash

# Local imports
from nav import nav
from user import User

def is_safe_url(target):
  ref_url = urlparse(request.host_url)
  test_url = urlparse(urljoin(request.host_url, target))
  return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
          
frontend = Blueprint('frontend', __name__)

# We're adding a navbar as well through flask-navbar. In our example, the
# navbar has an usual amount of Link-Elements, more commonly you will have a
# lot more View instances.
def create_frontend_top():
  if current_user is not None and current_user.is_authenticated:
    return Navbar(
      View('Minecraft Monitor', '.index'),
      Text('Logged in as {}'.format(current_user.name)),
      View('Logout', '.logout'),
      View('Player Details', '.players'),
      View('Server Details', '.server'),
      View('Server Admin', '.admin'))
  else:
    return Navbar(
      View('Minecraft Monitor', '.index'),
      View('Login', '.login'),
      View('Player Details', '.players'),
      View('Server Details', '.server'),
      View('Server Admin', '.admin'))

nav.register_element('frontend_top', create_frontend_top)

# Our index-page just shows a quick explanation. Check out the template
# "templates/index.html" documentation for more details.
@frontend.route('/')
def index():
  return render_template('index.html')

@frontend.route('/login', methods=['POST', 'GET'])
def login():
  email = request.form.get('email')
  password = request.form.get('password')
  next = request.form.get('next')

  if email is not None:
    user = User.find(email)
    if user is None:
      flash('Unrecognised email', category='error')
    elif not user.check_password_hash(password):
      flash('Incorrect password', category='error')
    else:
      login_user(user)
      flash('Successfully logged in as {}'.format(current_user.name))
      
  if next is None or not is_safe_url(next):
    return render_template('login.html')

  return redirect(next or url_for('frontend.index'))
  

@frontend.route('/logout')
@login_required
def logout():
  logout_user()
  flash('Logged out')
  return render_template('login.html')

@frontend.route('/server')
def server():
  return render_template('server.html')

@frontend.route('/players')
def players():
  return render_template('players.html')

@frontend.route('/admin', methods=['POST', 'GET'])
@login_required
def admin():
  return render_template('admin.html')

@frontend.route('/third_party')
def third_party():
  return render_template('third_party.html')
'''
@frontend.route('/start_server')
def start_server():
  print('starting server...')
  return 'starting...'
  
@frontend.route('/stop_server')
def stop_server():
  print('stopping server...')
  return 'stopping...'
'''