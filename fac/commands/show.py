from fac.commands import Command, Arg
from fac.api import ModNotFoundError


class ShowCommand(Command):
    'Show details about specific mods.'

    name = 'show'
    arguments = [
        Arg('mods', help='mods to show', nargs='+'),

        Arg('-F', '--format',
            help='show mods using the specified format string.'),
    ]

    epilog = """
    An optional format string can be specified with the -F flag.
    You can use this if you want to customize the default output format.

    The syntax of format strings is decribed here:
    https://docs.python.org/3/library/string.html#format-string-syntax

    There is only one argument passed to the format string which is the
    mod object returned by the API.

    Using the default string ('s') specifier on a JSON list or object will
    output valid JSON.

    Some examples:
        {mod}                        JSON as returned by the API
        {mod.name}                   Name of the mod
        {mod.releases[0].version}    Version of first release
        {mod.releases[0].info_json}  info.json of first release
    """

    def run(self, args):
        first = True
        for mod in args.mods:
            if first:
                first = False
            else:
                print('-' * 80)

            mod = self.manager.resolve_mod_name(mod, remote=True)
            try:
                m = self.api.get(mod)
            except ModNotFoundError as ex:
                print('Error: %s' % ex)
                continue

            if args.format:
                print(args.format.format(m, mod=m))
                continue

            print('Name: %s' % m.name)
            print('Author: %s' % m.owner)
            print('Title: %s' % m.title)
            print('Summary: %s' % m.summary)
            print('Description:')

            for line in m.description.splitlines():
                print('    %s' % line)

            if m.tags:
                print('Tags: %s' % ', '.join(tag.name for tag in m.tags))

            if m.homepage:
                print('Homepage: %s' % m.homepage)

            if m.github_path:
                print('GitHub page: https://github.com/%s' % m.github_path)

            print('License: %s' % m.license_name)
            print('Game versions: %s' % ", ".join(m.game_versions))

            print('Releases:')
            if not m.releases:
                print('    No releases')
            else:
                for release in m.releases:
                    print('    Version: %-9s Game version: %-9s' % (
                        release.version, release.factorio_version))
