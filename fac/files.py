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
        self.hold = []
        self.forced_game_version = None
        self.forced_mods_directory = None

        if config_file:
            self.config_file = config_file
        else:
            self.config_file = os.path.join(
                user_config_dir('fac', appauthor=False),
                'config.ini'
            )

        if os.path.isfile(self.config_file):
            self.load()

    def load(self):
        self.read(self.config_file)
        self.hold = self.get('mods', 'hold').split()

    def save(self):
        dirname = os.path.dirname(self.config_file)

        hold = '\n'.join(self.hold)
        self.set('mods', 'hold', hold)

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

        if path and self.is_factorio_data_path(path):
            return path
        elif path:
            raise Exception(
                'The supplied data path (%s) does not seem to be correct.\n'
                'Please check the data-path variable in %s and make sure it '
                'points to a data directory containing a base/info.json file.'
                % (path, self.config_file)
            )
        else:
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

        if path and self.is_factorio_write_path(path):
            return path
        elif path:
            raise Exception(
                'The supplied write path (%s) does not seem to be correct.\n'
                'Please check the write-path variable in %s and make sure it '
                "points to a directory containing writeable 'config' and "
                "'mods' subdirectories." % (
                    path,
                    self.config_file,
                )
            )
        else:
            for path in FACTORIO_SEARCH_PATHS:
                path = os.path.expanduser(path)
                path = os.path.expandvars(path)
                if self.is_factorio_write_path(path):
                    return path

        raise Exception(
            'Can not find a valid factorio write path.\n'
            'Please set one using the write-path variable in %s' % (
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

    def get_game_version(self):
        if self.forced_game_version:
            return self.forced_game_version

        json_file = os.path.join(
            self.factorio_data_path,
            'base', 'info.json'
        )
        json = JSONFile(json_file)
        return json.version

    def set_game_version(self, version):
        self.forced_game_version = version

    game_version = property(get_game_version, set_game_version)

    @property
    def game_version_major(self):
        return '.'.join(self.game_version.split('.')[:2])

    def get_mods_directory(self):
        if self.forced_mods_directory:
            return self.forced_mods_directory
        return os.path.join(self.factorio_write_path, 'mods')

    def set_mods_directory(self, directory):
        self.forced_mods_directory = directory

    mods_directory = property(get_mods_directory, set_mods_directory)


class JSONFile(JSONDict):
    file = None

    def __init__(self, file):
        self.file = file
        self.data = {}
        self.reload()

    def __enter__(self):
        return self

    def __exit__(self):
        self.save()

    def reload(self):
        if not os.path.exists(self.file):
            return

        with open(self.file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def save(self):
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)
