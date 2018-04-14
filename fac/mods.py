import os.path
import shutil
import json

from urllib.parse import urljoin
from fnmatch import fnmatchcase
from zipfile import ZipFile
from pathlib import Path
from glob import glob

from fac.files import JSONFile
from fac.utils import (JSONDict, ProgressWidget,
                       Version, parse_game_version, match_game_version)

from fac.errors import ModNotFoundError, AuthError, OwnershipError


class Mod:
    location = None

    def __init__(self, manager, location):
        self.manager = manager
        self.location = os.path.abspath(location)

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
        return parse_game_version(self.info)

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
                print("Warning: invalid mod %s: %s" % (path, ex))
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
        self.parent = os.path.abspath(
            os.path.dirname(self.location)
        )
        self._read_info()

    def remove(self):
        print("Removing file: %s" % self.location)
        os.remove(self.location)

    def _read_info(self):
        with ZipFile(self.location) as f:
            first_entry = f.namelist()[0]
            self.toplevel = first_entry.split('/')[0]

            if not self.toplevel:
                raise Exception("Could not find a top-level directory")

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

        print("Unpacking: %s" % self.location)

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
            except Exception:
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
                open(dest, 'wb') as target:
            shutil.copyfileobj(source, target)

    @classmethod
    def find(cls, *args, **kwargs):
        return cls._find('*.zip', *args, **kwargs)


class UnpackedMod(Mod):
    packed = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if os.path.isfile(self.location):
            self.location = os.path.dirname(self.location)

        self.basename = os.path.basename(
            self.location
        )
        self.parent = os.path.abspath(
            os.path.join(self.location, '..')
        )

        self._read_info()

    def remove(self):
        print("Removing directory: %s" % self.location)
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

        print("Packing: %s" % self.location)

        with ZipFile(packed_location, 'w') as f:
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
            except Exception:
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
    """Provides access to the factorio mods directory"""

    def __init__(self, config, api, db):
        self.api = api
        self.config = config
        self.db = db
        self.mods_json = None

    def load(self):
        self.mods_json = JSONFile(
            os.path.join(
                self.config.mods_directory,
                'mod-list.json'
            )
        )
        if 'mods' not in self.mods_json:
            self.mods_json.mods = []

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

    def resolve_mod_name(self, name, remote=False, patterns=True):
        if patterns and '*' in name:
            # Keep patterns unmodified
            return name

        # Find an exact match
        mod_names = set(mod.name for mod in self.find_mods())

        if remote:
            mod_names |= set(self.db.mods)

        if name in mod_names:
            return name

        # Find a case-insensitive match
        for mod_name in mod_names:
            if mod_name.lower() == name.lower():
                return mod_name

        # Find a unique partial match (case-insensitive)
        partial_matches = [mod_name
                           for mod_name in mod_names
                           if name.lower() in mod_name.lower()]

        if len(partial_matches) == 1:
            return partial_matches[0]

        if remote:
            # Find a remote match (case-insensitive)
            remote_mods = list(self.db.search(name, limit=5))

            # If there was only one result, we can assume it's the one
            if len(remote_mods) == 1:
                return remote_mods[0].name
            elif len(remote_mods) > 1:
                print("'%s' not found, try one of the following:" % name)
                for match in remote_mods:
                    print(" - " + match.name)
                print()

        raise ModNotFoundError(name)

        # If nothing was found, return original mod name and let things fail
        return name

    def resolve_remote_requirement(self, req, ignore_game_ver=False):
        spec = req.specifier
        game_ver = None if ignore_game_ver else self.config.game_version_major

        releases = self.get_releases(req.name, game_ver)

        yield from (
            release
            for release in releases
            if release.version in spec
        )

    def resolve_local_requirement(self, req, ignore_game_ver=False):
        spec = req.specifier
        game_ver = self.config.game_version_major

        res = [mod for mod in self.find_mods(req.name)
               if mod.version in spec and
               (ignore_game_ver or mod.game_version == game_ver)]
        res.sort(key=lambda m: m.version, reverse=True)
        return res

    def get_releases(self, mod_name, game_version):
        try:
            mod = getattr(self.db.mods, mod_name)
        except AttributeError:
            raise ModNotFoundError(mod_name)

        if match_game_version(mod.latest_release, game_version):
            latest = mod.latest_release
            yield latest

        mod = self.api.get_mod(mod_name)
        res = [release
               for release in mod.releases
               if match_game_version(release, game_version)
               and release.version != latest.version]

        res.sort(key=lambda r: Version(r.version), reverse=True)
        yield from res

    def is_mod_enabled(self, name):
        mod = self.get_mod_json(name)
        if mod:
            # Factorio < 0.15 uses "true"/"false" strings instead of booleans
            return mod.enabled != 'false' and mod.enabled is not False
        else:
            return True  # by default, new mods are automatically enabled

    def set_mod_enabled(self, name, enabled=True):
        mod = self.get_mod_json(name)

        if not mod:
            mod = {'enabled': '', 'name': name}
            self.mods_json.mods.append(mod)
            mod = self.get_mod_json(name)

        if enabled != self.is_mod_enabled(name):
            if self.config.game_version < Version('0.15'):
                # Factorio < 0.15 uses "true"/"false" strings
                # instead of booleans
                mod.enabled = 'true' if enabled else 'false'
            else:
                mod.enabled = enabled
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
            print("You need a Factorio account to download mods.")
            print("Please provide your username and password to authenticate "
                  "yourself.")
            print("Your username and token (NOT your password) will be stored "
                  "so that you only have to enter it once")
            print("This uses the exact same method used by Factorio itself")
            print()
            while True:
                if username:
                    print("Username [%s]:" % username, end=" ", flush=True)
                else:
                    print("Username:", end=" ", flush=True)

                input_username = sys.stdin.readline().strip()

                if input_username:
                    username = input_username
                elif not username:
                    continue

                password = getpass.getpass("Password (not shown):")
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
                    print("Authentication error: %s." % ex)
                except Exception as ex:
                    print("Error: %s." % ex)
                else:
                    print("Logged in successfully.")
                    break
                print()
            player_data['service-token'] = token
            player_data['service-username'] = username
            player_data.save()
        return player_data

    def install_mod(self, mod_name, release, enable=None, unpack=None):
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
        shutil.move(tmp_file, file_path)

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
        basename = release.file_name

        with ProgressWidget("Downloading: %s..." % basename) as progress:
            while True:
                req = self.api.get(
                    url,
                    params={
                        'username': player_data['service-username'],
                        'token': player_data['service-token']
                    },
                    stream=True,
                )

                if req.status_code == 403:
                    progress.error()
                    print("Authentication error when downloading mod. "
                          "Please login again.")
                    player_data = self.require_login(reset=True)
                    continue
                break

            req.raise_for_status()
            length = int(req.headers['content-length'])

            with open(file_path, 'wb') as f:
                for chunk in req.iter_content(chunk_size=1024):
                    f.write(chunk)
                    progress(f.tell(), length)

        return ZippedMod(self, file_path)
