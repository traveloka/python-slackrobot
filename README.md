# python-slackbot
Simple python implementation of slack bot.

## Install
```Python
pip install slackrobot
```

## Usage
```Python
TOKEN = "YOUR BOT TOKEN HERE"

# default, the plugins directory is in your current directory
slackbot = SlackRobot(TOKEN)
slackbot.start()

# set plugins directory to your app directory
import os
slackbot = SlackRobot(TOKEN, plugins_directory=os.path.join(os.path.dirname(__file__), 'plugins'))
slackbot.start()
```

## Plugins
You need to add your plugins into your plugins directory. (see the example in this repo)
There are 2 types of plugin: normal & cron.

For a **normal plugin**, you need to have function `process_message(bot, message)` in your plugin file to process the message. Every message the bot receives will be spread to all plugins. 
```Python
# example 1
def process_message(bot, message):
  bot.send_message('Hello World', '#channel')
```

```Python
# example 2
import re 
def process_message(bot, message):
  match = re.match(r'hello', message['text'])
  if  not match:
    return
  bot.send_message('World', message['channel'])
```

```Python
# reference for message: https://api.slack.com/events/message
simple_message = {
    "type": "message",
    "channel": "C2147483705",
    "user": "U2147483697",
    "text": "Hello world",
    "ts": "1355517523.000005"
}
```

For a **cron plugin** you need to have variable `cron_interval` and function `cron_job(bot)` in your plugin file. Every `cron_interval` secs, the `cron_job` will be run.
```Python
# bot will send 'Hello' to channel '#channel' every 30 secs

cron_interval = 30 # in secs
def cron_job(bot):
  bot.send_message('Hello', '#channel')
```

## License
MIT
