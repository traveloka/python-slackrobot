"""
Tests for SlackRobot
"""
import mock
from unittest import TestCase, main
from slackrobot import SlackRobot
from slackrobot.utils.plugins import Plugin

def dummy_job(bot, data):   # pylint: disable=unused-argument
    """Just a dummy job used for testing"""
    print 'dummy!'

class SlackRobotTest(TestCase):
    """Class Test for SlackRobot"""

    def setUp(self):
        self.init_slackrobot()

    def init_slackrobot(self):
        """Init slack robot used by test methods"""
        self.slackrobot = SlackRobot('abcd')
        self.slackrobot.bot_name = 'bot'
        self.slackrobot.bot_id = 42
        self.slackrobot.executor = mock.MagicMock()
        self.slackrobot.plugins = [Plugin(dummy_job)]

    def test_not_message_input(self):
        """Test with wrong input message"""
        self.slackrobot.input({
            'type': 'ping'
        })
        self.assertFalse(self.slackrobot.executor.submit.called, 'Failed to not submit job')

    def test_correct_message_input(self):
        """Test with correct input message"""
        self.slackrobot.input({
            'type': 'message',
            'text': 'hello world',
            'user': 'U12345',
            'channel': 'D12345'
        })
        self.assertTrue(self.slackrobot.executor.submit.called, 'Failed to submit job')

    def test_not_direct_channel(self):
        """Test with not direct channel"""
        self.slackrobot.input({
            'type': 'message',
            'text': 'not direct channel',
            'user': 'U12345',
            'channel': 'C12345'
        })
        self.assertFalse(self.slackrobot.executor.submit.called, 'Failed to not submit job')

    def test_mention_bot(self):
        """Test by mentioning bot in not direct channel"""
        self.slackrobot.input({
            'type': 'message',
            'text': '<@42>hello',
            'user': 'U12345',
            'channel': 'C12345'
        })
        self.assertTrue(self.slackrobot.executor.submit.called, 'Failed to submit job')


if __name__ == '__main__':
    main()
