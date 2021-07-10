#!/usr/bin/env python
from flask_login import UserMixin

users = {
  '0001': {
    'name': 'Iain Charlton',
    'email': 'iwcharlton@gmail.com',
    'password': 'sha256$pmQ4Ncmw$fa12b60e19a5e5f35e7333028ac03e4cf6a7e428af52a1f0551e12515866882b'
  }
}

class User(UserMixin):
  def __init__(self, id_, name, email, password):
    self.id = id_
    self.name = name
    self.email = email
    self.password = password
    self.authenticated = True

  @staticmethod
  def get(user_id):
    if user_id not in users:
      return None

    user = users[user_id]
    user = User(id_=user_id, name=user['name'], email=user['email'], password=user['password'])
    return user

  @staticmethod
  def find(email):
    for user_id in users:
      user = users[user_id]
      if user['email'] == email:
        return User(id_=user_id, name=user['name'], email=user['email'], password=user['password'])
        
    return None

  @property
  def is_active(self):
    return True

  @property
  def is_authenticated(self):
    return self.authenticated

  @property
  def is_anonymous(self):
    return False

