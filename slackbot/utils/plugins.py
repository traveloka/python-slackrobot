import imp
import glob
import sys
import os
import time

class Plugin(object):
    def __init__(self, func):
        self.func = func
    
    def do_job(self, *args, **kwargs):
        self.func(*args, **kwargs)

class CronPlugin(object):
    def __init__(self, func, interval):
        self.func = func
        self.interval = interval
        self.last_run = 0
    
    def do_job(self, *args, **kwargs):
        self.func(*args, **kwargs)

# Plugin loader
class PluginLoader(object):
    def __init__(self, func_name, plugins_path):
        self.func_name = func_name
        self.plugins_path = plugins_path
        sys.path.append(self.plugins_path)
          
    def all(self):
        for path in glob.glob(self.plugins_path+'/*.py'):
            name, ext = os.path.splitext(os.path.basename(path))
            if name.startswith('__'):
                continue
            module = imp.load_source(name, path)
            if self.func_name in dir(module):
                yield Plugin(getattr(module, self.func_name))

# Cron Plugin Loader
class CronPluginLoader(PluginLoader):
    def __init__(self, func_name, interval_name, plugins_path):
        self.func_name = func_name
        self.interval_name = interval_name
        self.plugins_path = plugins_path
        sys.path.append(self.plugins_path)

    def all(self):
        for path in glob.glob(self.plugins_path+'/*.py'):
            name, ext = os.path.splitext(os.path.basename(path))
            if name.startswith('__'):
                continue
            module = imp.load_source(name, path)
            if self.func_name in dir(module) and self.interval_name in dir(module):
                yield CronPlugin(getattr(module, self.func_name),
                                 getattr(module, self.interval_name))

loader = PluginLoader(
    'process_message',
    './plugins'
)

cron_loader = CronPluginLoader(
    'cron_job',
    'cron_interval',
    './plugins'
)
