#!/usr/bin/env python
import argparse
import json
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

users = {}

'''
Admin only function used to generate new JSON for the user list
'''
def generate_user_json(name, email, password):
  hash = generate_password_hash(password, method='sha256')
  user = {
    'name': name,
    'email': email,
    'password': hash
  }
  print(json.dumps(user, indent=2))

class User(UserMixin):
  def __init__(self, user_id, name, email, password):
    self.id = user_id
    self.name = name
    self.email = email
    self.password = password
    self.authenticated = True

  @staticmethod
  def add(user_id, name, email, password):
    if user_id not in users:
      users[user_id] = { "name": name, "email": email, "password": password }

  @staticmethod
  def get(user_id):
    if user_id not in users:
      return None

    user = users[user_id]
    user_ = User(user_id=user_id, name=user['name'], email=user['email'], password=user['password'])
    return user_

  @staticmethod
  def find(email):
    for user_id in users:
      user = users[user_id]
      if user['email'] == email:
        return User(user_id=user_id, name=user['name'], email=user['email'], password=user['password'])
        
    return None

  def check_password_hash(self, password):
    return check_password_hash(self.password, password)

  @property
  def is_active(self):
    return True

  @property
  def is_authenticated(self):
    return self.authenticated

  @property
  def is_anonymous(self):
    return False



if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='User admin for minecraft monitor')
  parser.add_argument('--name', action='store', type=str, required=True, help='The name for the user')
  parser.add_argument('--email', action='store', type=str, required=False, help='The email for the user')
  parser.add_argument('--pwd', action='store', type=str, required=False, help='The raw password for the user')
  args = parser.parse_args()

  generate_user_json(args.name, args.email, args.pwd)
  
