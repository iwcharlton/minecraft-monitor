#!/usr/bin/env python
import ast
import copy
import datetime
import gzip
import json
import os
import re
import signal
import subprocess
from enum import Enum
from flask import request

from log_parser import LogParser, date_from_name
from whitelist import Whitelist

'''
The log data object - gathers up all of the details we want from the log
'''
class LogData(object):
  def __init__(self, mtime):
    self.mtime = mtime

    self.details = {}
    self.players = {}
    self.text = ''

  def clear(self):
    self.mtime = None
    self.details = {}
    self.players = {}
    self.text = ''

  '''
  Collape another log object into this one:
   - accumulates some data (player stats)
   - takes the latest for data/time info
  '''
  def collapse(self, data):
    if self.mtime is None or self.mtime < data.mtime:
      self.mtime = data.mtime
      self.details = data.details

    for name, stats in data.players.items():
      if name not in self.players:
        self.players[name] = copy.deepcopy(stats)
      else:
        new_stats = self.players[name]
        for key, val in stats.items():
          if key == 'Last Login' or key == 'Last Logout': # This should really be done by identifying properties as being of different types
            if key not in new_stats or val > new_stats[key]:
              new_stats[key] = val
          else:
            if key in new_stats:
              new_stats[key] = new_stats[key] + val
            else:
              new_stats[key] = val

    # log text we'll ignore

