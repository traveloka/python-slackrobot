"""
plugin utils for slack-robot
"""
import imp
import glob
import os
import sys

class Plugin(object): #pylint: disable-msg=R0903
    """Represents normal plugin"""
    def __init__(self, func):
        self.func = func

    def do_job(self, *args, **kwargs):
        """run the job"""
        self.func(*args, **kwargs)

class CronPlugin(object): #pylint: disable-msg=R0903
    """Represents cron plugin"""
    def __init__(self, func, interval):
        self.func = func
        self.interval = interval
        self.last_run = 0

    def do_job(self, *args, **kwargs):
        """run the job"""
        self.func(*args, **kwargs)

# Plugin loader
class PluginLoader(object): #pylint: disable-msg=R0903
    """
    A loader for loading normal plugins to slack bot
    """
    def __init__(self, func_name, plugins_dir):
        self.func_name = func_name
        self.plugins_dir = plugins_dir
        sys.path.append(self.plugins_dir)

    def all(self):
        """Get all normal plugins

        Returns:
            generator of all normal plugins
        """

        for path in glob.glob(self.plugins_dir+'/*.py'):
            name, _ = os.path.splitext(os.path.basename(path))
            if name.startswith('__'):
                continue
            module = imp.load_source(name, path)
            if self.func_name in dir(module):
                yield Plugin(getattr(module, self.func_name))

# Cron Plugin Loader
class CronPluginLoader(PluginLoader): #pylint: disable-msg=R0903
    """
    A loader for loading all cron plugins to slack bot
    """
    def __init__(self, func_name, interval_name, plugins_dir):
        super(CronPluginLoader, self).__init__(func_name, plugins_dir)
        self.interval_name = interval_name

    def all(self):
        """Get all cron plugins

        Returns:
            generator of cron plugins
        """
        for path in glob.glob(self.plugins_dir+'/*.py'):
            name, _ = os.path.splitext(os.path.basename(path))
            if name.startswith('__'):
                continue
            module = imp.load_source(name, path)
            if self.func_name in dir(module) and self.interval_name in dir(module):
                yield CronPlugin(getattr(module, self.func_name),
                                 getattr(module, self.interval_name))

