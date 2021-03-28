#!/usr/bin/env python
from flask_login import UserMixin

#from db import get_db

users = {
  '0001': {
    'name': 'Iain Charlton',
    'email': 'iwcharlton@gmail.com',
    'password': 'sha256$YkDh5nWs$7e1e5aeb4e3e083799ddba981258ab4ea317bd757b6a691d00597007dec5081d'
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
    #db = get_db()
    #user = db.execute("SELECT * FROM user WHERE id = ?", (user_id,)
    #).fetchone()
    if user_id not in users:
      return None

    user = users[user_id]
    user = User(id_=user_id, name=user['name'], email=user['email'], password=user['password'])
    return user

  @staticmethod
  def find(email):
    #db = get_db()
    #user = db.execute("SELECT * FROM user WHERE email = ?", (email,)
    #).fetchone()
    for user_id in users:
      user = users[user_id]
      if user['email'] == email:
        return User(id_=user_id, name=user['name'], email=user['email'], password=user['password'])
        
    return None

  #@staticmethod
  #def create(id_, name, email):
  #  db = get_db()
  #  db.execute(
  #    "INSERT INTO user (id, name, email, profile_pic) "
  #    "VALUES (?, ?, ?, ?)",
  #    (id_, name, email, profile_pic),
  #  )
  #  db.commit()
  
  @property
  def is_active(self):
    return True

  @property
  def is_authenticated(self):
    return self.authenticated

  @property
  def is_anonymous(self):
    return False
