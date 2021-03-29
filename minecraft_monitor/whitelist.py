#!/usr/bin/env python
import json
import os

'''
The whitelist object is for reading the standard minecraft
whitelist.json, and also maintaining a blacklist.json.
'''
class Whitelist():
  def __init__(self, location):
    self.location = location
    self.disk_whitelist = []
    self.whitelist = None
    self.disk_blacklist = []
    self.blacklist = None

  def parse_whitelist(self):
    wl_path = os.path.join(self.location, 'whitelist.json')
    if os.path.exists(wl_path):
      print('parsing whitelist...')
      with open(wl_path) as f:
        self.disk_whitelist = json.load(f)
    if self.whitelist is None:
      self.whitelist = self.disk_whitelist
    bl_path = os.path.join(self.location, 'blacklist.json')
    if os.path.exists(bl_path):
      print('parsing blacklist...')
      with open(bl_path) as f:
        self.disk_blacklist = json.load(f)
    if self.blacklist is None:
      self.blacklist = self.disk_blacklist
  
  def restart_needed(self):
    return self.blacklist != self.disk_blacklist or self.whitelist != self.disk_whitelist
      
  def save_whitelist(self):
    wl_path = os.path.join(self.location, 'whitelist.json')
    with open(wl_path, 'w') as f:
      print('saving whitelist...')
      json.dump(self.whitelist, f)
    bl_path = os.path.join(self.location, 'blacklist.json')
    with open(bl_path, 'w') as f:
      print('saving blacklist...')
      json.dump(self.blacklist, f)
    self.parse_whitelist()

  def player_is_whitelisted(self, player):
    for wl in self.whitelist:
      if player == wl['name']:
        return True
    return False

  def player_is_blacklisted(self, player):
    for wl in self.blacklist:
      if player == wl['name']:
        return True
    return False

  def player_uuid(self, player):
    for wl in self.whitelist:
      if player == wl['name']:
        return wl['uuid']
    for wl in self.blacklist:
      if player == wl['name']:
        return wl['uuid']
    return False

  def add_player(self, player, uuid):
    if player is not None and uuid is not None:
      if self.player_is_whitelisted(player):
        print('ERROR: player {player} is already whitelisted')
        return False
      if self.player_is_blacklisted(player):
        print('ERROR: player {player} is already blacklisted')
        return False
      self.whitelist.append({ 'name': player, 'uuid': uuid })
      print('whitelisted player {player} with uuid {uuid}')
      self.save_whitelist()
      return True
    else:
      print('ERROR: player and uuid not provided for add_player')
      return False

  def whitelist_player(self, player):
    if player is not None:
      new_whitelist = [wl for wl in self.blacklist if wl['name'] == player]
      new_blacklist = [wl for wl in self.blacklist if wl['name'] != player]
      if len(new_blacklist) < len(self.blacklist):
        self.blacklist = new_blacklist
        self.whitelist.extend(new_whitelist)
        print(f'Whitelisted player {player}')
        self.save_whitelist()
        return True
      else:
        return False
    else:
      return False

  def blacklist_player(self, player):
    if player is not None:
      new_whitelist = [wl for wl in self.whitelist if wl['name'] != player]
      new_blacklist = [wl for wl in self.whitelist if wl['name'] == player]
      if len(new_whitelist) < len(self.whitelist):
        self.whitelist = new_whitelist
        self.blacklist.extend(new_blacklist)
        print(f'Blacklisted player {player}')
        self.save_whitelist()
        return True
      else:
        return False
    else:
      return False
