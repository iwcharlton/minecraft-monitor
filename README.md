# The Minecraft Monitor

The minecraft-monitor was created as a small, lightweight web-app that I could
run alongside my Minecraft Server to give me basic visibility and control over
the everyday things so I wouldn't have to ssh onto my server all the time to
start it, stop it, update settings, add people onto the whitelist and so on.

It's not meant to be sophisticated or pretty, just functional.

## Installing

Installation is not 100% necessary to use the monitor as a command line script.

Installation as a package can be done with standard setup, using:

```
python setup.py install
```

## Running as a Script

From the command line, run:

```
.\minecraft_monitor\minecraft_monitor.py --config .\path\to\config.json
```

For servers that have been running a long time, startup can take a long time,
due to the number of log files to parse. to reduce this time (e.g. for dev),
use the `--log-limit` argument, and provide a maximum number of log files to
parse.

## Managing Users

A _very simple_, user management system has been put in place, to provide user
definitions in the `config.json` file as follows:

```
{
  "users": {
    "0001": {
      "name": "My Name",
      "email": "me@myself.i",
      "password": "sha256$generated-password-hash"
    }
  }
}
```

In order to create users, use the `user.py` script as follows:

```
user.py ---name "My Name" --email me@myself.i --pwd MyP@ssw0rd!
```

This will output a user JSON snippet that you can then add to your config file
against `"users"` and an ID you have picked, e.g. `"0001"`. Restart the server
with the updated config file and you will then be able to login with
`MyP@ssw0rd!`.

## Using in Other Scripts

To use in other scripts:

```
import minecraft_monitor

config = {}
# Requires the config to be populated as in example_config.json

# Use an additional log_limit argument if required
minecraft_monitor.create_app(config)
```

## Customisation

The monitor is intended to be pretty basic, however there is some customisation
of the log parsing. [logparse-config.json](logparse-config.json) can be updated
to parse the log lines in different ways by adjusting or entering new entries
in the `server-events` and `player-events` lists.
