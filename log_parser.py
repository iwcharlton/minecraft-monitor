#!/usr/bin/env python
import ast
import datetime
import gzip
import json
import os
import re

# Utility for getting a datetime.date object from a log name
date_re = re.compile("([0-9]{4})-([0-9]{2})-([0-9]{2})-(.*)")
def date_from_name(name):
  regex_result = date_re.split(name)
  if regex_result is not None and len(regex_result) > 1:
    date = datetime.date(int(regex_result[1]), int(regex_result[2]), int(regex_result[3]))
    return date
  return None


# Utility for general log lines of the form
# [hh:mm:ss] [{thread}/{level}]: {additional user regex}
def compile_log_line_re(re_extra):
  if re_extra is None:
    return re.compile("\[([0-2][0-9])\:([0-9]{2})\:([0-9]{2})\] \[(.*)/(.*)\]\: (.*)")
  else:
    return re.compile("\[([0-2][0-9])\:([0-9]{2})\:([0-9]{2})\] \[(.*)/(.*)\]\: " + re_extra)

# Utility for parsing a log line and return a time, plus extra regex matches
# returns time, ( further matches )
def parse_log_line(regex, line):
  regex_result = regex.split(line)
  if regex_result is not None and len(regex_result) > 1:
    time = datetime.time(int(regex_result[1]), int(regex_result[2]), int(regex_result[3]))
    thread = regex_result[4]
    level = regex_result[5]
    extra = regex_result[6:]
    return time, extra
  else:
    return None, None

class LogParser():
  def __init__(self, server_log_events, player_log_events):
    self.server_log_events = server_log_events
    self.player_log_events = player_log_events

    # Build the regular expressions
    for name, event in self.server_log_events.items():
      if 'regex' in event:
        event['re'] = compile_log_line_re(event['regex'])
    for name, event in self.player_log_events.items():
      if 'regex' in event:
        event['re'] = compile_log_line_re(event['regex'])

  # Parse a single log line and interpret the data into the server details
  # and player structure
  def visit_log_line(self, line, date, server_details, players):
    # Server events
    for key, server_event in self.server_log_events.items():
      time, extra = parse_log_line(server_event['re'], line)
      if time is not None:
        if "assign" in server_event:
          for key, val in server_event['assign'].items():
            server_details[key] = str(extra[val])
        if "assign-time" in server_event:
          for key in server_event['assign-time']:
            server_details[key] = datetime.datetime.combine(date, time)
        if "increment" in server_event:
          for key in server_event['increment']:
            if key not in server_details:
              server_details[key] = 0
            server_details[key] = server_details[key] + 1

    # Player events
    for key, player_event in self.player_log_events.items():
      time, extra = parse_log_line(player_event['re'], line)
      if time is not None:
        player = extra[player_event['player']]
        if player not in players:
          players[player] = {}
        if "assign-time" in player_event:
          for key in player_event['assign-time']:
            players[player][key] = datetime.datetime.combine(date, time)
        if "increment" in player_event:
          for key in player_event['increment']:
            if key not in players[player]:
              players[player][key] = 0
            players[player][key] = players[player][key] + 1
  
  # Parse a log (iterable object)
  # Assign details to server_details and player objects
  # returns the log as an array of lines
  def parse_log(self, log, date, server_details, players):
    log_text = ''
    for line in log:
      log_text = log_text + line
      self.visit_log_line(line, date, server_details, players)

    return log_text