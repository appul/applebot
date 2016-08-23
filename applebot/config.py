import json
import logging
import os
import sys

log = logging.getLogger(__name__)


class Config(object):
    def __init__(self, config=None):
        if config:
            self.load(config)

    def sub(self, name, config_type=None, default_value=None):
        """Create a subconfig from the config, for nested configs."""
        config_type = config_type or self.__class__
        self.__dict__[name] = config_type(self.__dict__.get(name, default_value))
        return self.__dict__[name]

    def update(self, config):
        """Update config dict with new values."""
        self.__dict__.update(config)

    def load(self, config):
        """Load a config from a file, dict or other Config."""
        if isinstance(config, str):
            return self.load_file(config)
        elif isinstance(config, dict):
            return self.update(config)
        elif isinstance(config, Config):
            return self.update(config.__dict__)
        raise TypeError('Parameter \'config\' must be of type str, dict or Config')

    def load_file(self, config):
        """Load a config from a file."""
        path, folder, file = self._find_config(config)
        if not path:
            raise FileNotFoundError('Could not find config file: {}'.format(config))
        with open(path, 'r') as data:
            try:
                log.info('Loading config from: {}'.format(file))
                self.update(json.load(data))
            except json.decoder.JSONDecodeError as e:
                raise Exception('Could not load config file: {}'.format(e))

    @staticmethod
    def _find_config(config):
        main_dir = os.path.dirname(os.path.realpath(sys.modules['__main__'].__file__))
        cnfg_dir = os.path.join(main_dir, 'config')
        user_dir = os.path.expanduser('~')

        def search_paths():
            yield '', config
            for dir_ in [main_dir, cnfg_dir, user_dir]:
                for name_ in ['{}.applebot', '{}.config', '{}.json', '{}.config.json']:
                    yield dir_, name_.format(config)

        for folder, file in search_paths():
            path = os.path.join(folder, file)
            if os.path.isfile(path):
                return path, folder, file
