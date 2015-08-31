import json
import logging
import re
import time
import slackrobot.utils.plugins
from collections import OrderedDict
from slackclient import SlackClient
from slackrobot.utils.thread import ThreadPoolExecutor as Pool

class SlackRobot(object):
    def __init__(self, token, max_workers=8):
        self.bot_id = None
        self.bot_name = None
        self.last_ping = 0
        self.cron_plugins = []
        self.plugins = []
        self._load_plugins()
        self._slack_client = SlackClient(token)
        self._executor = Pool(max_workers=max_workers)
    
    def _load_plugins(self):
        # load cron plugins
        for cron_plugin in slackrobot.utils.plugins.cron_loader.all():
            self.cron_plugins.append(cron_plugin)
        # load plugins
        for plugin in slackrobot.utils.plugins.loader.all():
            self.plugins.append(plugin) 
 
    def connect(self):
        logging.info('Trying to connect with Slack...')
        self._slack_client.rtm_connect()
        self.bot_id = self._slack_client.server.login_data['self']['id']
        self.bot_name = self._slack_client.server.login_data['self']['name']
        logging.info('Connected with bot name @{}'.format(self.bot_name))

    def start(self):
        self.connect()
        while True:
            for reply in self._slack_client.rtm_read():
                self.input(reply)
            self.crons()
            self.autoping()
            time.sleep(.1)
    
    def autoping(self):
        now = int(time.time())
        if now > self.last_ping + 3:
            self._slack_client.server.ping()
            self.last_ping = now
    
    def input(self, data):
        # handle incoming messages
        # handle only message type
        if "type" in data and not "subtype" in data and data['type'] == 'message':            
            # handle message only if the message mentions the bot or
            # the channel is a direct message to the bot and
            # don't handle messages that come from the bot itself
            if ((data['text'].find('<@{}>'.format(self.bot_id)) != -1 or 
                data['channel'].startswith('D')) and
                data['user'] != self.bot_id):
                # remove mention from message, get only the command
                data['text'] = re.match('(<@.+>:?\s?)?(.+)', data['text']).group(2)
                logging.info('got {}'.format(data))
                for plugin in self.plugins: 
                    self._executor.submit(plugin.do_job, self, data)

    def crons(self):
        for cron_plugin in self.cron_plugins:
            if cron_plugin.interval + cron_plugin.last_run <= time.time():
                cron_plugin.last_run = time.time()
                self._executor.submit(cron_plugin.do_job, self)
    
    def send_message(self, text, channel, attachments=[]):
        send_data = {
            'text': text,
            'channel': channel,
            'attachments': json.dumps(attachments),
            'as_user': True }
        logging.info('Send message {} ...'.format(send_data))
        message = json.loads(self._slack_client.api_call('chat.postMessage', **send_data))
        if not message['ok']:
            logging.info('send_message failed: ' + message['error'])
        return message

    def update_message(self, text, message):
       if message['ok']:
            update_data = {
                'text': text,
                'ts': message['ts'],
                'channel': message['channel'] }
            logging.info('Update message {} ...'.format(update_data))
            new_message = json.loads(self._slack_client.api_call('chat.update', **update_data))
            if not new_message['ok']:
                logging.info('update_message failed: ' + message['error'])
            return new_message