'''
The pattern here is that the server registers properties and actions with the app
so they can be called within the Flask templates to make things happen on templates
filling (i.e. on page load).
'''
class Server(LogData):
  def __init__(self, socketio, location, jar, java_args):
    self.socketio = socketio

    self.location = location
    self.jar = jar
    self.java_args = java_args

    self.properties = {}
    self.prop_separator = '='
    self.properties_backups = []

    self.log_parser = None
    self.logs = {}

    self.whitelist = Whitelist(location)

    self.is_running = False
    self.proc = None
    
    self.locked = False
    
    self.requires_restart = ''

    LogData.__init__(self, None) 

  '''
  Initialise a Flask app
  '''
  def register_global_functions(self, app):
    app.add_template_global(self.get_server, 'get_server')
    app.add_template_global(self.refresh_server, 'refresh_server')
    app.add_template_global(self.stop, 'stop_server')
    app.add_template_global(self.start, 'start_server')
    app.add_template_global(self.get_max_player_stats, 'get_max_player_stats')
    app.add_template_global(self.whitelist.player_uuid, 'get_player_uuid')
    app.add_template_global(self.whitelist.player_is_whitelisted, 'player_is_whitelisted')
    app.add_template_global(self.whitelist.player_is_blacklisted, 'player_is_blacklisted')
  
  def register_blueprint_routes(self, bp):
    bp.add_url_rule('/stop_server', view_func=self.stop)
    bp.add_url_rule('/start_server', view_func=self.start)
    bp.add_url_rule('/save_properties', view_func=self.save_properties)
    bp.add_url_rule('/restore_properties', view_func=self.restore_properties)
    bp.add_url_rule('/whitelist_player', view_func=self.whitelist_player)
    bp.add_url_rule('/blacklist_player', view_func=self.blacklist_player)
    bp.add_url_rule('/add_player_to_whitelist', view_func=self.add_player_to_whitelist)
  
  def get_server(self):
    if self.locked:
      return None
    else:
      return self

  def refresh_server(self):
    self.whitelist.parse_whitelist()
    self.load_properties()
    self.load_logs()
    for wl in self.whitelist.whitelist:
      if wl['name'] not in self.players:
        self.players[wl['name']] = {}
    for wl in self.whitelist.blacklist:
      if wl['name'] not in self.players:
        self.players[wl['name']] = {}
    if self.locked:
      return None
    else:
      return self

  def stop(self):
    if not self.is_running:
      return 'Unable to stop Minecraft Server - not running', 500

    print('stopping server...')
    if self.proc is not None:
      self.proc.terminate()

    self.is_running = False
    self.requires_restart = ''
    return 'Stopped Minecraft Server', 200

  def start(self):
    if self.is_running:
      return 'Unable to start Minecraft Server - already running', 500

    java_args = request.args.get('java_args')
    if java_args is not None:
      self.java_args = java_args
      print(f'starting server with args {java_args}...')
    else:
      print('starting server...')

    all_args = ['java']
    for arg in self.java_args.split(' '):
      all_args.append(arg)
    all_args.append('-jar')
    all_args.append(self.jar)

    self.proc = subprocess.Popen(all_args, cwd=self.location)
    if self.proc is not None:
      self.is_running = True
      return f'Started Minecraft Server, process ID is {self.proc.pid}', 200
    else:
      return 'Failed to start Minecraft Server', 500

  def get_max_player_stats(self):
    max_player = {}
    for name, stats in self.players.items():
      for key, val in stats.items():
        if key not in max_player or val > max_player[key]:
          max_player[key] = val
    return max_player

  def whitelist_player(self):
    player = request.args.get("player")
    if player is not None:
      if self.whitelist.whitelist_player(player):
        if self.is_running:
          self.requires_restart = 'Requires restart to relaod whitelist'
        return f'Whitelisted player {player}', 200
      else:
        return f'ERROR: whitelist_player called with unidentified player {player}', 500
    else:
      return 'ERROR: whitelist_player called with no player', 500
    
  def blacklist_player(self):
    player = request.args.get("player")
    if player is not None:
      if self.whitelist.blacklist_player(player):
        if self.is_running:
          self.requires_restart = 'Requires restart to relaod whitelist'
        return f'Blacklisted player {player}', 200
      else:
        return f'ERROR: blacklist_player called with unidentified player {player}', 500
    else:
      return 'ERROR: blacklist_player called with no player', 500

  def add_player_to_whitelist(self):
    player = request.args.get("player")
    uuid   = request.args.get("uuid")
    if player is not None and uuid is not None:
      if self.whitelist.add_player(player, uuid):
        if self.is_running:
          self.requires_restart = 'Requires restart to relaod whitelist'
        return f'Whitelisted player {player}', 200
      else:
        return 'ERROR: whitelist_player failed', 500
    else:
      return 'ERROR: whitelist_player called with no player and uuid', 500
    
  def save_properties(self):
    if not self.backup_properties():
      return 'ERRER: unable to backup propertyfile, aborting', 500

    new_properties = {}
    for key, val in self.properties.items():
      new_val = request.args.get(key)
      if new_val is None:
        print(f'No value for {key}')
        return f'ERRER: property {key} not provided in query to save_properties', 500
      else:
        new_properties[key] = new_val

    self.properties = new_properties

    try:
      print('Saving properties file...')
      prop_path = os.path.join(self.location, f'server.properties')
      with open(prop_path, 'wt') as f:
        self.write_properties(f, self.properties)
        
      if self.is_running:
        self.requires_restart = 'Requires restart to relaod properties'
      return 'Properties saved to file', 200
    except:
      return 'ERROR: Unable to save properties to file', 500

  def restore_properties(self):
    backup = request.args.get('backup')
    if backup is None:
      return 'ERRER: backup not provided in query to save_properties', 500
    backup_path = os.path.join(self.location, f'server.properties.backup.{backup}')
    if not os.path.exists(backup_path):
      return 'ERRER: property backup {prop_path} does not exist', 500
    
    if not self.backup_properties():
      return 'ERRER: unable to backup propertyfile, aborting', 500

    try:
      with open(backup_path) as f:
        self.parse_properties(f, self.properties)

      prop_path = os.path.join(self.location, f'server.properties')
      with open(prop_path, 'wt') as f:
        self.write_properties(f, self.properties)
        
      if self.is_running:
        self.requires_restart = 'Requires restart to relaod properties'
      return 'Properties saved to file', 200
    except:
      return 'ERROR: Unable to save properties to file', 500

    return 'Restored property backup {prop_path} ', 200

  def backup_properties(self):
    backup = 1
    prop_path = os.path.join(self.location, f'server.properties.backup.{backup}')
    while os.path.exists(prop_path):
      backup = backup + 1
      prop_path = os.path.join(self.location, f'server.properties.backup.{backup}')
    try:
      print(f'Backing up properties to file {prop_path}...')
      with open(prop_path, 'wt') as f:
        self.write_properties(f, self.properties)
      return True
    except:
      print(f'Unable to backup properties to file {prop_path}')
      return False

  def write_properties(self, file, properties):
    file.write('#Minecraft Server Properties\n')
    file.write('#' + datetime.datetime.now().strftime('%c') + '\n')
    for key, val in self.properties.items():
      if val is not None:
        file.write(f'{key}={val}\n')
      else:
        file.write(f'{key}=\n')

  def parse_properties(self, f, properties):
    print('parsing properties...')
    for line in f:
      if not line.startswith('#'):
        if self.prop_separator in line:
          name, value = line.split(self.prop_separator, 1)
          properties[name] = value.strip()
        else:
          name = line.split(self.prop_separator, 1)
          properties[name] = None
              
  def load_properties(self):
    new_properties = {}
    prop_path = os.path.join(self.location, 'server.properties')
    if os.path.exists(prop_path):
      with open(prop_path) as f:
        self.parse_properties(f, new_properties)
      self.properties = new_properties
    
    self.properties_backups = []
    backup = 1
    prop_path = os.path.join(self.location, f'server.properties.backup.{backup}')
    while os.path.exists(prop_path):
      mtime = os.path.getmtime(prop_path)
      time = datetime.datetime.fromtimestamp(mtime)
      self.properties_backups.append(time.strftime('%c'))
      backup = backup + 1
      prop_path = os.path.join(self.location, f'server.properties.backup.{backup}')

      
  def load_logs(self):
    if self.locked:
      print('log is locked')
      return

    self.locked = True
    
    # Lazy instantiation of the parser
    if not self.log_parser:
      dir_path = os.path.dirname(os.path.realpath(__file__))
      config_path = os.path.join(dir_path, 'logparse-config.json')
      if os.path.exists(config_path):
        print('loading log parser config...')
        with open(config_path) as f:
          config = json.load(f)
          server_log_events = config['server-events']
          player_log_events = config['player-events']

          self.log_parser = LogParser(server_log_events, player_log_events)

    # Use this to cut down load time
    loaded = 0
    max_to_load = 5

    # Parse the logs, but don't parse anything we've visited already
    log_path = os.path.join(self.location, 'logs', '')
    if os.path.exists(log_path) and self.log_parser:
      print('parsing logs...')
      filenames =  os.listdir(log_path)
      for filename in filenames:
        self.socketio.emit('log_loaded', { "percent": loaded / len(filenames), "loading": filename })
        fullpath = os.path.join(log_path, filename)
        shortname = filename.split('.', 1)[0]
        mtime = os.path.getmtime(fullpath)
        
        load_log = shortname not in self.logs or self.logs[shortname].mtime < mtime
        loaded = loaded + 1
        if loaded > max_to_load:
          load_log = False

        if load_log:
          print(f'loading {filename} for the first time')

          # Deal with plain and archive files
          f = None
          if filename.endswith('.gz'):
            f = gzip.open(fullpath, 'rt')
          else:
            f = open(fullpath)

          if f is not None:
            new_data = LogData(mtime)
            date = date_from_name(shortname)
            if date is None:
              date = datetime.date.today()
            new_data.text = self.log_parser.parse_log(f, date, new_data.details, new_data.players)
            self.logs[shortname] = new_data

    # Collapse the data into the current data
    self.clear()
    for shortname, log_object in self.logs.items():
      self.collapse(log_object)
      
    self.locked = False