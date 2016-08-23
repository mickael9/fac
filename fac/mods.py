import os.path
import shutil
import json
from pathlib import Path

from glob import glob
from zipfile import ZipFile
from urllib.parse import urljoin

import requests

from fac.files import JSONFile
from fac.utils import JSONDict
from fac.api import AuthError, ModNotFoundError


class Mod:
    location = None

    def __init__(self, manager, location):
        self.manager = manager
        self.location = location

    def get_enabled(self):
        return self.manager.is_mod_enabled(self.name)

    def set_enabled(self, val):
        self.manager.set_mod_enabled(self.name, val)

    enabled = property(get_enabled, set_enabled)

    @property
    def name(self):
        return self.info.name

    @property
    def version(self):
        return self.info.version

    def _check_valid(self):
        expected_basename = "%s_%s" % (self.name, self.version)

        assert self.basename == expected_basename, \
            "Invalid file name %s, expected %s" % (
                    self.basename,
                    expected_basename
            )

    @classmethod
    def _find(cls, pattern, manager, name, version):
        name = name or '*'
        version = version or '*'

        files = glob(
            os.path.join(
                manager.config.mods_path,
                pattern % (name, version)
            )
        )
        for file in files:
            try:
                mod = cls(manager, file)
                yield mod
            except Exception as ex:
                print('Warning: invalid mod %s: %s' % (file, ex))


class ZippedMod(Mod):
    """
    A zipped mod consists of a strictly named name_version.zip file.

    The top-level directory of the first zip entry must
    contain the info.json file and other mod files.

    Any subsequent top-level directories will be ignored.
    """

    packed = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.basename = os.path.splitext(
                os.path.basename(
                    self.location
                )
        )[0]
        self._read_info()
        self._check_valid()

    def remove(self):
        print('Removing file: %s' % self.location)
        os.remove(self.location)

    def _read_info(self):
        with ZipFile(self.location) as f:
            first_entry = f.namelist()[0]
            self.toplevel = first_entry.split('/')[0]

            if not self.toplevel:
                raise Exception('Could not find a top-level directory')

            info = json.loads(
                f.read(
                    '%s/info.json' % self.toplevel,
                ).decode('utf-8'),
            )

            self.info = JSONDict(info)

    def unpack(self):
        mod_directory = self.manager.config.mods_path
        unpacked_location = os.path.join(mod_directory, self.basename)

        print('Unpacking: %s' % self.location)

        with ZipFile(self.location) as f:
            os.makedirs(unpacked_location)

            for arcname in f.namelist():
                if not arcname.startswith(self.toplevel + '/'):
                    print("Warning: out-of-place file %s ignored" % (
                        arcname))
                    continue

                dest = arcname[len(self.toplevel) + 1:]
                dest = self._sanitize_arcname(dest)
                dest = os.path.join(unpacked_location, dest)
                self._extract_member(f, arcname, dest)

        self.remove()
        return UnpackedMod(self.manager, unpacked_location)

    def _sanitize_arcname(self, arcname):
        arcname = arcname.replace('/', os.path.sep)

        if os.path.altsep:
            arcname = arcname.replace(os.path.altsep, os.path.sep)
        # interpret absolute pathname as relative, remove drive letter or
        # UNC path, redundant separators, "." and ".." components.
        arcname = os.path.splitdrive(arcname)[1]
        invalid_path_parts = ('', os.path.curdir, os.path.pardir)
        arcname = os.path.sep.join(x for x in arcname.split(os.path.sep)
                                   if x not in invalid_path_parts)
        if os.path.sep == '\\':
            # filter illegal characters on Windows
            arcname = ZipFile._sanitize_windows_name(arcname, os.path.sep)

        return arcname

    def _extract_member(self, zipfile, arcname, dest):
        # Create all upper directories if necessary.
        upperdirs = os.path.dirname(dest)
        if upperdirs and not os.path.exists(upperdirs):
            os.makedirs(upperdirs)

        if arcname[-1] == '/':
            if not os.path.isdir(dest):
                os.mkdir(dest)
            return

        with zipfile.open(arcname) as source, \
                open(dest, "wb") as target:
            shutil.copyfileobj(source, target)

    @classmethod
    def find(cls, *args, **kwargs):
        return cls._find("%s_%s.zip", *args, **kwargs)


