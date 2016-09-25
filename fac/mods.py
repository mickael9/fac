import os.path
import shutil
import json

from urllib.parse import urljoin
from fnmatch import fnmatchcase
from zipfile import ZipFile
from pathlib import Path
from glob import glob

import requests

from fac.files import JSONFile
from fac.utils import JSONDict, Version
from fac.api import AuthError, OwnershipError, ModNotFoundError


class Mod:
    location = None

    def __init__(self, manager, location):
        self.manager = manager
        self.location = os.path.realpath(location)

    def get_enabled(self):
        return self.manager.is_mod_enabled(self.name)

    def set_enabled(self, val):
        self.manager.set_mod_enabled(self.name, val)

    enabled = property(get_enabled, set_enabled)

    def get_held(self):
        return self.manager.is_mod_held(self.name)

    def set_held(self, held):
        self.manager.set_mod_held(self.name, held)

    held = property(get_held, set_held)

    @property
    def name(self):
        return self.info.name

    @property
    def version(self):
        return Version(self.info.version)

    @property
    def game_version(self):
        try:
            return Version(self.info.factorio_version)
        except AttributeError:
            return Version('0.12')

    @classmethod
    def _find(cls, pattern, manager, name, version):
        name = '*' if name is None else name

        installed = glob(
            os.path.join(
                manager.config.mods_directory,
                pattern
            )
        )
        for path in installed:
            try:
                mod = cls(manager, path)

            except Exception as ex:
                print('Warning: invalid mod %s: %s' % (path, ex))
                continue

            if not fnmatchcase(mod.name, name):
                continue

            if version is not None and version != mod.version:
                continue

            yield mod


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
        self.parent = os.path.realpath(
            os.path.dirname(self.location)
        )
        self._read_info()

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

    def pack(self, *args, **kwargs):
        return self

    def unpack(self, replace=False, keep=False):
        unpacked_location = os.path.join(self.parent, self.basename)

        assert (os.path.sep not in self.basename and not (
                os.path.altsep and os.path.altsep in self.basename)), \
            "Unsafe mod directory name: %s" % self.basename

        if os.path.isdir(unpacked_location) and not replace:
            return UnpackedMod(self.manager, unpacked_location)

        print('Unpacking: %s' % self.location)

        with ZipFile(self.location) as f:
            if replace and os.path.isdir(unpacked_location):
                shutil.rmtree(unpacked_location)

            os.makedirs(unpacked_location)

            try:
                for arcname in f.namelist():
                    if not arcname.startswith(self.toplevel + '/'):
                        print("Warning: out-of-place file %s ignored" % (
                            arcname))
                        continue

                    dest = arcname[len(self.toplevel) + 1:]
                    dest = self._sanitize_arcname(dest)
                    dest = os.path.join(unpacked_location, dest)
                    self._extract_member(f, arcname, dest)
                unpacked_mod = UnpackedMod(self.manager, unpacked_location)
            except:
                shutil.rmtree(unpacked_location)
                raise

        if not keep:
            self.remove()

        return unpacked_mod

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
        return cls._find("*.zip", *args, **kwargs)


class UnpackedMod(Mod):
    packed = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if os.path.isfile(self.location):
            self.location = os.path.dirname(self.location)

        self.basename = os.path.basename(
            self.location
        )
        self.parent = os.path.realpath(
            os.path.join(self.location, '..')
        )

        self._read_info()

    def remove(self):
        print('Removing directory: %s' % self.location)
        shutil.rmtree(self.location)

    def _read_info(self):
        path = os.path.join(self.location, 'info.json')
        self.info = JSONFile(path)

    def unpack(self, *args, **kwargs):
        return self

    def pack(self, replace=False, keep=False):
        packed_location = os.path.join(
            self.parent,
            self.basename + '.zip'
        )

        if not replace and os.path.exists(packed_location):
            return ZippedMod(self.manager, packed_location)

        print('Packing: %s' % self.location)

        with ZipFile(packed_location, "w") as f:
            try:
                for root, dirs, files in os.walk(self.location):
                    zip_root = Path(root).relative_to(
                        self.parent).as_posix()

                    for file_name in files:
                        f.write(
                            '%s/%s' % (root, file_name),
                            '%s/%s' % (zip_root, file_name),
                        )
                f.close()
                packed_mod = ZippedMod(self.manager, packed_location)
            except:
                f.close()
                os.remove(packed_location)
                raise

        if not keep:
            self.remove()

        return packed_mod

    @classmethod
    def find(cls, *args, **kwargs):
        return cls._find("*/info.json", *args, **kwargs)


