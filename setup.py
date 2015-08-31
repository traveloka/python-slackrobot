from setuptools import setup, find_packages

setup(
    name='slackbot',
    version='0.1.0',
    description='Simple Python implementation of Slack Bot',
    url='',
    author='Ricky Winata',
    author_email='ricky.w12@gmail.com',
    license='MIT',
    keywords='slack bot',
    install_requires=['slackclient'],
    packages=['slackbot', 'slackbot.utils'],
)
