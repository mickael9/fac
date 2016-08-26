from fac.commands import Command


class ListCommand(Command):
    'List installed mods and their status.'

    name = 'list'

    def run(self, args):
        mods = self.manager.find_mods()
        if not mods:
            print('No installed mods.')
            return

        print('Installed mods:')

        for mod in sorted(mods, key=lambda m: (not m.enabled, m.name)):
            tags = []
            if not mod.enabled:
                tags.append('disabled')
            if not mod.packed:
                tags.append('unpacked')
            if mod.held:
                tags.append('held')
            if mod.game_version != self.config.game_version_major:
                tags.append('incompatible')
            if tags:
                tags = ' (%s)' % (', '.join(tags))
            else:
                tags = ''

            print('    %s %s%s' % (
                mod.name, mod.version, tags
            ))
