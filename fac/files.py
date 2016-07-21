import os
import sys
import json

from configparser import ConfigParser

from appdirs import user_config_dir, user_data_dir

from fac.utils import JSONDict

__all__ = ['Config', 'JSONFile']

FACTORIO_SEARCH_PATHS = [
    '.',
    os.path.join('.', 'factorio'),
    '..',
    os.path.join('..', 'factorio'),
    user_data_dir('factorio', appauthor=False),
    os.path.join(
        user_data_dir('Steam', appauthor=False),
        os.path.join('SteamApps', 'common', 'Factorio'),
    ),
]

if sys.platform.startswith('win32'):
    FACTORIO_SEARCH_PATHS += [
        r'%APPDATA%\factorio',
        r'C:\Program Files (x86)\Steam\SteamApps\common\factorio',
    ]
elif sys.platform.startswith('linux'):
    FACTORIO_SEARCH_PATHS += [
        '~/factorio',
        '~/.factorio',
        '/usr/share/factorio/',
    ]
else:
    FACTORIO_SEARCH_PATHS += [
        '~/factorio',
        '/Applications/factorio.app/Contents',
    ]


class Config(ConfigParser):
    default_config = '''
    [mods]
    hold =

    [paths]
    data-path =
    write-path =
    '''

    def __init__(self, config_file=None):
        super().__init__(allow_no_value=True)

        self.read_string(self.default_config)

        if config_file:
            self.config_file = config_file
        else:
            self.config_file = os.path.join(
                user_config_dir('fac', appauthor=False),
                'config.ini'
            )

        try:
            self.read(self.config_file)
        except IOError:
            pass

    def save(self):
        dirname = os.path.dirname(self.config_file)

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.write(f)

    @staticmethod
    def is_factorio_data_path(path):
        return os.path.isfile(os.path.join(path, 'base', 'info.json'))

    @staticmethod
    def is_factorio_write_path(path):
        config_dir = os.path.join(path, 'config')
        mods_dir = os.path.join(path, 'mods')
        if not (os.path.isdir(config_dir) and
                os.path.isdir(mods_dir)):
            return False

        if not (os.access(config_dir, os.W_OK) and
                os.access(mods_dir, os.W_OK)):
            return False
        return True

    @property
    def factorio_data_path(self):
        path = self.get('paths', 'data-path')
        if path and not self.is_factorio_data_path(path):
            raise Exception(
                'Factorio data path does not seem to be correct'
                )
        elif not path:
            for path in FACTORIO_SEARCH_PATHS:
                path = os.path.expanduser(path)
                path = os.path.expandvars(path)
                if self.is_factorio_data_path(path):
                    return path
                path = os.path.join(path, 'data')
                if self.is_factorio_data_path(path):
                    return path
        raise Exception(
            'Can not find the factorio data path.\n'
            'Please set the data-path variable in %s' % (
                self.config_file
            )
        )

    @property
    def factorio_write_path(self):
        path = self.get('paths', 'write-path')
        if path and not self.is_factorio_write_path(path):
            raise Exception(
                'Factorio writable path does not seem to be correct'
            )
        elif not path:
            for path in FACTORIO_SEARCH_PATHS:
                path = os.path.expanduser(path)
                path = os.path.expandvars(path)
                if self.is_factorio_write_path(path):
                    return path
        raise Exception(
            'Can not find the factorio write path.\n'
            'Please set the write-path variable in %s' % (
                self.config_file
            )
        )

    @property
    def player_data(self):
        return JSONFile(
            os.path.join(
                self.factorio_write_path,
                'player-data.json'
            )
        )

    @property
    def game_version(self):
        json_file = os.path.join(
            self.factorio_data_path,
            'base', 'info.json'
        )
        json = JSONFile(json_file)
        return json.version

    @property
    def game_version_major(self):
        return '.'.join(self.game_version.split('.')[:2])

    @property
    def mods_path(self):
        return os.path.join(self.factorio_write_path, 'mods')

    def get_hold(self):
        return self.get('mods', 'hold').split()

    def set_hold(self, value):
        self.set('mods', 'hold', '\n'.join(value))

    hold = property(get_hold, set_hold)


class JSONFile(JSONDict):
    file = None

    def __init__(self, file):
        self.file = file
        self.reload()

    def __enter__(self):
        return self

    def __exit__(self):
        self.save()

    def reload(self):
        with open(self.file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def save(self):
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)
