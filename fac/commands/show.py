from fac.commands import Command, Arg
from fac.api import ModNotFoundError


class ShowCommand(Command):
    'Show details about specific mods'

    name = 'show'
    arguments = [
        Arg('mod', help='Mod name', nargs='+'),
    ]

    def run(self, opts):
        first = True
        for mod in opts.mod:
            if first:
                first = False
            else:
                print('-' * 80)
            try:
                m = self.api.get(mod)
            except ModNotFoundError:
                print('Error: Mod %s does not exist' % mod)
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
                        release.version, release.game_version))
