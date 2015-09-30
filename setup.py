from setuptools import setup, find_packages

setup(
    name='slackrobot',
    version='0.1.3',
    description='Simple python implementation of slack bot',
    url='https://github.com/traveloka/python-slackrobot',
    author='Ricky Winata',
    author_email='ricky.w12@gmail.com',
    license='MIT',
    keywords='slack bot robot',
    install_requires=['slackclient'],
    packages=['slackrobot', 'slackrobot.utils'],
)
