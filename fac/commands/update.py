from pkg_resources import parse_version

from fac.commands import Command, Arg
from fac.api import ModNotFoundError
from fac.utils import prompt


class UpdateCommand(Command):
    'Update installed mods'

    name = 'update'
    arguments = [
        Arg('-s', '--show', action='store_true',
            help='only show what would be updated'),

        Arg('-y', '--yes', action='store_true',
            help='automatic yes to confirmation prompt'),

        Arg('--force', action='store_true',
            help='force update of held mods'),
    ]

    def run(self, args):
        installed = self.manager.get_installed_mods()
        updates = []
        game_ver = self.config.game_version_major

        for local_mod in installed:
            print('Checking: %s' % local_mod.name)
            try:
                remote_mod = self.api.get(local_mod.name)
            except ModNotFoundError:
                print('Warning: %s not found in the mod database.' % (
                    local_mod.name
                ))
                continue

            for release in remote_mod.releases:
                if release.game_version != game_ver:
                    continue

                release_ver = parse_version(release.version)
                local_ver = parse_version(local_mod.version)

                if release_ver > local_ver:
                    if not args.force and local_mod.name in self.config.hold:
                        print('%s is held. '
                              'Use --force to update it anyway.' %
                              local_mod.name)
                        break
                    updates.append((local_mod, release))
                    break

        if not updates:
            print('No updates were found')
            return

        print('Found %d update%s:' % (
            len(updates),
            's' if len(updates) != 1 else '',
        ))

        for local_mod, release in updates:
            print('    %s %s -> %s' % (
                local_mod.name, local_mod.version, release.version
            ))

        if not args.show:
            if not args.yes and prompt('Continue?', 'Y/n') != 'y':
                return

            for local_mod, release in updates:
                self.manager.install_mod(release)