class UnpackedMod(Mod):
    packed = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.basename = os.path.basename(
            os.path.realpath(
                self.location
            )
        )
        self._read_info()
        self._check_valid()

    def remove(self):
        print('Removing directory: %s' % self.location)
        shutil.rmtree(self.location)

    def _read_info(self):
        path = os.path.join(self.location, 'info.json')
        self.info = JSONFile(path)

    def pack(self):
        packed_location = os.path.join(
            self.manager.config.mods_path,
            self.basename + '.zip'
        )

        print('Packing: %s' % self.location)

        if os.path.exists(packed_location):
            raise Exception("File already exists: %s" % packed_location)

        with ZipFile(packed_location, "w") as f:
            for root, dirs, files in os.walk(self.location):
                zip_root = Path(root).relative_to(
                    self.manager.config.mods_path).as_posix()

                for file_name in files:
                    f.write(
                        '%s/%s' % (root, file_name),
                        '%s/%s' % (zip_root, file_name),
                    )

        self.remove()

        return ZippedMod(self.manager, packed_location)

    @classmethod
    def find(cls, *args, **kwargs):
        return cls._find("%s_%s/", *args, **kwargs)


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
        """Return the mod json configuration from mods-list.json"""

        for mod in self.mods_json.mods:
            if mod.name == name:
                return mod

    def get_mod(self, name):
        for mod in self.get_mods(name):
            if mod.name == name:
                return mod

    def get_mods(self, name=None, version=None):
        for mod_type in (ZippedMod, UnpackedMod):
            yield from mod_type.find(self, name, version)

    def resolve_mod_name(self, name, remote=False):
        if '*' in name:
            # Keep patterns unmodified
            return name

        # Find an exact local match
        local_mods = list(self.get_mods())

        for mod in local_mods:
            if mod.name == name:
                return name

        if remote:
            # Find an exact remote match
            try:
                mod = self.api.get(name)
                return mod.name
            except ModNotFoundError:
                pass

        # Find a local match (case-insensitive)
        for mod in local_mods:
            if mod.name.lower() == name.lower():
                return mod.name

        if remote:
            # Find a remote match (case-insensitive)
            remote_mods = list(self.api.search(name, page_size=5, limit=5))
            for mod in remote_mods:
                if mod.name.lower() == name.lower():
                    return mod.name

            # If there was only one result, we can assume it's the one
            if len(remote_mods) == 1:
                return remote_mods[0].name

        # If nothing was found, return original mod name and let things fail
        return name

    def resolve_remote_requirement(self, req):
        spec = req.specifier
        game_ver = self.config.game_version_major

        mod = self.api.get(req.name)

        return [release for release in mod.releases
                if release.version in spec and
                release.game_version == game_ver]

    def resolve_local_requirement(self, req):
        spec = req.specifier
        game_ver = self.config.game_version_major

        return [info for info in self.get_mods(req.name)
                if info.version in spec and
                info.factorio_version == game_ver]

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

    def install_mod(self, release, enable=None, unpack=None):
        file_name = release.file_name
        mod_name = release.info_json.name

        assert '/' not in file_name
        assert '\\' not in file_name
        assert file_name.endswith('.zip')

        try:
            installed_mod = next(self.get_mods(mod_name))
            if unpack is None:
                unpack = not installed_mod.packed
        except StopIteration:
            installed_mod = None

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

        mod = ZippedMod(self, file_path)

        if installed_mod and (installed_mod.basename != mod.basename or
                              not installed_mod.packed):
            installed_mod.remove()

        if enable is not None:
            mod.enabled = enable

        if unpack:
            mod.unpack()

    def uninstall_mods(self, name, version=None):
        mods_to_remove = self.get_mods(name=name, version=version)

        for mod in mods_to_remove:
            mod.remove()
