import os.path

from fac.mods import ZippedMod
from fac.commands import Command, Arg
from fac.api import ModNotFoundError
from fac.utils import parse_requirement, Requirement


class FetchCommand(Command):
    '''
    Fetch a mod from the mod portal.

    This will fetch the mods matching the given requirements using this format:
        name
        name==version
        name>=version
        name<version
        ...

    If the version is not specified, the latest version will be selected.
    '''
    name = 'fetch'

    arguments = [
        Arg('requirements', nargs='+',
            help='requirement to fetch '
                 '("name", "name>=1.0", "name==1.2", ...)'),

        Arg('-U', '--unpack', action='store_true', default=None,
            help='unpack mods zip files after downloading'),

        Arg('-K', '--keep', action='store_true',
            help='keep mod zip file after unpacking'),

        Arg('--dest', '-d', default='.',
            help='destination directory (default: current directory)'),

        Arg('-R', '--replace', action='store_true',
            help='replace existing file/directory'),
    ]

    def run(self, args):
        for req in args.requirements:
            name, spec = parse_requirement(req)
            name = self.manager.resolve_mod_name(name, remote=True)
            req = Requirement(name, spec)

            try:
                releases = self.manager.resolve_remote_requirement(
                    req, ignore_game_ver=True
                )
            except ModNotFoundError as ex:
                print("Error: %s" % ex)
                continue

            if not releases:
                print('No match found for %s' % (req,))
                continue

            release = releases[0]

            file_name = release.file_name
            self.manager.validate_mod_file_name(file_name)
            file_path = os.path.join(args.dest, file_name)

            if os.path.exists(file_path) and not args.replace:
                print(
                    'File %s already exists. '
                    'Use -R to replace it.' % file_path
                )
                continue

            if not os.path.isdir(args.dest):
                os.makedirs(args.dest)

            print('Saving to: %s' % file_path)
            mod = self.manager.download_mod(release, file_path)

            if args.unpack:
                mod.unpack(replace=args.replace, keep=args.keep)
