import os.path
import json

from glob import glob
from zipfile import ZipFile
from urllib.parse import urljoin
from pkg_resources import parse_requirements

import requests

from fac.files import JSONFile
from fac.utils import JSONDict
from fac.api import AuthError


class ModManager:
    'Provides access to the factorio mods directory'

    def __init__(self, config, api):
        self.api = api
        self.config = config
        self.mods_json = JSONFile(
            os.path.join(
                self.config.mods_path,
                'mod-list.json'
            )
        )

    def get_mod_json(self, name):
        for mod in self.mods_json.mods:
            if mod.name == name:
                return mod

    def get_mod_info(self, name):
        for mod in self.get_installed_mods():
            if mod.name == name:
                return mod

    def get_mod_files(self, name=None, version=None):
        name = name or '*'
        version = version or '*'

        return glob(
            os.path.join(
                self.config.mods_path,
                '%s_%s.zip' % (name, version)
            )
        )

    def resolve_remote_requirement(self, req):
        if isinstance(req, str):
            req = list(parse_requirements(req))[0]
        spec = req.specifier
        game_ver = self.config.game_version_major

        mod = self.api.get(req.name)

        return [release for release in mod.releases
                if release.version in spec and
                release.game_version == game_ver]

    def resolve_local_requirement(self, req):
        if isinstance(req, str):
            req = list(parse_requirements(req))[0]
        spec = req.specifier
        game_ver = self.config.game_version_major

        return [info for info in self.get_installed_mods(req.name)
                if info.version in spec and
                info.factorio_version == game_ver]

    def get_installed_mods(self, name=None, version=None):
        zips = self.get_mod_files(name, version)

        for zipname in zips:
            basename = os.path.splitext(
                os.path.basename(zipname)
            )[0]

            with ZipFile(zipname) as f:
                info = json.loads(
                    f.read(
                        '%s/info.json' % basename,
                    ).decode('utf-8'),
                )
                yield JSONDict(info)

    def is_mod_enabled(self, name):
        mod = self.get_mod_json(name)
        if mod:
            return mod.enabled != 'false'
        else:
            return True  # by default, new mods are automatically enabled

    def set_mod_enabled(self, name, enabled=True):
        mod = self.get_mod_json(name)
        if not mod:
            mod = {'enabled': '', 'name': name}
            self.mods_json.mods.append(mod)

        if enabled != mod.enabled:
            mod.enabled = 'true' if enabled else 'false'
            self.mods_json.save()
            return True
        else:
            return False

    def require_login(self):
        import getpass
        import sys
        player_data = self.config.player_data
        username = player_data.get('service-username')
        token = player_data.get('service-token')

        if not (username and token):
            print('You need a Factorio account to download mods.')
            print('Please provide your username and password to authenticate '
                  'yourself.')
            print('Your username and token (NOT your password) will be stored '
                  'so that you only have to enter it once')
            print('This uses the exact same method used by Factorio itself')
            print()
            while True:
                if username:
                    print('Username [%s]:' % username, end=' ', flush=True)
                else:
                    print('Username:', end=' ', flush=True)

                input_username = sys.stdin.readline().strip()

                if input_username:
                    username = input_username
                elif not username:
                    continue

                password = getpass.getpass('Password (not shown):')
                if not password:
                    continue

                try:
                    token = self.api.login(username, password)
                except AuthError as ex:
                    print('Authentication error: %s.' % ex)
                except Exception as ex:
                    print('Error: %s.' % ex)
                else:
                    print('Logged in successfully.')
                    break
                print()
            player_data['service-token'] = token
            player_data['service-username'] = username
            player_data.save()
        return player_data

    def install_mod(self, release, enable=None):
        file_name = release.file_name
        mod_name = release.info_json.name

        assert '/' not in file_name
        assert '\\' not in file_name
        assert file_name.endswith('.zip')

        player_data = self.require_login()
        url = urljoin(self.api.base_url, release.download_url)

        print('Downloading: %s...' % url)

        req = requests.get(
            url,
            params={
                'username': player_data['service-username'],
                'token': player_data['service-token']
            }
        )
        data = req.content

        if len(data) != release.file_size:
            raise Exception(
                'Downloaded file has incorrect size (%d), expected %d.' % (
                    len(data), release.file_size
                )
            )

        file_path = os.path.join(self.config.mods_path, file_name)

        with open(file_path, 'wb') as f:
            f.write(data)

        if enable is not None:
            self.set_mod_enabled(mod_name, enable)

        for mod in self.get_installed_mods():
            if mod.name != mod_name or mod.version == release.version:
                continue
            self.uninstall_mod(mod.name, mod.version)

    def uninstall_mod(self, name, version=None):
        files_to_remove = self.get_mod_files(name=name, version=version)

        for file in files_to_remove:
            print('Removing: %s' % file)
            os.remove(file)

        return files_to_remove
