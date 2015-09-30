"""
slack-robot, simple slack bot implementation
"""
import json
import logging
import re
import time
import slackrobot.utils.plugins
from ssl import SSLError
from collections import OrderedDict
from slackclient import SlackClient
from slackclient._client import SlackNotConnected
from slackrobot.utils.thread import ThreadPoolExecutor as Pool

class SlackRobot(object):
    """SlackRobot implementation

    Public attributes:
    - slack_client: for accessing slack api (SlackClient)
    - bot_id: bot id in slack, exist when bot connected to slack (string)
    - bot_name: bot name in slack, exist when bot connected to slack (string)
    - plugin_dirs: plugins directory
    """

    def __init__(self, token, plugins_dir='./plugins', max_workers=8):
        self.bot_id = None
        self.bot_name = None
        self.last_ping = 0
        self.plugins_dir = plugins_dir
        self.cron_plugins = []
        self.plugins = []
        self.slack_client = SlackClient(token)
        self.executor = Pool(max_workers=max_workers)
        self.load_plugins()

    def load_plugins(self):
        """Load plugins (normal & cron)"""
        # load cron plugins
        cron_loader = slackrobot.utils.plugins.CronPluginLoader(
            'cron_job', 'cron_interval', self.plugins_dir
        )
        for cron_plugin in cron_loader.all():
            self.cron_plugins.append(cron_plugin)

        # load normal plugins
        loader = slackrobot.utils.plugins.PluginLoader(
            'process_message', self.plugins_dir
        )
        for plugin in loader.all():
            self.plugins.append(plugin)

    def connect(self):
        """Connect to slack server"""
        logging.info('Trying to connect with Slack...')
        self.slack_client.rtm_connect()
        self.bot_id = self.slack_client.server.login_data['self']['id']
        self.bot_name = self.slack_client.server.login_data['self']['name']
        logging.info('Connected with bot name @%s', self.bot_name)

    def start(self):
        """Start the bot"""
        self.connect()
        while True:
            self.try_read_input()
            self.crons()
            self.autoping()
            time.sleep(.1)

    def try_read_input(self):
        """Try to read inputs from rtm channel"""
        try:
            for reply in self.slack_client.rtm_read():
                self.input(reply)
        except SlackNotConnected:
            logging.warning('Slack is not connected.')
        except SSLError, exception:
            logging.warning('SSL Error: %s', exception)

    def autoping(self):
        """Ping slack server, to ensure it's connected"""
        now = int(time.time())
        if now > self.last_ping + 3:
            self.slack_client.server.ping()
            self.last_ping = now

    def input(self, event):
        """Handle incoming event to bot
        only handle event with type message

        Args:
            event: event sent by slack when something happens.
                for more information about the structure: https://api.slack.com/rtm
        """
        if "type" in event and not "subtype" in event and event['type'] == 'message':
            # handle message only if the message mentions the bot or
            # the channel is a direct message to the bot and
            # don't handle the message coming from the bot itself
            if ((event['text'].find('<@{}>'.format(self.bot_id)) != -1 or
                 event['channel'].startswith('D')) and
                    event['user'] != self.bot_id):
                # remove mention (@bot_name) from message
                event['text'] = re.match(r'(<@.+>:?\s?)?(.+)', event['text']).group(2)
                for plugin in self.plugins:
                    self.executor.submit(plugin.do_job, self, event)

    def crons(self):
        """Run cron plugins job"""
        for cron_plugin in self.cron_plugins:
            if cron_plugin.interval + cron_plugin.last_run <= time.time():
                cron_plugin.last_run = time.time()
                self.executor.submit(cron_plugin.do_job, self)

    def send_message(self, text, channel, attachments=None):
        """Send text message to slack channel

        Args:
            text: the text to be sent (string)
            channel: what channel should the text be sent (string, ex: #test, #abc)
            attachments: https://api.slack.com/docs/attachments

        Return:
            the message response returned by slack api.
            for more information https://api.slack.com/methods/chat.postMessage
        """
        attachments = attachments or []
        send_data = {
            'text': text,
            'channel': channel,
            'attachments': json.dumps(attachments),
            'as_user': True}
        logging.info('Send message %s ...', send_data)
        message = json.loads(self.slack_client.api_call('chat.postMessage', **send_data))
        if not message['ok']:
            logging.info('send_message failed: ' + message['error'])
        return message

    def update_message(self, text, message):
        """Update text message in sent message
        Update only if the message['ok'] is True

        Args:
            text: updated text (string)
            message: the message that want to be changed, got from method send_message
                for more information: https://api.slack.com/methods/chat.postMessage

        Return:
            the message response returned by slack api.
            for more information: https://api.slack.com/methods/chat.postMessage
        """
        update_data = {
            'text': text,
            'ts': message['ts'],
            'channel': message['channel']}
        logging.info('Update message %s ...', update_data)
        new_message = json.loads(self.slack_client.api_call('chat.update', **update_data))
        if not new_message['ok']:
            logging.info('update_message failed: %s', message['error'])
        return new_message

