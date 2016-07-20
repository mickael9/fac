from fac.commands import Command


class ListCommand(Command):
    'List installed mods and their status'

    name = 'list'

    def run(self, args):
        enabled, disabled = categories = [[], []]
        mods = self.manager.get_installed_mods()
        for mod in mods:
            n = int(not self.manager.is_mod_enabled(mod.name))
            categories[n].append(mod.name)

        for i, name in enumerate(('Enabled', 'Disabled')):
            mods = categories[i]
            if mods:
                print('%s mods:' % name)
                for mod in mods:
                    print('    %s' % mod)
                print()