class ModManager:
    'Provides access to the factorio mods directory'

    def __init__(self, config, api):
        self.api = api
        self.config = config
        self.mods_json = JSONFile(
            os.path.join(
                self.config.mods_directory,
                'mod-list.json'
            )
        )

    def get_mod_json(self, name):
        """Return the mod json configuration from mods-list.json"""

        for mod in self.mods_json.mods:
            if mod.name == name:
                return mod

    def get_mod(self, name, *args, **kwargs):
        for mod in self.find_mods(name, *args, **kwargs):
            if mod.name == name:
                return mod

    def find_mods(self, name=None, version=None, packed=None):
        mods = []
        for mod_type in (ZippedMod, UnpackedMod):
            if packed is not None and mod_type.packed != bool(packed):
                continue
            mods.extend(mod_type.find(self, name, version))
        return mods

    def resolve_mod_name(self, name, remote=False):
        if '*' in name:
            # Keep patterns unmodified
            return name

        # Find an exact local match
        local_mods = self.find_mods()

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

        # Find a local partial match (case-insensitive)
        partial_matches = [mod for mod in local_mods
                           if name.lower() in mod.name.lower()]
        if len(partial_matches) == 1:
            return partial_matches[0].name

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

    def resolve_remote_requirement(self, req, ignore_game_ver=False):
        spec = req.specifier
        game_ver = self.config.game_version_major

        mod = self.api.get(req.name)

        res = [release for release in mod.releases
               if release.version in spec and
               (ignore_game_ver or
                release.factorio_version == game_ver)]
        res.sort(key=lambda r: Version(r.version), reverse=True)
        return res

    def resolve_local_requirement(self, req, ignore_game_ver=False):
        spec = req.specifier
        game_ver = self.config.game_version_major

        res = [mod for mod in self.find_mods(req.name)
               if mod.version in spec and
               (ignore_game_ver or mod.game_version == game_ver)]
        res.sort(key=lambda m: m.version, reverse=True)
        return res

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
            mod = self.get_mod_json(name)

        if enabled != (mod.enabled == 'true'):
            mod.enabled = 'true' if enabled else 'false'
            self.mods_json.save()
            return True
        else:
            return False

    def is_mod_held(self, name):
        return name in self.config.hold

    def set_mod_held(self, name, held=True):
        if self.is_mod_held(name) == held:
            return False

        if held:
            self.config.hold.append(name)
        else:
            self.config.hold.remove(name)

        self.config.save()
        return True

    def require_login(self, reset=False):
        import getpass
        import sys
        player_data = self.config.player_data
        username = player_data.get('service-username')
        token = player_data.get('service-token')

        if reset or not (username and token):
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
                    token = self.api.login(username, password,
                                           require_ownership=True)
                except OwnershipError as ex:
                    print("Ownership error: Your factorio account doesn't "
                          "own the game.")
                    print("Please buy the game or link your Steam account if "
                          "you have bought the game from Steam.")
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
        mod_name = release.info_json.name
        file_name = release.file_name
        self.validate_mod_file_name(file_name)
        file_path = os.path.join(self.config.mods_directory, file_name)

        installed_mod = self.get_mod(mod_name)
        if installed_mod and unpack is None:
            unpack = not installed_mod.packed

        tmp_file = os.path.join(
            self.config.factorio_write_path,
            'tmp',
            file_name
        )

        os.makedirs(os.path.dirname(tmp_file), exist_ok=True)
        self.download_mod(release, tmp_file)
        os.rename(tmp_file, file_path)

        mod = ZippedMod(self, file_path)

        if installed_mod and (installed_mod.basename != mod.basename or
                              not installed_mod.packed):
            installed_mod.remove()

        if enable is not None:
            mod.enabled = enable

        if unpack:
            mod.unpack()

    def validate_mod_file_name(self, file_name):
        assert '/' not in file_name
        assert '\\' not in file_name
        assert file_name.endswith('.zip')

    def download_mod(self, release, file_path):
        player_data = self.require_login()
        url = urljoin(self.api.base_url, release.download_url)

        while True:
            print('Downloading: %s...' % url)

            req = requests.get(
                url,
                params={
                    'username': player_data['service-username'],
                    'token': player_data['service-token']
                }
            )

            if req.status_code == 403:
                print('Authentication error when downloading mod. '
                      'Please login again.')
                player_data = self.require_login(reset=True)
                continue
            break

        req.raise_for_status()
        data = req.content

        if len(data) != release.file_size:
            raise Exception(
                'Downloaded file has incorrect size (%d), expected %d.' % (
                    len(data), release.file_size
                )
            )

        with open(file_path, 'wb') as f:
            f.write(data)

        return ZippedMod(self, file_path)
