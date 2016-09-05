from fac.commands import Command, Arg
from fac.api import ModNotFoundError
from fac.utils import prompt, Version


class UpdateCommand(Command):
    'Update installed mods.'

    name = 'update'
    arguments = [
        Arg('-s', '--show', action='store_true',
            help='only show what would be updated'),

        Arg('-y', '--yes', action='store_true',
            help='automatic yes to confirmation prompt'),

        Arg('-U', '--unpacked', action='store_true',
            help='allow updating unpacked mods'),

        Arg('-H', '--held', action='store_true',
            help='allow updating held mods'),
    ]

    def run(self, args):
        installed = self.manager.find_mods()
        updates = []
        game_ver = self.config.game_version_major

        for local_mod in installed:
            print('Checking: %s' % local_mod.name)
            try:
                remote_mod = self.api.get(local_mod.name)
            except ModNotFoundError as ex:
                print('Warning: %s' % ex)
                continue

            for release in remote_mod.releases:
                if not args.ignore_game_ver and \
                        release.factorio_version != game_ver:
                    continue

                release_ver = Version(release.version)
                local_ver = local_mod.version

                if release_ver > local_ver:
                    print('Found update: %s %s' % (
                        local_mod.name, release.version)
                    )

                    if not args.unpacked and not local_mod.packed:
                        print(
                            '%s is unpacked. '
                            'Use -U to update it anyway.' % (
                                local_mod.name
                            )
                        )
                        continue

                    if not args.held and local_mod.name in self.config.hold:
                        print('%s is held. '
                              'Use -H to update it anyway.' %
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
